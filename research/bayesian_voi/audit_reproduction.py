import json, platform
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import v8_budget_aware as v8
import v8_posthoc_diagnostics as post
import independent_outcomes as v7
from fair_baselines import allocate

root=Path(__file__).parent
comparisons=[]
for old in sorted((root/'published_v8_results').glob('v8_*.csv')):
    new=root/'results'/old.name
    if not new.exists(): continue
    if old.stat().st_size < 5:
        comparisons.append({'file':old.name,'comparison':'NOT COMPARED: connector did not return the published file body; rerun output retained'})
        continue
    a,b=pd.read_csv(old),pd.read_csv(new)
    try:
        pd.testing.assert_frame_equal(a,b,check_exact=False,rtol=1e-10,atol=1e-10)
        status='MATCH within rtol=atol=1e-10'
    except AssertionError as e: status='MISMATCH: '+str(e)[:400]
    comparisons.append({'file':old.name,'rows':len(b),'comparison':status})
gamma=json.loads((root/'results/v8_config.json').read_text())['selected_gamma']
selection=[]
for quota in v8.QUOTAS:
    for name in v8.SCENARIOS:
        for seed in v8.TEST_SEEDS:
            c=v7.make_cohort(seed,v7.SCENARIOS[name])
            s=allocate(v8.rank_terms(c,seed,gamma)['v8 budget VOI'],quota)
            p=allocate(post.simple_scores(c)['Highest expected unit contribution'],quota)
            selection.append({'quota':quota,'scenario':name,'seed':seed,'equal_set':bool(np.array_equal(s,p)), 'term_agreement':float(np.mean(s==p)), 'selected_overlap':float((s&p).sum()/s.sum())})
df=pd.DataFrame(selection)
df.to_csv(root/'audit_selection_checks.csv',index=False)
summary=df.groupby('quota').agg(cohorts=('equal_set','size'),identical_sets=('equal_set','sum'),mean_term_agreement=('term_agreement','mean'),mean_selected_overlap=('selected_overlap','mean')).reset_index()
report={'commit':'6e55061294278bd0adcb37cce24d8fb4d6ff4e6d','environment':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__},'selected_gamma':gamma,'csv_comparisons':comparisons,'selection_checks':summary.to_dict(orient='records')}
(root/'audit_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
