# Information use intervention results

29 October 2026. All outcomes are synthetic. This extends v8 without changing its simulator or tuning another algorithm.

## Frozen evaluation

The local protocol was written and hashed before the new outcome run. Implementation hashes were recorded after 79 validation tests passed and before generating seeds 52000–52029. Six existing scenarios and three quotas were retained. Seven allocation rankers were evaluated under the same v8 action rule at gamma=0. Each use/withhold pair purchased identical probes with identical cashflows, overhead and campaign budget depletion. Only the information available for subsequent action and priority changed. A no-probe comparator was evaluated separately.

The full grid completed 7,740 policy evaluations and 3,780 matched information-use contrasts, on 180 scenario/seed cohorts. These are not thousands of independent datasets.

## Primary 10 percent quota

Combined ranker use-minus-withhold mean contribution differences per term, with descriptive 95% half-widths:

| Scenario | Information-use effect | Use minus no probe | Withhold minus no probe |
|---|---:|---:|---:|
| Reference | 0.000 ± 0.000 | 1.998 ± 0.279 | 1.998 ± 0.279 |
| Auction costs +35% | −0.011 ± 0.016 | 1.685 ± 0.295 | 1.696 ± 0.292 |
| Conversions 50% visible | 0.000 ± 0.000 | 1.777 ± 0.236 | 1.777 ± 0.236 |
| Campaign budgets halved | 0.015 ± 0.070 | 1.367 ± 0.342 | 1.353 ± 0.316 |
| Future conversion probability −40% | 0.000 ± 0.000 | 1.009 ± 0.196 | 1.009 ± 0.196 |
| Combined adverse | 0.056 ± 0.094 | 0.556 ± 0.218 | 0.501 ± 0.212 |

Zeros are numerical zeros rounded for display, not statements about all possible outcomes. Units are fictional contribution per term. The six information-use intervals include zero; this is not proof of absent effects. The twelve mean net-probing comparisons are positive with descriptive intervals excluding zero, including when observations are withheld. No multiplicity adjustment was applied.

No term changes its follow-up action between paired use/withhold arms in any of the 180 combined-ranker primary-quota cohorts. Priority values change for approximately 10% of terms. Small nonzero contribution effects can occur through traffic reprioritisation with shared budgets. The result is conditional on this selection, action policy and simulator.

The combined score and simple unit-profit ranker choose identical sets in 180/180 new cohorts at 5%, 179/180 at 10%, and 136/180 at 20%. Thus the original 180/180 primary-quota equivalence was sample-specific, not a universal identity. Other rankers show mixed information effects, including positive and negative values; all methods, quotas and per-seed outcomes are retained in `information_results/`.

## Interpretation

The new experiment does not rescue a claim of superior information targeting. It strengthens the narrower computational diagnosis: profitable probing can improve the total economic endpoint even when the policy cannot use its observations later. It does not establish that information is generally useless, prove real-world profit lift, or supply external validation. This is a possible negative-results computational study; acceptance and methodological novelty remain uncertain.

## Integrity checks

- Existing suite plus eight intervention checks: 79 tests passed.
- Use-arm parity with the prior v8 simulator verified on smoke seeds across all six scenarios.
- Matching probe cashflows, probe spending by campaign, completion and depletion checked for every paired evaluation.
- Total equals probe plus downstream contribution checked for every use/withhold evaluation.
- Budget caps enforced throughout; historical counts used for both withheld decisions and priorities.
- Protocol and implementation hashes unchanged since their pre-evaluation local freeze records.

## Files

`INFORMATION_USE_PROTOCOL.md`, `information_protocol_freeze.json`, `information_implementation_freeze.json`, `information_use.py`, `tests/test_information_use.py`, `information_validation.log`, `information_run.log`, and `information_results/{config.json,per_seed.csv,paired.csv,selection.csv,summary.csv,contrasts.csv}`.

No journal submission was made as part of running the experiment. The manuscript and supplementary package have been updated to describe the extension while retaining the original post-hoc chronology.
