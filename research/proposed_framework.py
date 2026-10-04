"""Proposed multi-metric, evidence-aware PPC decision framework."""
import pandas as pd

def predict(df: pd.DataFrame, target_acos=25.0, min_clicks=15, min_orders=3):
    out=[]
    for _,r in df.iterrows():
        if r.clicks < 5 or (r.orders < min_orders and r.clicks < min_clicks):
            a="COLLECT_DATA"
        elif r.orders==0 and r.clicks>=min_clicks:
            a="NEGATIVE"
        elif r.orders < min_orders:
            a="COLLECT_DATA"
        elif r.acos <= target_acos*.8 and r.cvr >= 8:
            a="SCALE"
        elif r.acos <= target_acos:
            a="MAINTAIN"
        elif r.acos <= target_acos*1.5 and r.cvr >= 4:
            a="REDUCE"
        else:
            a="REDUCE"
        out.append(a)
    return out
