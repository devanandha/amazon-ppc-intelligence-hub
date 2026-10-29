"""POST-HOC exploratory negative controls, added AFTER v8 held-out result inspection.

Not part of originally fixed v8 protocol. These same seeds have already been
examined, so this check cannot be treated as independent confirmatory evidence.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import independent_outcomes as v7
import v8_budget_aware as v8
from fair_baselines import allocate

OUT=Path(__file__).resolve().parent/'results'


def simple_scores(d):
    p=(v7.PRIOR[0]+d['orders'])/(sum(v7.PRIOR)+d['clicks'])
    unit=p*v7.ASSUMED_MARGIN*d['aov']-d['cpc']
    return {'Highest expected unit contribution':unit,
            'Highest expected contribution per CPC':unit/d['cpc'],
            'Highest historical estimated CVR':p,
            'Pure modeled information value':v8.budget_voi_score(d['clicks'],d['orders'],d['cpc'],d['aov'],d['campaign'],d['scenario']['budget_mult'],0.0)-v7.PROBE_CLICKS*unit+v7.OVERHEAD}


def run(gamma,seed_set=v8.TEST_SEEDS,quota=.10):
    rows=[]
    for scenario_name in v8.SCENARIOS:
        for seed in seed_set:
            cohort=v7.make_cohort(seed,v7.SCENARIOS[scenario_name])
            scores=v8.rank_terms(cohort,seed,gamma)
            scores.update(simple_scores(cohort))
            selected_v8=allocate(scores['v8 budget VOI'],quota)
            for mode in v8.ACTION_MODES:
                for method in ('v8 budget VOI',*simple_scores(cohort)):
                    selected=allocate(scores[method],quota)
                    result=(v7.run_policy(cohort,selected) if mode=='v7 heuristic action'
                            else v8.run_policy_v8(cohort,selected,gamma))
                    rows.append(dict(scenario=scenario_name,seed=seed,action_mode=mode,method=method,
                                     profit=result['profit'],defer_rate=result['defer_rate'],
                                     selection_overlap_with_v8=float((selected&selected_v8).sum()/max(selected.sum(),1))))
    data=pd.DataFrame(rows)
    summary=data.groupby(['scenario','action_mode','method'],sort=False).agg(profit=('profit','mean'),selection_overlap_with_v8=('selection_overlap_with_v8','mean')).reset_index()
    pairs=[]
    for (scenario,mode),group in data.groupby(['scenario','action_mode'],sort=False):
        pivot=group.pivot(index='seed',columns='method',values='profit')
        for baseline in simple_scores(v7.make_cohort(seed_set[0],v7.SCENARIOS[scenario])):
            d=pivot['v8 budget VOI']-pivot[baseline]
            pairs.append(dict(scenario=scenario,action_mode=mode,comparator=baseline,mean_diff=float(d.mean()),halfwidth_95=float(1.96*d.std(ddof=1)/np.sqrt(len(d)))))
    paired=pd.DataFrame(pairs)
    return data,summary,paired


def main():
    gamma=float(pd.read_json(OUT/'v8_config.json',typ='series')['selected_gamma'])
    data,summary,paired=run(gamma)
    data.to_csv(OUT/'v8_posthoc_per_seed.csv',index=False)
    summary.to_csv(OUT/'v8_posthoc_summary.csv',index=False)
    paired.to_csv(OUT/'v8_posthoc_paired.csv',index=False)
    print('POST-HOC EXPLORATORY CHECK: v8 minus simple profit rankings (positive favors v8)')
    print(paired[paired.action_mode=='v8 budget action'].round(4).to_string(index=False))

if __name__=='__main__':main()

