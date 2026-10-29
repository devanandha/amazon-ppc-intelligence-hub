# v7 synthetic independent-outcome stress test — results

**19 October 2026 · internal synthetic model, not Amazon Ads performance or external peer review.**

## Held-out 10% exploration quota

Synthetic matured net contribution per term (higher is better). All rankings choose 18 of 180 terms in each cohort; 40 seed replicates. Reported differences are paired VOI minus profitability-uncertainty with descriptive 95% half-widths.

| Scenario | Profitability-uncertainty profit | v5 VOI profit | VOI − uncertainty ± 95% half-width |
|---|---:|---:|---:|
| Mixture reference | 13.2922 | 13.0541 | -0.2381 ± 0.1517 |
| Auction costs +35% | 7.2005 | 7.0081 | -0.1924 ± 0.1185 |
| Conversions 50% visible | 13.6533 | 13.3846 | -0.2687 ± 0.2338 |
| Campaign budgets halved | 10.2250 | 9.9506 | -0.2744 ± 0.1478 |
| Future CVR -40% | 1.8963 | 1.7949 | -0.1014 ± 0.0897 |
| Combined adverse | 0.0745 | -0.2087 | -0.2833 ± 0.1236 |

**Finding:** The unchanged v5 VOI ranking has *lower synthetic realised contribution* than the profitability-uncertainty ranking in **all six 10%-quota scenarios**. At least one reason may be that the v5 VOI equation does not represent a three-action, budget-constrained auction environment. This result limits, rather than invalidates, previous in-model evidence and does not prove the uncertainty rank is commercially superior.

## Sensitivity to exploration quota (paired difference)

Positive would favour VOI; negative favours the simpler uncertainty rank. Descriptive between-seed 95% half-width, without multiplicity correction.

| Scenario | 5% quota | 10% quota | 20% quota |
|---|---:|---:|---:|
| Mixture reference | -0.1292 ± 0.1172 | -0.2381 ± 0.1517 | -0.0215 ± 0.1263 |
| Auction costs +35% | -0.1549 ± 0.1242 | -0.1924 ± 0.1185 | -0.0337 ± 0.1009 |
| Conversions 50% visible | -0.1197 ± 0.1927 | -0.2687 ± 0.2338 | -0.2020 ± 0.1178 |
| Campaign budgets halved | -0.1259 ± 0.1318 | -0.2744 ± 0.1478 | -0.1159 ± 0.1300 |
| Future CVR -40% | -0.0597 ± 0.0876 | -0.1014 ± 0.0897 | -0.0130 ± 0.0737 |
| Combined adverse | -0.1314 ± 0.1064 | -0.2833 ± 0.1236 | -0.1113 ± 0.1115 |

## Unmatched zero-exploration comparison (separate question)

This comparison does **not** control deferral counts; it indicates whether a policy that chooses to gather evidence actually beats choosing not to gather evidence under the stylised portfolio assumptions.

| Scenario | No exploration profit | Model-positive VOI gate profit | Positive-gate deferral rate |
|---|---:|---:|---:|
| Mixture reference | 13.3846 | 13.2349 | 7.10% |
| Auction costs +35% | 7.3900 | 7.1248 | 7.10% |
| Conversions 50% visible | 13.3081 | 13.3471 | 7.64% |
| Campaign budgets halved | 10.9159 | 10.2760 | 7.10% |
| Future CVR -40% | 2.0502 | 1.9021 | 7.10% |
| Combined adverse | 0.2343 | -0.0880 | 7.64% |

In five of six scenarios, the positive-model VOI gate earned lower mean profit than **no exploration**; the incomplete-attribution scenario showed a small opposite point-estimate difference, without a paired interval calculated here. This is a *diagnostic*, not a matched-rate test.

## Quality checks

- **57 automated tests passing**: 38 existing v4/v5 checks plus 19 new simulator and experimental-invariant tests.
- **All six scenarios, 40 independent test seeds, three fixed quotas** evaluated without re-fitting the v5 prior or changing its VOI scoring equation.
- **Exact 5/10/20% term-selection quotas**, with 100% completion of selected 10-click probes across reported fixed-quota runs; campaign spend stays within scenario caps.
- **MAINTAIN** was chosen for roughly 17–21% of terms in the reported policy/scenario comparisons; SCALE and NEGATIVE cover the rest.
- **Paired potential outcomes** are based on fixed per-term random streams. No latent CVR, true margins or future auction shocks are passed into initial rankings.

## What not to claim

Do not state that VOI improves PPC commercial profitability, that the uncertainty method is superior in real auctions, or that this simulation establishes scientific novelty. The outcome model is internally developed and not independently calibrated. The falsification is conditional on our specific stylised environment.

## Recommended next research

1. Develop a budget-aware, three-action VOI policy *without touching the v7 holdout results*; compare it on a predeclared **new** seed set against matched-budget rules and the existing frozen version.
2. Perform parameter sensitivity across auction-price response, volume response, conversion-quality dilution and exploration opportunity scarcity; document parameter-range failures.
3. Obtain legitimate independent seller usability feedback without requesting confidential campaign exports, and seek external methodological critique of the model and novelty.

Reproduce: `python independent_outcomes.py`. See `INDEPENDENT_OUTCOME_PROTOCOL.md` and `results/independent_*.csv` for the design and individual synthetic seed outputs.

