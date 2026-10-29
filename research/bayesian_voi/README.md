# Sponsored-search evidence collection: reproducibility materials

**Manuscript:** Separating Profitability from Information Value in Sponsored Search Evidence Collection  
**Author:** Devanandha Vellaramkuzhiyil Shaji  
**Status as of 29 October 2026:** Submitted to *Operations Research Forum*; at technical check. Not accepted or confirmed as externally peer reviewed.

This directory provides synthetic experiments associated with the submitted computational study. It is separate from the production dashboard. The full manuscript and private submission correspondence are not included.

## Main findings

- A simple expected-contribution ranker selected the same terms as the combined Bayesian score in all 180 original cohorts at the primary 10% quota.
- In the new information-use intervention, use and withhold arms share the same probes, costs, returns and depleted budgets. All six primary combined-ranker information-use intervals include zero.
- Probing can improve total contribution even when the observations are withheld from later decisions; a profitable probe does not by itself establish a learning benefit.
- The combined and simple profitability rankings select identical sets in 179 of 180 fresh primary-quota cohorts.
- An action-rule comparison improves contribution in five scenarios but fails under incomplete conversion reporting.

All data are internally synthetic. These findings do not establish marketplace uplift, external validity or general algorithmic superiority. Intervals are descriptive and are not adjusted for multiple comparisons.

## Start here

- [New intervention protocol](INFORMATION_USE_PROTOCOL.md)
- [New intervention results and limitations](INFORMATION_USE_RESULTS.md)
- [Original v8 protocol](V8_PROTOCOL.md) and [results](V8_RESULTS.md)
- [Reproduction audit](audit_verification.json)
- [New per-seed and paired results](information_results/)
- [Original reproduced results](results/)
- [Numerical manuscript tables](manuscript_tables/)

Earlier protocols and result notes preserve the development chronology. Their environment or branch-status descriptions refer to those earlier runs, not this publication update. The original profitability controls were post hoc. The new local protocol and implementation were hashed before fresh-seed evaluation; this is not external preregistration.

## Reproduce

Tested on Python 3.12.14 with the versions in `requirements-tested.txt`:

```bash
cd research/bayesian_voi
python -m pip install -r requirements-tested.txt
python -m unittest discover -s tests -v
python v8_budget_aware.py
python v8_posthoc_diagnostics.py
python information_use.py
python audit_reproduction.py
python manuscript_tables.py
```

The test suite contains 79 passing tests, including eight information-use checks. Tests verify computational properties, not scientific novelty or real-world effectiveness. Full experiments overwrite their generated CSV outputs. Keep an archived copy if comparing with the supplied results.

The fresh extension uses seeds 52000–52029, six scenarios, seven rankers and three quotas: 7,740 policy evaluations and 3,780 paired contrasts arise from 180 scenario–seed cohorts, not thousands of independent datasets.

The original frozen research source was commit `6e55061294278bd0adcb37cce24d8fb4d6ff4e6d`. The archived original primary per-seed file was unavailable for direct comparison; a newly regenerated primary per-seed file is supplied, and the audit records that limitation.
