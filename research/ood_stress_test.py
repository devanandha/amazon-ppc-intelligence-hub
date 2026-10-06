"""Out-of-distribution stress tests for the frozen PPC decision frameworks.

This script does not alter the primary 50-seed experiment. It challenges external
validity by perturbing the synthetic generator after the primary rules were frozen.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from generate_benchmark import generate
import baseline_acos, baseline_rules, proposed_framework

MODELS={"ACOS-only":baseline_acos.predict,"Evidence-aware":baseline_rules.predict,
        "Multi-metric":proposed_framework.predict}

def perturb(df, scenario, rng):
    x=df.copy()
    if scenario=="cost_inflation":
        x["spend"]*=1.25; x["cpc"]=np.where(x.clicks>0,x.spend/x.clicks,0)
    elif scenario=="conversion_degradation":
        # prospective stress: reduce realised orders by 25% without using labels
        x["orders"]=rng.binomial(x["orders"].astype(int),.75)
        # preserve observed AOV where identifiable
        aov=np.where(df.orders>0,df.sales/df.orders,0)
        x["sales"]=x.orders*aov
    elif scenario=="sparse_traffic":
        x["clicks"]=rng.binomial(x["clicks"].astype(int),.60)
        x["orders"]=np.minimum(x["orders"].astype(int),x["clicks"].astype(int))
        x["spend"]=x.clicks*df.cpc
        aov=np.where(df.orders>0,df.sales/df.orders,0)
        x["sales"]=x.orders*aov
    elif scenario=="noisy_metrics":
        x["spend"]*=rng.lognormal(0,.15,len(x))
        x["sales"]*=rng.lognormal(0,.15,len(x))
    x["ctr"]=np.where(x.impressions>0,100*x.clicks/x.impressions,0)
    x["cpc"]=np.where(x.clicks>0,x.spend/x.clicks,0)
    x["cvr"]=np.where(x.clicks>0,100*x.orders/x.clicks,0)
    x["acos"]=np.where(x.sales>0,100*x.spend/x.sales,np.nan)
    x["roas"]=np.where(x.spend>0,x.sales/x.spend,0)
    return x

def main():
    rows=[]
    for seed in range(50):
        base=generate(n=5000,seed=seed)
        for scenario in ["cost_inflation","conversion_degradation","sparse_traffic","noisy_metrics"]:
            rng=np.random.default_rng(10000+seed)
            df=perturb(base,scenario,rng)
            for name,fn in MODELS.items():
                pred=fn(df)
                p,r,f,_=precision_recall_fscore_support(df.ground_truth,pred,average="macro",zero_division=0)
                rows.append([seed,scenario,name,accuracy_score(df.ground_truth,pred),p,r,f])
    out=pd.DataFrame(rows,columns=["seed","scenario","method","accuracy","macro_precision","macro_recall","macro_f1"])
    out.to_csv("research/results/ood_stress_runs.csv",index=False)
    summary=out.groupby(["scenario","method"],as_index=False)[["accuracy","macro_f1"]].agg(["mean","std"])
    summary.to_csv("research/results/ood_stress_summary.csv")
    print(summary.to_string())

if __name__=="__main__": main()
