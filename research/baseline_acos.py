"""Single-metric ACOS baseline."""
import pandas as pd

def predict(df: pd.DataFrame, target_acos=25.0):
    out=[]
    for _,r in df.iterrows():
        if pd.isna(r.acos): out.append("NEGATIVE")
        elif r.acos <= target_acos*.8: out.append("SCALE")
        elif r.acos <= target_acos: out.append("MAINTAIN")
        else: out.append("REDUCE")
    return out
