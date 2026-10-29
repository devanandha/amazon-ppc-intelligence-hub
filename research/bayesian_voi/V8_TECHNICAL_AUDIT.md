# v8 technical integrity notes

**Environment:** Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3 (captured local environment, not exact requirements pinning).

The v7 `independent_outcomes.make_cohort` generates all v8 outcomes using a separate latent process. v8's `run_policy_v8` duplicates the v7 portfolio accounting but **replaces only** the three-action selection function with `budget_action`; the simulation's auction/conversion/budget mechanics were not altered.

## Isolation and fairness

- Candidate score inputs: historical clicks, observed orders, nominal CPC, AOV, campaign and known cap multiplier. No unknown true margin, CVR, realised auction shock or potential outcomes are used in ranking.
- Gamma selected before any 42000–42029 test-seed scores or outcomes were generated. Training included 12 independently seeded cohorts per each of three known simulation settings, and tuned **only gamma for the new proposed method**, a potential baseline-comparison asymmetry.
- Hold-out comparison pairs every method on exactly the same term cohort, fixed quota, shared action rule and identical simulated potential outcomes; separate ablation compares decision rules under the same selection.
- Tests verify input guards, hidden-data invariance, budget caps, 3-class action consistency, deterministic replay, disjoint seeds and full legacy verification.

## Limitations and audit warning

The original primary protocol compared v8 to random, fewest clicks, uncertainty and v5 VOI. A simple estimated-profit rule was missing. We constructed it **only after** looking at favourable first results. It matches the v8 ranking at 5% and 10% quotas in 100% of cohort comparisons, invalidating any interpretation that superior performance comes from informational novelty. This is a substantive specification failure, not a detail to obscure.

Even the new budget-aware action heuristic has no rigorous real-world calibration and is less successful when conversion reporting is incomplete. This validation is research-level simulation and does not support production deployment or UK Global Talent endorsement on its own.

