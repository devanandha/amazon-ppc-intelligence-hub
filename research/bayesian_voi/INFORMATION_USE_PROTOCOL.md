# Controlled information use experiment

Design fixed on 29 October 2026 before generating the new evaluation cohorts. This is a prospective local protocol for a synthetic extension, not external preregistration. Earlier v8 results and their failures are already known.

## Question
Within the frozen v7 outcome simulator and v8 action rule, does using new probe observations improve downstream contribution compared with buying exactly the same probes but withholding their observations from subsequent action and traffic-priority decisions?

## Frozen design
- Keep `independent_outcomes.make_cohort`, v8 budget action, PRIOR=(2,18), overhead=2, probe length=10 and selected gamma=0 unchanged. No new model or tuning.
- New evaluation seeds: 52000 through 52029, absent from the inspected earlier experiment seed definitions. Six existing scenarios, 180 terms in six campaigns each, quotas 5%, 10%, 20%; primary quota 10%.
- Rankers: random, fewest clicks, profitability uncertainty, earlier binary VOI, v8 combined score, posterior expected unit contribution, posterior expected contribution per CPC. All rankings computed from pre-probe observable inputs only. Same selected set in the use/withhold pair; stable ties; no use of true CVR or realised future data in selection.
- `use`: update clicks and reported orders with actual probe observations for BOTH follow-up action and follow-up within-campaign priority.
- `withhold`: buy identical probes and apply identical matured probe contribution, overhead and budget depletion, but calculate BOTH action and priority from pre-probe historical counts. Do not change simulator outcomes, nominal CPC, AOV or campaign budget.
- Same seed/scenario/term potential-outcome draws in each paired comparison. No averaging across scenario families as independent samples.
- Additional no-probe arm: empty selection, no overhead or probe costs, historical-information v8 action and priority. It is a separate net-exploration comparator, not the information-use effect.

## Endpoints fixed before outcomes
Primary: use minus withhold mean net contribution per term at 10%, reported per scenario and ranker. Since probe cashflows match within a pair, this equals the difference in downstream contribution under the simulated intervention. This is not a real-market causal effect.
Secondary: use minus no-probe and withhold minus no-probe; full total/probe/downstream contribution decomposition; spend, probe completion, action changes and selection-set equivalence between v8 and unit-profit. Include all six scenarios and all negative results. Quotas 5% and 20% are sensitivity comparisons.
Report seed-level differences, means and descriptive 95% normal intervals = mean +/-1.96*sd/sqrt(30), with no multiple-comparison adjustment and no simulator-uncertainty coverage. No binary acceptance threshold; conclusions stay conditional and exploratory.

## Verification before full run
Use smoke-test seeds outside the 52000 evaluation range. Verify use-arm parity with the frozen v8 implementation, exact probe cost/return/budget equality in use/withhold pairs, decomposition identity, no-probe parity, budgets, seed disjointness, deterministic replay, unchanged historical decisions when withheld and hidden-outcome invariance of selection. Preserve the protocol hash and implementation hashes before full evaluation. Do not rerun new seeds with altered assumptions to seek a favourable result.

## Interpretation and stopping
One run of this frozen grid, followed by manuscript revision. A positive learning effect need not imply that v8 selects information better than unit-profit. A negative or mixed effect remains a reportable result. No novelty, real sales lift, independent validation or acceptance claim will follow from synthetic improvement alone. New data or algorithm changes require a separate protocol. No journal submission is made by running this experiment.
