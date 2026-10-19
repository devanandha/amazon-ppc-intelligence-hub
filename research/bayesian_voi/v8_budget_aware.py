"""v8 exploratory budget-aware allocation and three-action sponsored-search decisions.

SYNTHETIC research ONLY. Not Amazon Ads API logic, not suitable for bid changes.
The v7 simulator is used unchanged for its outcome generation. The v8 shared
follow-up variant reuses v7 evaluation mechanics, replacing only its action rule.
See V8_PROTOCOL.md, written before accessing any v8 held-out results.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import betabinom

import independent_outcomes as v7
from fair_baselines import allocate

OUT = Path(__file__).resolve().parent / 'results'
TRAIN_SEEDS = tuple(range(32000, 32012))
TEST_SEEDS = tuple(range(42000, 42030))
TRAIN_SCENARIOS = ('Mixture reference', 'Auction costs +35%', 'Campaign budgets halved')
SCENARIOS = tuple(v7.SCENARIOS)
GAMMAS = (0.0, 0.20, 0.50)
QUOTAS = (.05, .10, .20)
PRIMARY_QUOTA = .10
ACTIONS = np.asarray(['NEGATIVE', 'MAINTAIN', 'SCALE'])
METHODS = ('Random', 'Fewest clicks', 'Profitability uncertainty', 'v5 VOI rank', 'v8 budget VOI')
ACTION_MODES = ('v7 heuristic action', 'v8 budget action')
N = v7.N_TERMS
# Exact same simulator constants as the published v7 portfolio accounting.
OVERHEAD = v7.OVERHEAD
PROBE_CLICKS = v7.PROBE_CLICKS
FUTURE_MAX_CLICKS = v7.FUTURE_MAX_CLICKS
PRIOR = v7.PRIOR
ASSUMED_MARGIN = v7.ASSUMED_MARGIN


def _validate_inputs(clicks, orders, cpc, aov, campaign, budget_mult, gamma):
    c = np.asarray(clicks, dtype=float)
    o = np.asarray(orders, dtype=float)
    cost = np.asarray(cpc, dtype=float)
    value = np.asarray(aov, dtype=float)
    camp = np.asarray(campaign)
    if not (c.ndim == 1 and c.shape == o.shape == cost.shape == value.shape == camp.shape and len(c) > 0):
        raise ValueError('Observed fields must be matching nonempty vectors')
    if not (np.isfinite(c).all() and np.isfinite(o).all() and np.isfinite(cost).all() and np.isfinite(value).all()):
        raise ValueError('Observed fields must be finite')
    if (np.any(c < 0) or np.any(o < 0) or np.any(o > c) or np.any(c != np.floor(c))
            or np.any(o != np.floor(o)) or np.any(cost <= 0) or np.any(value <= 0)):
        raise ValueError('Invalid counts, CPC or AOV')
    if (not np.issubdtype(camp.dtype, np.integer) or np.any(camp < 0)
            or not np.isfinite(budget_mult) or budget_mult <= 0
            or not np.isfinite(gamma) or gamma < 0 or gamma > 1):
        raise ValueError('Invalid campaign, announced budget or shadow parameter')
    return c, o, cost, value, camp


def _posterior_utilities(posterior_p, cpc, aov, budget_mult, gamma):
    """Expected action values using policy ASSUMPTIONS, not test latent outcomes.

    Supports posterior_p shapes (n,) and (n,m) for predictive calculations.
    Fair budget shares are deliberately naive and are not the simulator's
    sequence-dependent realised remaining balances.
    """
    p = np.asarray(posterior_p, dtype=float)
    cost = np.asarray(cpc, dtype=float)
    value = np.asarray(aov, dtype=float)
    if p.ndim not in (1, 2) or p.shape[0] != len(cost):
        raise ValueError('Expected a per-term posterior array')
    expand = p.ndim == 2
    costv = cost[:, None] if expand else cost
    valuev = value[:, None] if expand else value
    share = 440. * budget_mult / v7.TERMS_PER_CAMPAIGN
    # Budget shadow term is an heuristic known-budget surcharge, not a real auction prediction.
    scarcity = np.maximum(0., 1. - share/(38. * cost))
    shadow = gamma * scarcity
    cv = shadow[:, None] if expand else shadow
    clicks_keep = np.minimum(38., share/costv)
    clicks_scale = np.minimum(53., share/(1.16*costv))
    maintain = clicks_keep * (p*v7.ASSUMED_MARGIN*valuev - costv*(1.+cv))
    scale = clicks_scale * (p*.90*v7.ASSUMED_MARGIN*valuev -1.16*costv*(1.+cv))
    return np.stack(np.broadcast_arrays(np.zeros_like(p), maintain, scale), axis=-1)


def budget_action(clicks, orders, cpc, aov, campaign, budget_mult, gamma):
    """Select NEGATIVE / MAINTAIN / SCALE by predicted *budget-aware* value."""
    c,o,cp,av,camp = _validate_inputs(clicks,orders,cpc,aov,campaign,budget_mult,gamma)
    a=v7.PRIOR[0]+o; b=v7.PRIOR[1]+c-o
    values = _posterior_utilities(a/(a+b),cp,av,budget_mult,gamma)
    return ACTIONS[np.argmax(values,axis=-1)]


def budget_voi_score(clicks, orders, cpc, aov, campaign, budget_mult, gamma):
    """One-step hypothetical information value for THREE actions, incl. budget share.

    Uses only observable historical records and announced campaign budget. Posterior
    predictive conversions after a 10-click probe are beta-binomial. Fixed quotas
    can force a probe despite negative predicted gain (reported explicitly).
    """
    c,o,cp,av,camp = _validate_inputs(clicks,orders,cpc,aov,campaign,budget_mult,gamma)
    a = v7.PRIOR[0]+o; b = v7.PRIOR[1]+c-o
    p = a/(a+b)
    immediate = np.max(_posterior_utilities(p,cp,av,budget_mult,gamma),axis=-1)
    k = np.arange(v7.PROBE_CLICKS+1)
    predictive=betabinom.pmf(k[None,:],v7.PROBE_CLICKS,a[:,None],b[:,None])
    after_p=(a[:,None]+k[None,:])/(a[:,None]+b[:,None]+v7.PROBE_CLICKS)
    post=np.max(_posterior_utilities(after_p,cp,av,budget_mult,gamma),axis=-1)
    exp_post=np.sum(predictive*post,axis=1)
    expected_probe_margin=v7.PROBE_CLICKS*(p*v7.ASSUMED_MARGIN*av-cp)
    budget_share=440.*budget_mult/v7.TERMS_PER_CAMPAIGN
    scarcity=np.maximum(0.,1.-budget_share/(38.*cp))
    estimated_probe_opportunity=gamma*scarcity*cp*v7.PROBE_CLICKS
    return exp_post-immediate+expected_probe_margin-v7.OVERHEAD-estimated_probe_opportunity


def rank_terms(cohort, seed, gamma):
    """v8 only uses observable columns, campaign membership and known budget."""
    observed = {k:cohort[k] for k in ('clicks','orders','cpc','aov','campaign')}
    base = v7.rank_terms(cohort,seed)
    base['v8 budget VOI']=budget_voi_score(**observed,budget_mult=cohort['scenario']['budget_mult'],gamma=gamma)
    return base


# The portfolio simulator below is directly adapted from the v7 run_policy
# accounting, exploration and auction allocation loops; the SOLE mechanics
# change is substituting the announced-budget-aware decision rule. The source
# v7 run_policy remains available unchanged for action-mode ablation.

def run_policy_v8(cohort: dict, selected, gamma: float, *, check_budget=True):
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
    action = budget_action(clicks, observed_orders,cohort['cpc'],cohort['aov'],cohort['campaign'],scenario['budget_mult'],gamma)
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



def evaluate_one(cohort, seed, gamma, quota, action_mode):
    scores = rank_terms(cohort,seed,gamma)
    data=[]
    for name in METHODS:
        selection=allocate(scores[name],quota)
        result = (v7.run_policy(cohort,selection) if action_mode=='v7 heuristic action'
                  else run_policy_v8(cohort,selection,gamma))
        result.pop('spend_by_campaign'); result.pop('campaign_caps')
        data.append(dict(method=name,**result))
    return data


def train_gamma():
    """Fix v8 shadow gamma using TRAIN seeds, BEFORE test seed generation."""
    rows=[]
    for gamma in GAMMAS:
        profits=[]
        for scenario in TRAIN_SCENARIOS:
            for seed in TRAIN_SEEDS:
                cohort=v7.make_cohort(seed,v7.SCENARIOS[scenario])
                selected=allocate(rank_terms(cohort,seed,gamma)['v8 budget VOI'],PRIMARY_QUOTA)
                result=run_policy_v8(cohort,selected,gamma)
                profits.append(result['profit'])
        rows.append(dict(gamma=gamma,train_mean_profit=float(np.mean(profits)),train_sd=float(np.std(profits,ddof=1)),training_scenario_count=len(TRAIN_SCENARIOS),training_seeds=len(TRAIN_SEEDS)))
    table=pd.DataFrame(rows)
    best=min(GAMMAS,key=lambda g:(-table.loc[table.gamma==g,'train_mean_profit'].iloc[0],g))
    return best,table


def heldout_evaluation(gamma, seeds=TEST_SEEDS, scenarios=SCENARIOS, quotas=QUOTAS):
    rows=[]
    for scenario_name in scenarios:
        for seed in seeds:
            cohort=v7.make_cohort(seed,v7.SCENARIOS[scenario_name])
            for quota in quotas:
                for action_mode in ACTION_MODES:
                    for d in evaluate_one(cohort,seed,gamma,quota,action_mode):
                        rows.append(dict(scenario=scenario_name,seed=seed,quota=quota,action_mode=action_mode,**d))
    return pd.DataFrame(rows)


def summarize(frame):
    keys=['scenario','quota','action_mode','method']
    summary=frame.groupby(keys,sort=False).agg(mean_profit=('profit','mean'),sd_profit=('profit','std'),spend=('spend_per_term','mean'),budget_utilisation=('budget_utilisation','mean'),mean_scale_rate=('scale_rate','mean'),mean_maintain_rate=('maintain_rate','mean'),defer_rate=('defer_rate','mean')).reset_index()
    summary['descriptive_ci95_halfwidth']=1.96*summary.sd_profit/np.sqrt(frame.seed.nunique())
    diffs=[]
    for (scenario,quota,mode),group in frame.groupby(['scenario','quota','action_mode'],sort=False):
        pv=group.pivot(index='seed',columns='method',values='profit')
        for baseline in METHODS[:-1]:
            values=pv['v8 budget VOI']-pv[baseline]
            diffs.append(dict(scenario=scenario,quota=quota,action_mode=mode,contrast='v8 rank minus '+baseline,mean_diff=float(values.mean()),halfwidth_95=float(1.96*values.std(ddof=1)/np.sqrt(len(values))),seed_count=len(values)))
    for (scenario,quota,method),group in frame.groupby(['scenario','quota','method'],sort=False):
        pv=group.pivot(index='seed',columns='action_mode',values='profit')
        values=pv['v8 budget action']-pv['v7 heuristic action']
        diffs.append(dict(scenario=scenario,quota=quota,action_mode='action ablation',contrast=method+': v8 action minus v7 action',mean_diff=float(values.mean()),halfwidth_95=float(1.96*values.std(ddof=1)/np.sqrt(len(values))),seed_count=len(values)))
    return summary,pd.DataFrame(diffs)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    gamma,train=train_gamma()
    # TEST SEEDS FIRST USED ONLY AFTER gamma locked by separate train sets.
    test=heldout_evaluation(gamma)
    summary,paired=summarize(test)
    train.to_csv(OUT/'v8_training.csv',index=False)
    test.to_csv(OUT/'v8_per_seed.csv',index=False)
    summary.to_csv(OUT/'v8_summary.csv',index=False)
    paired.to_csv(OUT/'v8_paired.csv',index=False)
    config={'training_seeds':list(TRAIN_SEEDS),'training_scenarios':list(TRAIN_SCENARIOS),'test_seeds':list(TEST_SEEDS),'test_scenarios':list(SCENARIOS),'candidate_gamma':list(GAMMAS),'selected_gamma':float(gamma),'quotas':list(QUOTAS),'primary_quota':PRIMARY_QUOTA,'policies':list(METHODS),'action_modes':list(ACTION_MODES),'simulator':'unmodified v7 make_cohort; v7 accounting loops with action-only switch','data':'synthetic only, not Amazon Ads'}
    (OUT/'v8_config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    print('gamma selected only on train:',gamma)
    print(train.round(4).to_string(index=False))
    print('\nPRIMARY 10% held-out summary:')
    print(summary[np.isclose(summary.quota,.10)][['scenario','action_mode','method','mean_profit','descriptive_ci95_halfwidth']].round(4).to_string(index=False))
    print('\nPRIMARY 10% paired rankings:')
    print(paired[(np.isclose(paired.quota,.10))&(paired.contrast.isin(['v8 rank minus Profitability uncertainty','v8 rank minus v5 VOI rank']))][['scenario','action_mode','contrast','mean_diff','halfwidth_95']].round(4).to_string(index=False))
    return gamma,train,summary,paired


if __name__ == '__main__':
    main()
