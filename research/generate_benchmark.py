"""Generate a reproducible synthetic PPC benchmark with latent ground-truth states."""
from pathlib import Path
import numpy as np
import pandas as pd

STATES = ["SCALE", "MAINTAIN", "REDUCE", "NEGATIVE", "COLLECT_DATA"]
PARAMS = {
    "SCALE":        dict(imp=(1200,6000), ctr=(.018,.045), cvr=(.14,.25), cpc=(.35,.75), aov=(24,40)),
    "MAINTAIN":     dict(imp=(1000,5500), ctr=(.012,.035), cvr=(.08,.16), cpc=(.40,.85), aov=(22,38)),
    "REDUCE":       dict(imp=(1000,6000), ctr=(.012,.04),  cvr=(.025,.08),cpc=(.80,1.45), aov=(18,32)),
    "NEGATIVE":     dict(imp=(900,5000),  ctr=(.015,.05),  cvr=(0,.012),   cpc=(.70,1.40), aov=(18,30)),
    "COLLECT_DATA": dict(imp=(50,500),    ctr=(.003,.02),  cvr=(.03,.18),  cpc=(.30,1.00), aov=(18,38)),
}

def generate(n=5000, seed=42):
    rng=np.random.default_rng(seed)
    states=rng.choice(STATES,n,p=[.20,.25,.20,.20,.15])
    rows=[]
    for i,s in enumerate(states):
        p=PARAMS[s]
        imp=int(rng.integers(*p["imp"]))
        ctr=rng.uniform(*p["ctr"]); clicks=int(rng.binomial(imp,ctr))
        cpc=rng.uniform(*p["cpc"]); spend=round(clicks*cpc,2)
        cvr=rng.uniform(*p["cvr"]); orders=int(rng.binomial(clicks,cvr)) if clicks else 0
        aov=rng.uniform(*p["aov"]); sales=round(orders*aov,2)
        rows.append(dict(id=i,ground_truth=s,impressions=imp,clicks=clicks,spend=spend,sales=sales,orders=orders,
                         ctr=100*clicks/imp if imp else 0,cpc=spend/clicks if clicks else 0,
                         cvr=100*orders/clicks if clicks else 0,
                         acos=100*spend/sales if sales else np.nan,roas=sales/spend if spend else 0))
    return pd.DataFrame(rows)

if __name__=="__main__":
    out=Path(__file__).parent/"data"/"benchmark.csv"; out.parent.mkdir(parents=True,exist_ok=True)
    df=generate(); df.to_csv(out,index=False); print(f"Wrote {len(df)} rows to {out}")
