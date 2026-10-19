# v8 budget-aware synthetic experiment (review copy)

This is **experimental research**, not a live Amazon Ads tool. No business/private advertising data is included. The existing Streamlit dashboard and GitHub `main` are unchanged.

- `V8_PROTOCOL.md`: primary protocol fixed before seeing v8 hold-out outcomes
- `v8_budget_aware.py`: three-action budget-aware decision policy, simulated evidence-allocation score, train-only gamma choice and matched-seed evaluation
- `v8_posthoc_diagnostics.py`: explicitly post-hoc simple-profit and pure-information negative controls, written after initial results were observed
- `V8_RESULTS.md`: full interpretation with unflattering findings and source data references
- `results/v8_*.csv`, `results/v8_config.json`: reproducible synthetic cohort/seed comparisons
- `tests/test_v8_budget_aware.py`: input, leakage, budget and reproducibility checks

**Most important result:** At fixed 10% information-collection quota, the new v8 ranking makes exactly the same selection as a simple estimated-contribution-per-click rule in all 180 held-out cohorts. Therefore its apparent gain over prior weak baselines is **not evidence of a new Bayesian information-acquisition benefit**. A separate v8 action-rule improvement occurs under five of six internally generated scenarios, but it **fails under delayed attribution**. Both points must accompany any sharing of this package.

Do not deploy these policies to change bids, keywords or budgets in a real Amazon account.
