"""Reproducible exploratory synthetic diagnostic for PPC v2 (not external validation).

Seed range fixed in this script before initial execution: 2000..2024, 2500 terms each, future horizon 100,
explore 10 clicks, fixed 25% contribution margin. No per-seed tuning; not an external preregistration.
Models are assessed on the same sampled latent terms / follow-up conversions.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from adaptive_policy import immediate_bayes, confidence_gate, one_step_voi

OUT=Path(__file__).parent/'results'
METHODS=('ACOS only','Fixed 15-click gate','ORF evidence gate',
         'Bayesian myopic','Bayesian 95% confidence','Bayesian one-step VOI')
EXPOSURE={'SCALE':1.25,'MAINTAIN':1.0,'REDUCE':.50,'NEGATIVE':0.,'COLLECT_DATA':1.}
HORIZON=100; EXPLORE=10; MARGIN=.25; PRIOR=(1.,9.)
SEEDS=range(2000,2025); N_TERMS=2500


def draw_terms(seed, n=N_TERMS):
    """Independent continuous latent profitability, matching ORF diagnostic distributions."""
    r=np.random.default_rng(seed)
    clicks=r.integers(5,201,n)
    p=r.uniform(.005,.20,n)
    cpc=r.uniform(.30,1.50,n)
    aov=r.uniform(20.,50.,n)
    orders=r.binomial(clicks,p)
    # common potential outcome after subsequent 10 clicks for matched policies
    extra_orders=r.binomial(EXPLORE,p)
    return clicks, orders, cpc, aov, p, extra_orders


def classical(clicks, orders, cpc, aov, name):
    spend=clicks*cpc
    sales=orders*aov
    acos=np.divide(100*spend,sales,out=np.full(len(clicks),np.nan),where=sales>0)
    base=np.select([np.isnan(acos),acos<=20,acos<=25],
                   ['NEGATIVE','SCALE','MAINTAIN'],default='REDUCE')
    if name=='ACOS only': return base
    if name=='Fixed 15-click gate': return np.where(clicks<15,'COLLECT_DATA',base)
    if name=='ORF evidence gate':
        return np.where((clicks<5)|((orders==0)&(clicks<15)),'COLLECT_DATA',base)
    raise KeyError(name)


def initial(clicks,orders,cpc,aov,method,prior):
    if method in METHODS[:3]: return classical(clicks,orders,cpc,aov,method)
    if method=='Bayesian myopic':return immediate_bayes(clicks,orders,cpc,aov,MARGIN,prior)
    if method=='Bayesian 95% confidence':return confidence_gate(clicks,orders,cpc,aov,MARGIN,prior)
    if method=='Bayesian one-step VOI':return one_step_voi(clicks,orders,cpc,aov,MARGIN,prior,HORIZON,EXPLORE)
    raise KeyError(method)


def after_observation(clicks,orders,cpc,aov,method,prior):
    """Continue after deferral; still-inconclusive threshold rules maintain exposure."""
    if method in METHODS[:3]:
        action=classical(clicks,orders,cpc,aov,method)
        return np.where(action=='COLLECT_DATA','MAINTAIN',action)
    if method=='Bayesian 95% confidence':
        action=confidence_gate(clicks,orders,cpc,aov,MARGIN,prior)
        return np.where(action=='COLLECT_DATA','MAINTAIN',action)
    return immediate_bayes(clicks,orders,cpc,aov,MARGIN,prior)


def run(prior=PRIOR, label='main'):
    rows=[]
    for seed in SEEDS:
        clicks,orders,cpc,aov,p,extra=draw_terms(seed)
        true_mu=p*aov*MARGIN-cpc
        oracle=HORIZON*1.25*np.maximum(true_mu,0)
        for method in METHODS:
            action=initial(clicks,orders,cpc,aov,method,prior)
            exposure=np.array([EXPOSURE[a] for a in action])
            utility=HORIZON*exposure*true_mu
            is_collect=(action=='COLLECT_DATA')
            # Deferral uses first 10 clicks *within* the 100-click opportunity
            # horizon. The same latent follow-up conversions are shared across policies.
            if is_collect.any():
                idx=np.where(is_collect)[0]
                follow=after_observation(clicks[idx]+EXPLORE, orders[idx]+extra[idx],cpc[idx],aov[idx],method,prior)
                following_exposure=np.array([EXPOSURE[a] for a in follow])
                utility[idx]=EXPLORE*true_mu[idx]+(HORIZON-EXPLORE)*following_exposure*true_mu[idx]
            regret=oracle-utility
            if not np.all(regret>=-1e-7):raise RuntimeError('Oracle consistency broken')
            rows.append(dict(seed=seed,prior_label=label,method=method,regret=float(regret.mean()),
                             expected_utility=float(utility.mean()),
                             defer_rate=float(is_collect.mean()),
                             harmful_exclusion_rate=float(((action=='NEGATIVE')&(true_mu>0)).mean()),
                             harmful_scaling_rate=float(((action=='SCALE')&(true_mu<0)).mean())))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(exist_ok=True)
    main=run((1.,9.),'Beta(1,9)')
    alternate=run((1.,1.),'Beta(1,1)')
    results=pd.concat([main,alternate],ignore_index=True)
    results.to_csv(OUT/'per_seed.csv',index=False)
    summary=(results.groupby(['prior_label','method'],sort=False)
             .agg(regret=('regret','mean'),regret_sd=('regret','std'),
                  expected_utility=('expected_utility','mean'),
                  defer_rate=('defer_rate','mean'),
                  harmful_exclusion_rate=('harmful_exclusion_rate','mean'),
                  harmful_scaling_rate=('harmful_scaling_rate','mean')).reset_index())
    summary['regret_ci95_half_width']=1.96*summary.regret_sd/np.sqrt(len(SEEDS))
    summary.to_csv(OUT/'summary.csv',index=False)
    print(summary.round(4).to_string(index=False))

if __name__=='__main__':main()
