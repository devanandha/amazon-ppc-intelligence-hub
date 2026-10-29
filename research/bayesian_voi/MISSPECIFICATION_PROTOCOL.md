# Model-Misspecification Diagnostic — Protocol

Date: 17 October 2026. This protocol records an **exploratory follow-up experiment**; it was not externally preregistered and does not imply peer review. The scenario definitions below are frozen before running `misspecification_experiment.py` for the reported package. Retain this file with results.

## Goal

Test whether the one-step Bayesian evidence-collection (value-of-information; VOI) policy remains useful when the environment departs from its own assumptions. The target is *limitations and failure discovery*, not maximising a favourable headline result.

## Policies and controls

Same policies as `matched_comparison.py`: immediate Bayesian action, Bayesian fixed 15-click and 25-click gates, a 95% posterior-confidence gate, and one-step Bayesian VOI. All five operate with the same information, available initial actions (SCALE, NEGATIVE, COLLECT_DATA), 100-click prospective opportunity horizon, 10-click information acquisition, 25% **assumed** contribution margin, Beta(1,9) prior and subsequent posterior-mean action after deferral. The 10 exploratory clicks carry true revenue/cost; any explicit exploration overhead is charged on top. Each policy receives *exactly the same underlying sample* per scenario and seed, including its future conversions.

## Scenarios — declared before running

- `Stationary reference`: current and future CVR equal; 100% order reporting; true margin 25%.
- `CVR decline 40%`: future CVR is 60% of historical conversion probability; order reporting complete; true margin 25%.
- `CVR increase 50%`: future CVR is 150% of historical conversion probability, capped at 0.99; reporting complete; true margin 25%.
- `Delayed attribution 65% visible`: only 65% of actual attributed orders are shown in historical and prospective evidence; underlying profit includes all true conversions; true margin 25%.
- `Unknown true margins 12-40%`: the policy assumes 25% margin, while each term's true margin is sampled independently from Uniform(0.12,0.40).
- `Combined adverse`: future CVR declines 40%, only 65% of order conversions are visible, and each term's true margin is drawn from Uniform(0.12,0.40).

The data-generating historical CVR is Uniform(0.005,0.20), CPC Uniform(0.30,1.50), AOV Uniform(20,50), historical clicks discrete Uniform{5,...,200}. Historical order counts are binomial conditional on clicks and historical CVR. Future conversions are binomial conditional on 10 exploratory clicks and *future* CVR; unobserved conversions are randomly censored using a binomial visibility fraction.

## Outcomes and analysis

20 matched random seeds 4000–4019, 2,500 synthetic terms each; acquisition-overhead settings 0 and 2 fictional currency units. Report per-policy mean regret and defer rate and paired (policy minus immediate Bayesian) regret differences with across-seed normal-approximation 95% confidence intervals. Report and discuss scenarios where VOI does not improve, or loses to simple heuristic gates. No threshold selection or post-hoc tuning is performed using evaluation data.

The omniscient reference utility is the best of (a) fully scaled future exposure, (b) full baseline exposure or (c) no exposure, evaluated at *future* true conversion probability and true margin. This is a simplified upper-bound oracle under stationary future economics, not an implementable advertiser strategy. It ignores market auctions, budgets, attribution spillovers, inventory, longitudinal learning and the ability to choose other actions.

## Interpretive boundaries

A positive result in a synthetic environment does not demonstrate a novel algorithm, real advertiser uplift, practical Amazon Ads suitability, or a Tech Nation qualifying criterion. The policy deliberately shares the same simplified utility model used to compute its decisions; that may confer an advantage in the stationary setting. Any economic model, prior distribution, reporting assumptions, and censoring model here are researcher-defined. Real-data tests require separate written permission and prospective safeguards. Report negative results as prominently as positive ones.

