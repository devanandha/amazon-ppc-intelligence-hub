"""Simple evidence-aware baseline using clicks/orders plus ACOS."""
import pandas as pd

def predict(df: pd.DataFrame, target_acos=25.0, min_clicks=15):
    out=[]
    for _,r in df.iterrows():
        if r.clicks < 5: a="COLLECT_DATA"
        elif r.orders==0 and r.clicks>=min_clicks: a="NEGATIVE"
        elif r.orders==0: a="COLLECT_DATA"
        elif r.acos <= target_acos*.8: a="SCALE"
        elif r.acos <= target_acos: a="MAINTAIN"
        else: a="REDUCE"
        out.append(a)
    return out
