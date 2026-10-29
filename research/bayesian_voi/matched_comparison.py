"""Exploratory action-matched synthetic comparator.

All policies choose only SCALE, NEGATIVE or COLLECT_DATA at time zero.
If deferred, all policies acquire the same m click observations and choose the
same posterior-mean Bayes SCALE or NEGATIVE action for H-m remaining units.
Same latent terms and prospective conversions per seed. Model is synthetic and
assumes stationary conversion rates and known unit economics.

IMPORTANT: fixed gates and VOI are not threshold-tuned on a held-out population;
this is a fairness diagnostic, not external validation or novelty proof.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from adaptive_policy import (immediate_bayes, confidence_gate, one_step_voi)
from evaluate_pilot import draw_terms, HORIZON, EXPLORE, MARGIN

SEEDS = tuple(range(2000, 2025))
POLICIES=('Immediate Bayesian','Fixed 15-click Bayesian gate','Fixed 25-click Bayesian gate',
          '95% probability Bayesian gate','One-step Bayesian VOI')
N=2500
PRIOR=(1.,9.)
OUT=Path(__file__).resolve().parent/'results'


def select(clicks, orders, cpc, aov, policy, overhead=0., prior=PRIOR):
    immediate=immediate_bayes(clicks,orders,cpc,aov,MARGIN,prior)
    if policy=='Immediate Bayesian':return immediate
    if policy=='Fixed 15-click Bayesian gate':return np.where(clicks<15,'COLLECT_DATA',immediate)
    if policy=='Fixed 25-click Bayesian gate':return np.where(clicks<25,'COLLECT_DATA',immediate)
    if policy=='95% probability Bayesian gate':
        conf=confidence_gate(clicks,orders,cpc,aov,MARGIN,prior)
        return np.where(conf=='COLLECT_DATA','COLLECT_DATA',immediate)
    if policy=='One-step Bayesian VOI':
        return one_step_voi(clicks,orders,cpc,aov,MARGIN,prior,HORIZON,EXPLORE,
                            scale_factor=1.25,explore_cost=overhead)
    raise KeyError(policy)


def run(overhead=0., n=N, seeds=SEEDS):
    rows=[]
    for seed in seeds:
        n_clicks,orders,cpc,aov,p,future=draw_terms(seed,n)
        mu=p*aov*MARGIN-cpc
        oracle=HORIZON*1.25*np.maximum(mu,0)
        for policy in POLICIES:
            action=select(n_clicks,orders,cpc,aov,policy,overhead)
            deferred=action=='COLLECT_DATA'
            # Initial decisions use same 125% or 0 exposure, same economics.
            utility=np.where(action=='SCALE',HORIZON*1.25*mu,0.).astype(float)
            if deferred.any():
                ix=np.where(deferred)[0]
                post=immediate_bayes(n_clicks[ix]+EXPLORE,orders[ix]+future[ix],cpc[ix],aov[ix],MARGIN,PRIOR)
                # Same m observation window, m baseline clicks, time/economic cost.
                utility[ix]=EXPLORE*mu[ix]+(HORIZON-EXPLORE)*1.25*np.where(post=='SCALE',mu[ix],0)-overhead
            regret=oracle-utility
            # Regret can be >oracle (overhead), but not negative as oracle knows latent p
            if not np.all(regret>=-1e-8):raise RuntimeError('Oracle inconsistency')
            rows.append(dict(seed=seed,policy=policy,overhead=overhead,
                             regret=float(regret.mean()),defer_rate=float(deferred.mean()),
                             utility=float(utility.mean())))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(exist_ok=True)
    all_runs=pd.concat([run(overhead=x) for x in (0.,2.)],ignore_index=True)
    all_runs.to_csv(OUT/'matched_per_seed.csv',index=False)
    summary=all_runs.groupby(['overhead','policy'],sort=False).agg(
        regret=('regret','mean'),regret_sd=('regret','std'),defer_rate=('defer_rate','mean'))
    summary['regret_ci95_half_width']=1.96*summary.regret_sd/np.sqrt(len(SEEDS))
    summary.reset_index().to_csv(OUT/'matched_summary.csv',index=False)
    print(summary.round(4).to_string())
    # paired differences relative to myopic, independent of inter-seed variability
    diff=[]
    for overhead,g in all_runs.groupby('overhead'):
        pivot=g.pivot(index='seed',columns='policy',values='regret')
        for policy in POLICIES:
            if policy=='Immediate Bayesian':continue
            d=pivot[policy]-pivot['Immediate Bayesian']
            diff.append(dict(overhead=overhead,policy=policy,mean_regret_difference=float(d.mean()),
                ci95_half_width=float(1.96*d.std(ddof=1)/np.sqrt(len(d)))))
    pd.DataFrame(diff).to_csv(OUT/'matched_paired_differences.csv',index=False)

if __name__=='__main__':main()

