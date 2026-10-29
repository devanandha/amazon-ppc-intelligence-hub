from pathlib import Path
import pandas as pd

root=Path(__file__).resolve().parent
summary=pd.read_csv(root/'results/v8_summary.csv')
paired=pd.read_csv(root/'results/v8_paired.csv')
out=root/'manuscript_tables'; out.mkdir(exist_ok=True)
summary[(summary.quota==.1)&(summary.action_mode=='v8 budget action')].to_csv(out/'Table_2_primary.csv',index=False)
selection=pd.read_csv(root/'audit_selection_checks.csv')
selection.groupby('quota').agg(cohorts=('equal_set','size'),identical_sets=('equal_set','sum'),mean_selected_overlap=('selected_overlap','mean'),mean_term_agreement=('term_agreement','mean')).reset_index().to_csv(out/'Table_3_selection.csv',index=False)
paired[(paired.quota==.1)&(paired.contrast=='v8 budget VOI: v8 action minus v7 action')].to_csv(out/'Table_4_action.csv',index=False)
print('Generated Tables 2 through 4 numerical sources')

info=pd.read_csv(root/'information_results/contrasts.csv')
info[(info.quota==.1)&(info.method=='v8 budget VOI')].to_csv(out/'Table_5_information.csv',index=False)
print('Generated Table 5 numerical source')
