# Fixed-budget held-out baseline validation — findings (v5)

**19 October 2026 — newly run exploratory synthetic experiment. Not real Amazon Ads evidence, not external peer review.**

## Design and reproducibility

- 20 disjoint training seeds and 30 test seeds (1,600 terms/seed); four shared-prior candidates, five hybrid weights, 5/10/20% fixed allocation quotas, six synthetic scenarios.
- All allocation rankings use only historical counts, CPC, AOV and the common trained prior; no test latent data or future outcomes are used to rank terms.
- **38 tests passed in the combined v4+v5 local test suite** (25 previous, 13 new). This is software verification, not validation of model realism.
- Shared prior chosen on training historical-order log-likelihood: **Beta(2,18)**. Training-tuned hybrid chose **lambda = 1.0**, meaning **the hybrid is exactly the VOI ranking**: it yields **no independent gain** and must not be advertised as an additional outperforming method.
- The primary analysis imposes a 10% mandatory evidence-acquisition quota on all rankings; positive gains are not required for forced deferrals.

## Primary comparison: held-out test, matched 10% deferral

Lower mean regret is better. Paired difference is (VOI minus uncertainty) with descriptive 95% between-seed CI half-width; negative favors VOI.

| Scenario | Profitability-uncertainty regret | VOI regret | Paired difference ± half-width |
|---|---:|---:|---:|
| Stationary reference | 2.8389 | 2.7190 | -0.1199 ± 0.0424 |
| CVR decline 40% | 6.3916 | 6.6215 | +0.2299 ± 0.0254 |
| CVR increase 50% | 10.0949 | 9.2943 | -0.8007 ± 0.0952 |
| Delayed attribution 65% visible | 7.8539 | 7.5877 | -0.2662 ± 0.0425 |
| Unknown true margins 12-40% | 6.1592 | 6.0028 | -0.1563 ± 0.0456 |
| Combined adverse | 4.1824 | 4.2554 | +0.0730 ± 0.0247 |

The VOI rank has lower regret than the uncertainty comparator in four of six scenarios and **higher regret** in two (conversion decline 40% and the combined adverse scenario). Under the stationary reference environment: VOI 2.7190; uncertainty 2.8389; fewest clicks 3.1085; random 3.3030. Under conversion decline, uncertainty 6.3916 beats VOI 6.6215. All numbers are fictional model units per term, not advertiser revenue, profit or return on spend.

The training-selected hybrid collapses to VOI (lambda 1.0). Therefore there is **no independent fifth-method improvement**; the fifth tested line is a training diagnostic, not a separate win.

## Sensitivity: VOI vs profitability uncertainty across mandatory quotas

Each row is a paired synthetic regret difference; positive values favor the simpler uncertainty ranking.

| Fixed quota | Scenario | VOI minus uncertainty ± half-width |
|---|---|---:|
| 5% | Stationary reference | -0.1470 ± 0.0605 |
| 5% | CVR decline 40% | +0.4022 ± 0.0401 |
| 5% | CVR increase 50% | -0.9046 ± 0.1154 |
| 5% | Delayed attribution 65% visible | -0.4439 ± 0.0724 |
| 5% | Unknown true margins 12-40% | -0.2133 ± 0.0805 |
| 5% | Combined adverse | +0.0867 ± 0.0452 |
| 10% | Stationary reference | -0.1199 ± 0.0424 |
| 10% | CVR decline 40% | +0.2299 ± 0.0254 |
| 10% | CVR increase 50% | -0.8007 ± 0.0952 |
| 10% | Delayed attribution 65% visible | -0.2662 ± 0.0425 |
| 10% | Unknown true margins 12-40% | -0.1563 ± 0.0456 |
| 10% | Combined adverse | +0.0730 ± 0.0247 |
| 20% | Stationary reference | +0.0035 ± 0.0179 |
| 20% | CVR decline 40% | -0.0719 ± 0.0114 |
| 20% | CVR increase 50% | +0.2416 ± 0.0509 |
| 20% | Delayed attribution 65% visible | +0.0817 ± 0.0203 |
| 20% | Unknown true margins 12-40% | +0.0318 ± 0.0275 |
| 20% | Combined adverse | -0.0129 ± 0.0096 |

**Important failure modes:** At the 5% and 10% quotas, the uncertainty rule beats VOI when CVR declines 40% or combined adverse assumptions apply. At 20% quota, the uncertainty rule beats VOI for increasing CVR, delayed attribution and margin variation, and the stationary difference is negligible. Budget dependence means choosing one quota for a single headline would be misleading.

## Unconstrained VOI diagnostic — not comparable at fixed deferral rate

| Scenario | Immediate Bayesian regret (0% defer) | VOI policy regret | VOI deferral rate |
|---|---:|---:|---:|
| Stationary reference | 2.8310 | 2.6838 | 4.76% |
| CVR decline 40% | 7.0559 | 6.7433 | 4.76% |
| CVR increase 50% | 10.6811 | 9.9044 | 4.76% |
| Delayed attribution 65% visible | 7.6000 | 7.5431 | 4.64% |
| Unknown true margins 12-40% | 6.1207 | 5.9604 | 4.76% |
| Combined adverse | 4.3704 | 4.2107 | 4.64% |

This diagnostic asks a different question: instead of forcing 10% collection, would a model-based VOI gate ever defer when predicted gain is not positive? The model chooses approximately 4.6–4.8% deferral. Lower regret versus no deferral under these matching simulation assumptions is **not** evidence of real-world gain, robust generalisation, or independent novelty.

## Interpretation for independent reviewers

This study resolves a clear issue in v4: unequal deferral rates between rules. The *allocation rank* comparison now enforces matched counts, uses disjoint training/test seeds, and tests scenarios in which the algorithm fails. It does **not** fix the deeper issue that evaluation and VOI scoring share a simplified economic model. Prior tuning on the training sample and the held-out test split constrain overfitting to test random draws, not structural model assumptions.

No production software changed; no Denman/advertiser confidential data used. No claim is made about demonstrated real-seller lift, scientific novelty, or UK Global Talent criterion satisfaction. See `FAIR_BASELINE_PROTOCOL.md` for full design and limitations, and `results/fair_*.csv` for all seed-level and aggregated values.
