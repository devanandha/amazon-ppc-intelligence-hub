"""Exploratory stress checks added after reviewing the primary run; seeds 3000..3019.
The same simulated terms and follow-up clicks compare Bayes myopic and one-step VOI.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from adaptive_policy import immediate_bayes, one_step_voi

H=100; M=10; PRIOR=(1.,9.); MARGIN=.25
REGIMES={
 'Lower conversion': {'p':(.005,.05),'cpc':(.3,1.5),'aov':(20.,50.)},
 'Higher conversion':{'p':(.08,.30),'cpc':(.3,1.5),'aov':(20.,50.)},
 'Higher CPC':{'p':(.005,.2),'cpc':(1.1,2.),'aov':(20.,50.)},
 'Lower order value':{'p':(.005,.2),'cpc':(.3,1.5),'aov':(12.,30.)},
}

def evaluate(seed, ranges, extra_cost=0.):
    rng=np.random.default_rng(seed)
    n=2500
    clicks=rng.integers(5,201,n)
    p=rng.uniform(*ranges['p'],size=n)
    cpc=rng.uniform(*ranges['cpc'],size=n)
    aov=rng.uniform(*ranges['aov'],size=n)
    orders=rng.binomial(clicks,p)
    future=rng.binomial(M,p)
    mu=p*aov*MARGIN-cpc
    oracle=H*1.25*np.maximum(mu,0.)
    a=immediate_bayes(clicks,orders,cpc,aov,MARGIN,PRIOR)
    regret_myopic=(oracle-np.where(a=='SCALE',H*1.25*mu,0)).mean()
    v=one_step_voi(clicks,orders,cpc,aov,MARGIN,PRIOR,H,M,explore_cost=extra_cost)
    utility=np.where(v=='SCALE',H*1.25*mu,0.)
    choose=v=='COLLECT_DATA'
    idx=np.where(choose)[0]
    if len(idx):
        final=immediate_bayes(clicks[idx]+M,orders[idx]+future[idx],cpc[idx],aov[idx],MARGIN,PRIOR)
        utility[idx]=M*mu[idx]+np.where(final=='SCALE',(H-M)*1.25*mu[idx],0.)-extra_cost
    regret_voi=(oracle-utility).mean()
    return regret_myopic,regret_voi,float(choose.mean())

def main():
    out=Path(__file__).parent/'results';out.mkdir(exist_ok=True)
    rows=[]
    for regime,rg in REGIMES.items():
        for cost in (0.,2.):
            for seed in range(3000,3020):
                rm,rv,collect=evaluate(seed,rg,extra_cost=cost)
                rows.append({'regime':regime,'exploration_overhead':cost,'seed':seed,
                             'myopic_regret':rm,'voi_regret':rv,
                             'voi_minus_myopic':rv-rm,'collect_rate':collect})
    d=pd.DataFrame(rows);d.to_csv(out/'stress_per_seed.csv',index=False)
    summary=d.groupby(['regime','exploration_overhead'],as_index=False).agg(
        myopic_regret=('myopic_regret','mean'),voi_regret=('voi_regret','mean'),
        voi_minus_myopic=('voi_minus_myopic','mean'),
        paired_sd=('voi_minus_myopic','std'),collect_rate=('collect_rate','mean'))
    summary['paired_ci95_half_width']=1.96*summary.paired_sd/np.sqrt(20)
    summary.to_csv(out/'stress_summary.csv',index=False)
    print(summary.round(4).to_string(index=False))

if __name__=='__main__':main()
