"""Run reproducible comparison of PPC decision frameworks."""
from pathlib import Path
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from generate_benchmark import generate
import baseline_acos, baseline_rules, proposed_framework

def evaluate(y, pred):
    p,r,f,_=precision_recall_fscore_support(y,pred,average="macro",zero_division=0)
    return accuracy_score(y,pred),p,r,f

def main():
    root=Path(__file__).parent; results=root/"results"; results.mkdir(exist_ok=True)
    df=generate()
    models={"ACOS-only":baseline_acos.predict,"Evidence baseline":baseline_rules.predict,
            "Proposed multi-metric":proposed_framework.predict}
    rows=[]
    labels=["SCALE","MAINTAIN","REDUCE","NEGATIVE","COLLECT_DATA"]
    for name,fn in models.items():
        pred=fn(df); acc,p,r,f=evaluate(df.ground_truth,pred)
        rows.append(dict(method=name,accuracy=acc,macro_precision=p,macro_recall=r,macro_f1=f))
        pd.DataFrame(confusion_matrix(df.ground_truth,pred,labels=labels),index=labels,columns=labels).to_csv(results/f"confusion_{name.lower().replace(' ','_')}.csv")
    pd.DataFrame(rows).to_csv(results/"metrics.csv",index=False)

    sensitivity=[]
    for target in [20,25,30,35,40]:
        for clicks in [10,15,20,25]:
            pred=proposed_framework.predict(df,target_acos=target,min_clicks=clicks)
            acc,p,r,f=evaluate(df.ground_truth,pred)
            sensitivity.append(dict(target_acos=target,min_clicks=clicks,accuracy=acc,macro_f1=f))
    pd.DataFrame(sensitivity).to_csv(results/"sensitivity_analysis.csv",index=False)
    print(pd.DataFrame(rows).to_string(index=False))

if __name__=="__main__": main()
