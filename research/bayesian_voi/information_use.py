"""Frozen information-use intervention. See INFORMATION_USE_PROTOCOL.md.

Accounting adapted verbatim from v8 with one intervention: when observations
are withheld, restore historical counts before BOTH action and priority.
Extra return fields expose decomposition and paired accounting invariants.
"""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd
import v8_budget_aware as v8
import independent_outcomes as v7
import v8_posthoc_diagnostics as post
from v8_budget_aware import budget_action, PRIOR, ASSUMED_MARGIN, OVERHEAD, PROBE_CLICKS, FUTURE_MAX_CLICKS
from fair_baselines import allocate

SEEDS = tuple(range(52000,52030))
QUOTAS = (.05,.10,.20)
OUT = Path(__file__).parent/'information_results'

def run_information_policy(cohort: dict, selected, gamma: float = 0.0, *, use_evidence=True, check_budget=True):
    """Two-stage portfolio, with exploration first and budget-limited auction traffic.

    Within each selected-set pair, only access to new probe evidence changes.
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
    if not use_evidence:
        clicks = cohort['clicks'].astype(int).copy()
        observed_orders = cohort['orders'].astype(int).copy()
    probe_contribution = profit
    probe_spend_by_campaign = spend_per_campaign.copy()
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
            'probe_contribution_per_term':float(probe_contribution/n),
            'downstream_contribution_per_term':float((profit-probe_contribution)/n),
            'probe_spend_by_campaign':probe_spend_by_campaign,
            'actions':action.copy(), 'priority':priority.copy(),
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


def ranking_scores(cohort, seed):
    scores=v8.rank_terms(cohort,seed,0.0)
    simple=post.simple_scores(cohort)
    scores['Unit profit']=simple['Highest expected unit contribution']
    scores['Profit per CPC']=simple['Highest expected contribution per CPC']
    return scores


def evaluate(seeds=SEEDS, scenarios=None, quotas=QUOTAS):
    rows=[]; pairs=[]; selections=[]
    for name in (v8.SCENARIOS if scenarios is None else scenarios):
        for seed in seeds:
            c=v7.make_cohort(seed,v7.SCENARIOS[name])
            scores=ranking_scores(c,seed)
            no=run_information_policy(c,np.zeros(len(c['clicks']),bool))
            rows.append(dict(scenario=name,seed=seed,quota=0.0,method='No probe',arm='no_probe',**{k:no[k] for k in scalar_keys()}))
            for quota in quotas:
                v8sel=allocate(scores['v8 budget VOI'],quota)
                profitsel=allocate(scores['Unit profit'],quota)
                selections.append(dict(scenario=name,seed=seed,quota=quota,identical=bool(np.array_equal(v8sel,profitsel)),selected_overlap=float((v8sel&profitsel).sum()/v8sel.sum())))
                for method,score in scores.items():
                    selected=allocate(score,quota)
                    use=run_information_policy(c,selected,use_evidence=True)
                    withheld=run_information_policy(c,selected,use_evidence=False)
                    for k in ['probe_contribution_per_term','probe_spend','probe_complete_rate']:
                        if use[k]!=withheld[k]:raise AssertionError('Probe matching failed: '+k)
                    np.testing.assert_array_equal(use['probe_spend_by_campaign'],withheld['probe_spend_by_campaign'])
                    for arm,result in [('use',use),('withhold',withheld)]:
                        np.testing.assert_allclose(result['profit'],result['probe_contribution_per_term']+result['downstream_contribution_per_term'],rtol=1e-12,atol=1e-12)
                        rows.append(dict(scenario=name,seed=seed,quota=quota,method=method,arm=arm,**{k:result[k] for k in scalar_keys()}))
                    pairs.append(dict(scenario=name,seed=seed,quota=quota,method=method,
                        information_effect=use['profit']-withheld['profit'],
                        use_minus_no_probe=use['profit']-no['profit'],
                        withhold_minus_no_probe=withheld['profit']-no['profit'],
                        action_change_fraction=float(np.mean(use['actions']!=withheld['actions'])),
                        priority_change_fraction=float(np.mean(use['priority']!=withheld['priority']))))
    return pd.DataFrame(rows),pd.DataFrame(pairs),pd.DataFrame(selections)


def scalar_keys():
    return ('profit','probe_contribution_per_term','downstream_contribution_per_term','spend_per_term','budget_utilisation','probe_spend','probe_complete_rate','defer_rate')


def summarize(rows,pairs):
    summary=rows.groupby(['scenario','quota','method','arm'],sort=False)[list(scalar_keys())].mean().reset_index()
    out=[]
    for keys,g in pairs.groupby(['scenario','quota','method'],sort=False):
        for metric in ('information_effect','use_minus_no_probe','withhold_minus_no_probe'):
            x=g[metric]
            mean=float(x.mean()); half=float(1.96*x.std(ddof=1)/np.sqrt(len(x)))
            out.append(dict(zip(('scenario','quota','method'),keys),contrast=metric,mean_diff=mean,halfwidth_95=half,ci_low=mean-half,ci_high=mean+half,seed_count=len(x)))
    return summary,pd.DataFrame(out)


def main():
    # Do not modify this design after seeing 52000-series outcomes.
    OUT.mkdir(exist_ok=True)
    rows,pairs,selections=evaluate()
    summary,contrasts=summarize(rows,pairs)
    for name,frame in [('per_seed',rows),('paired',pairs),('selection',selections),('summary',summary),('contrasts',contrasts)]:frame.to_csv(OUT/(name+'.csv'),index=False)
    config={'seeds':list(SEEDS),'scenarios':list(v8.SCENARIOS),'quotas':list(QUOTAS),'primary_quota':.1,'gamma':0.0,'methods':list(ranking_scores(v7.make_cohort(SEEDS[0],v7.SCENARIOS[v8.SCENARIOS[0]]),SEEDS[0])),'data':'synthetic only; fresh seeds within unchanged simulator; not independent external data','protocol_sha256':hashlib.sha256((Path(__file__).parent/'INFORMATION_USE_PROTOCOL.md').read_bytes()).hexdigest()}
    (OUT/'config.json').write_text(json.dumps(config,indent=2))
    print('Complete grid',len(rows),'policy evaluations',len(pairs),'matched information-use contrasts')
    print(contrasts[(contrasts.quota==.1)&(contrasts.method=='v8 budget VOI')].round(4).to_string(index=False))


if __name__=='__main__':main()


