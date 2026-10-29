"""v7: stylised *out-of-policy-model* sponsored-search portfolio simulator.

Tests an UNCHANGED v5 one-step VOI allocation rank against three alternative
ranking rules, given shared exploration quota and a common three-action
(SCALE/MAINTAIN/NEGATIVE) follow-up rule. No seller data. This deliberately
adds uncertainty and mechanics absent from the VOI decision equation: CPC
auction shocks, bid-dependent traffic/quality, finite portfolio budgets,
delayed observed conversions, heterogeneous margins and a MAINTAIN option.

This is not a calibrated Amazon Ads simulator, a causal estimate, or external
validation. Do not automate actual bids based on these tests.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_distribution
from fair_baselines import voi_increment, allocate

OUT = Path(__file__).resolve().parent / 'results'
N_TERMS = 180
TERMS_PER_CAMPAIGN = 30
N_CAMPAIGNS = N_TERMS // TERMS_PER_CAMPAIGN
PROBE_CLICKS = 10
FUTURE_MAX_CLICKS = 220
PRIOR = (2., 18.)  # fixed from v5 TRAIN ONLY; no tuning on v7 test outcomes
ASSUMED_MARGIN = .25
OVERHEAD = 2.0  # fictional units per selected term, outside ad-spend budget
QUOTAS = (.05, .10, .20)
SEEDS = tuple(range(23000, 23040))  # completely fresh v7 tests
POLICIES = ('Random', 'Fewest clicks', 'Profitability uncertainty', 'v5 VOI rank')
SCENARIOS = {
    'Mixture reference': dict(cvr_mult=1.0, auction_mult=1.0, visible_fraction=1.0, budget_mult=1.0, scale_quality=.90),
    'Auction costs +35%': dict(cvr_mult=1.0, auction_mult=1.35, visible_fraction=1.0, budget_mult=1.0, scale_quality=.85),
    'Conversions 50% visible': dict(cvr_mult=1.0, auction_mult=1.0, visible_fraction=.50, budget_mult=1.0, scale_quality=.90),
    'Campaign budgets halved': dict(cvr_mult=1.0, auction_mult=1.0, visible_fraction=1.0, budget_mult=.50, scale_quality=.90),
    'Future CVR -40%': dict(cvr_mult=.60, auction_mult=1.0, visible_fraction=1.0, budget_mult=1.0, scale_quality=.90),
    'Combined adverse': dict(cvr_mult=.60, auction_mult=1.35, visible_fraction=.50, budget_mult=.60, scale_quality=.85),
}


def make_cohort(seed: int, scenario: dict, n: int = N_TERMS):
    """Draw synthetic latent commercial processes not used by v5 VOI formula.

    Random streams use seed only to make scenario comparisons paired where
    possible. Future conversion potential outcomes use per-term uniform draws.
    """
    if n <= 0 or n % TERMS_PER_CAMPAIGN:
        raise ValueError('n must be a positive multiple of 30')
    rng = np.random.default_rng(seed)
    segment = rng.integers(0, 4, n)
    a = np.array([1.5, 2.5, 2., 3.])[segment]
    b = np.array([34., 23., 45., 18.])[segment]
    historical_p = np.clip(rng.beta(a, b), .002, .42)
    hist_clicks = rng.integers(5, 161, n)
    hist_orders_actual = rng.binomial(hist_clicks, historical_p)
    visible_fraction = scenario['visible_fraction']
    # Historical attribution can be incomplete and masks some realised orders.
    hist_orders = rng.binomial(hist_orders_actual, visible_fraction) if visible_fraction < 1 else hist_orders_actual.copy()
    cpc = rng.uniform(.35, 1.55, n)
    aov = rng.uniform(18., 78., n)
    margin = rng.uniform(.14, .39, n)
    auction_shock = rng.lognormal(mean=-.5 * .2**2, sigma=.2, size=n)
    demand = rng.poisson(rng.uniform(10., 65., n)).astype(int)
    demand = np.maximum(demand, 1)
    future_p = np.clip(historical_p * scenario['cvr_mult'], .001, .80)
    probe_u = rng.random((n, PROBE_CLICKS))
    report_u = rng.random((n, PROBE_CLICKS))
    future_u = rng.random((n, FUTURE_MAX_CLICKS))
    return dict(clicks=hist_clicks, orders=hist_orders, cpc=cpc,
                aov=aov, margin=margin, historical_p=historical_p,
                future_p=future_p, auction_shock=auction_shock,
                demand=demand, probe_u=probe_u, report_u=report_u,
                future_u=future_u, campaign=np.arange(n)//TERMS_PER_CAMPAIGN,
                visible_fraction=visible_fraction, **{'scenario': scenario})


def rank_terms(cohort: dict, seed: int):
    """No latent future, margins, auction shocks, demand, or report outcomes used."""
    clicks, orders, cpc, aov = (cohort[k] for k in ('clicks','orders','cpc','aov'))
    aa, bb = PRIOR[0] + orders, PRIOR[1] + clicks - orders
    threshold = np.clip(cpc / (ASSUMED_MARGIN*aov), 0, 1)
    chance = beta_distribution.sf(threshold, aa, bb)
    uncertainty = .5 - np.abs(chance-.5)
    return {'Random': np.random.default_rng(400000+seed).random(len(clicks)),
            'Fewest clicks': -clicks.astype(float),
            'Profitability uncertainty': uncertainty,
            'v5 VOI rank': voi_increment(clicks, orders, cpc, aov, PRIOR, overhead=OVERHEAD)}


def three_action_policy(clicks, orders, cpc, aov):
    """Fixed heuristic shared by every ranker; no parameter fitted on v7 results.

    MAINTAIN occupies a narrow band of uncertain projected unit profitability.
    """
    alpha, beta = PRIOR[0] + np.asarray(orders), PRIOR[1]+np.asarray(clicks)-np.asarray(orders)
    profit_est = alpha/(alpha+beta)*ASSUMED_MARGIN*np.asarray(aov)-np.asarray(cpc)
    cpc = np.asarray(cpc)
    return np.where(profit_est > .18*cpc, 'SCALE',
                    np.where(profit_est >= -.25*cpc, 'MAINTAIN', 'NEGATIVE'))


def run_policy(cohort: dict, selected, *, check_budget=True):
    """Two-stage portfolio, with exploration first and budget-limited auction traffic.

    The *only* manipulated factor across ranking policies is which terms get
    exploration; policy and simulation share no hidden future parameters.
    Future customer outcomes come from the same per-term uniforms across
    policies. Actual conversions are counted at final maturity, even when the
    *reported* attribution available at decision time is delayed.
    """
    n = len(cohort['clicks'])
    selected = np.asarray(selected, dtype=bool)
    if selected.shape != (n,):
        raise ValueError('Selection must match cohort length')
    scenario = cohort['scenario']
    campaign = cohort['campaign']
    nc = int(campaign.max())+1
    cap = np.full(nc, 440.0 * scenario['budget_mult'])
    spend_per_campaign = np.zeros(nc)
    clicks = cohort['clicks'].astype(int).copy()
    observed_orders = cohort['orders'].astype(int).copy()
    profit = -OVERHEAD*int(selected.sum())
    probe_spend=0.
    earned_revenue=0.
    # This is a potential-outcome exposure model, not a real auction/traffic engine.
    cpc_actual = cohort['cpc']*cohort['auction_shock']*scenario['auction_mult']
    probe_complete=0
    seen_probe_orders=0
    true_probe_orders=0
    for i in np.flatnonzero(selected):
        camp=int(campaign[i]); cost=float(cpc_actual[i]); remaining=cap[camp]-spend_per_campaign[camp]
        num=min(PROBE_CLICKS, max(0,int(np.floor((remaining+1e-9)/cost))))
        spend=float(num*cost)
        observed_true=(cohort['probe_u'][i,:num] < cohort['future_p'][i])
        conversions=int(observed_true.sum())
        visible=int((observed_true & (cohort['report_u'][i,:num] < cohort['visible_fraction'])).sum())
        clicks[i]+=num
        observed_orders[i]+=visible
        spend_per_campaign[camp]+=spend
        probe_spend+=spend
        revenue=conversions*cohort['aov'][i]*cohort['margin'][i]
        earned_revenue+=float(revenue)
        profit+=float(revenue)-spend
        true_probe_orders+=conversions;seen_probe_orders+=visible
        probe_complete += int(num==PROBE_CLICKS)
    action = three_action_policy(clicks, observed_orders,cohort['cpc'],cohort['aov'])
    # Equal priority rule for all policies; allocation can interact through budgets.
    alpha=PRIOR[0]+observed_orders
    beta=PRIOR[1]+clicks-observed_orders
    expected_profit=alpha/(alpha+beta)*ASSUMED_MARGIN*cohort['aov']-cohort['cpc']
    priority=expected_profit / np.maximum(cohort['cpc'],.01)
    auction_spend=0.
    auction_clicks=0
    auction_conversions=0
    for camp in range(nc):
        indices=np.flatnonzero((campaign==camp) & (action!='NEGATIVE'))
        indices=indices[np.argsort(-priority[indices],kind='stable')]
        for i in indices:
            is_scale=action[i]=='SCALE'
            cost=float(cpc_actual[i]*(1.16 if is_scale else 1.0))
            volume_factor=1.40 if is_scale else 1.0
            demanded=min(FUTURE_MAX_CLICKS, int(np.floor(cohort['demand'][i]*volume_factor)))
            budget_remaining=float(cap[camp]-spend_per_campaign[camp])
            awarded=min(demanded, max(0,int(np.floor((budget_remaining+1e-9)/cost))))
            if awarded==0:
                continue
            conversion_p=float(cohort['future_p'][i] * (scenario['scale_quality'] if is_scale else 1.0))
            conversions=int((cohort['future_u'][i,:awarded] < conversion_p).sum())
            spent=float(awarded*cost)
            revenue=float(conversions*cohort['aov'][i]*cohort['margin'][i])
            profit+=revenue-spent
            earned_revenue+=revenue
            auction_spend+=spent
            auction_clicks+=awarded
            auction_conversions+=conversions
            spend_per_campaign[camp]+=spent
    if check_budget and np.any(spend_per_campaign > cap+1e-6):
        raise AssertionError('Campaign budget exceeded')
    return {'profit':float(profit/n),'total_profit':float(profit),
            'spend_per_term':float(spend_per_campaign.sum()/n),
            'revenue_per_term':float(earned_revenue/n),
            'budget_utilisation':float((spend_per_campaign/cap).mean()),
            'probe_spend':float(probe_spend),
            'probe_complete_rate':float(probe_complete/max(1,selected.sum())),
            'probe_orders_visible_fraction':float(seen_probe_orders/max(1,true_probe_orders)),
            'defer_rate':float(selected.mean()),
            'maintain_rate':float((action=='MAINTAIN').mean()),
            'scale_rate':float((action=='SCALE').mean()),
            'negative_rate':float((action=='NEGATIVE').mean()),
            'spend_by_campaign':spend_per_campaign,
            'campaign_caps':cap,
            'auction_clicks':auction_clicks,
            'auction_conversions':auction_conversions}


def evaluate(seeds=SEEDS, scenario_names=None, quotas=QUOTAS, n=N_TERMS):
    names=tuple(scenario_names or SCENARIOS)
    rows=[]
    for name in names:
        scenario=SCENARIOS[name]
        for seed in seeds:
            cohort=make_cohort(seed,scenario,n)
            scores=rank_terms(cohort,seed)
            for quota in quotas:
                for method in POLICIES:
                    selected=allocate(scores[method],quota)
                    metric=run_policy(cohort,selected)
                    metric.pop('spend_by_campaign'); metric.pop('campaign_caps')
                    rows.append(dict(scenario=name,seed=seed,quota=quota,method=method,**metric))
    return pd.DataFrame(rows)


def summarize(frame):
    grouped=frame.groupby(['scenario','quota','method'],sort=False)
    main=grouped.agg(profit=('profit','mean'),sd=('profit','std'),
             spend=('spend_per_term','mean'),budget_utilisation=('budget_utilisation','mean'),
             maintain_rate=('maintain_rate','mean'),defer_rate=('defer_rate','mean'),
             probe_complete_rate=('probe_complete_rate','mean')).reset_index()
    main['ci95_half_width']=1.96*main.sd/np.sqrt(frame.seed.nunique())
    paired=[]
    for (name, quota),rows in frame.groupby(['scenario','quota'],sort=False):
        tab=rows.pivot(index='seed',columns='method',values='profit')
        for method in POLICIES[:-1]:
            vals=tab['v5 VOI rank']-tab[method]
            paired.append(dict(scenario=name,quota=quota,voi_minus=method,
                          mean_difference=float(vals.mean()),
                          ci95_half_width=float(1.96*vals.std(ddof=1)/np.sqrt(len(vals))),
                          comparison_seed_count=len(vals)))
    return main,pd.DataFrame(paired)



def natural_diagnostics(seeds=SEEDS, scenario_names=None, n=N_TERMS):
    """Separately assess unconstrained model-positive VOI and no deferral.

    These differ in allocation rates and are NOT matched-quota comparisons.
    """
    names=tuple(scenario_names or SCENARIOS)
    rows=[]
    for name in names:
        for seed in seeds:
            cohort=make_cohort(seed,SCENARIOS[name],n)
            scores=rank_terms(cohort,seed)
            for name_policy,selection in (
                ('No exploration', np.zeros(n,dtype=bool)),
                ('Positive-model-VOI gate', scores['v5 VOI rank']>1e-9)
            ):
                result=run_policy(cohort,selection)
                result.pop('spend_by_campaign'); result.pop('campaign_caps')
                rows.append(dict(scenario=name,seed=seed,method=name_policy,**result))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(exist_ok=True)
    data=evaluate()
    main,paired=summarize(data)
    data.to_csv(OUT/'independent_per_seed.csv',index=False)
    main.to_csv(OUT/'independent_summary.csv',index=False)
    paired.to_csv(OUT/'independent_paired.csv',index=False)
    diagnostic=natural_diagnostics()
    diagnostic.to_csv(OUT/'independent_unmatched_per_seed.csv',index=False)
    diagnostic.groupby(['scenario','method'],sort=False).agg(
        profit=('profit','mean'), defer_rate=('defer_rate','mean'),
        budget_utilisation=('budget_utilisation','mean')).reset_index().to_csv(
            OUT/'independent_unmatched_summary.csv',index=False)
    config={'seed_set':list(SEEDS),'quotas':list(QUOTAS),'n_terms':N_TERMS,
            'n_campaigns':N_CAMPAIGNS,'campaign_budget_reference':440,
            'probe_clicks':PROBE_CLICKS,'overhead':OVERHEAD,'assumed_margin':ASSUMED_MARGIN,
            'fixed_prior':list(PRIOR),'source_of_prior':'v5 training split',
            'policy_rank':'v5 one-step VOI (unchanged formula)',
            'outcome_model':'independent portfolio simulator, synthetic only',
            'scenario_specs':SCENARIOS,
            'unmatched_diagnostic':'No exploration and positive-model VOI gate (not matched quota)'}
    (OUT/'independent_config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    print('PRIMARY 10% QUOTA (profit per synthetic term; higher is better)')
    print(main[np.isclose(main.quota,.10)][['scenario','method','profit','ci95_half_width',
                               'budget_utilisation','maintain_rate']].round(4).to_string(index=False))
    print('\nPAIRED VOI vs UNCERTAINTY (profit; positive favors VOI)')
    print(paired[(np.isclose(paired.quota,.10)) &
                 (paired.voi_minus=='Profitability uncertainty')][['scenario','mean_difference','ci95_half_width']].round(4).to_string(index=False))

if __name__=='__main__':
    main()

