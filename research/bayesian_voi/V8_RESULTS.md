# v8 synthetic research — results and research-integrity assessment

**19 October 2026. Exploratory simulation, NOT Amazon Ads evidence or independent peer review.** The experiment and its baseline comparisons are governed by `V8_PROTOCOL.md`, drafted before v8 test outcomes were examined. Additional negative controls were constructed **after** primary results were inspected and therefore labelled post-hoc.

## Setup

12 training seeds (32,000–32,011) restricted to three training scenario definitions and 30 new held-out seeds (42,000–42,029) in six previously defined synthetic scenarios; 180 terms and six 30-term campaigns per seed. Total held-out portfolios: 180 distinct scenario/seed cohorts, assessed at quotas 5%, 10%, 20%, and under the two common follow-up action rules. The same test seed used in different scenario families is not an independent external dataset.

Every method uses the same exact collection quota (primary 10%). All ranking methods have access to historical clicks, reported orders, CPC, AOV and no hidden future outcomes. The v8 score also uses known campaign budget, as does the v8 shared action rule. No Denman data or other employer/advertiser data is used.

### Parameter selection

The training-only search selected **gamma = 0.0**. The candidate values were 0, 0.20 and 0.50. Therefore the proposed additional budget-shadow-cost penalty **did not improve the training objective** in this experiment. The budget-aware action valuation still uses budget shares, but claiming that the fitted shadow-cost mechanism improved outcomes would be false.

## Primary results at 10% quota

Higher profit is better. Fictional contribution per term; not real advertising revenue. Values in the two rightmost columns are paired mean differences with descriptive 95% half-width across 30 test seeds; they are NOT multiple-comparison-adjusted confidence intervals.

| Simulation condition | Uncertainty rank + v8 action | v8 rank + v8 action | v8 rank − uncertainty (same action) | v8 action − v7 action (same v8 ranking) |
|---|---:|---:|---:|---:|
| Mixture reference | 13.664 | 15.546 | +1.882 ± 0.263 | +1.324 ± 0.507 |
| Auction costs +35% | 9.301 | 11.114 | +1.813 ± 0.269 | +2.838 ± 0.426 |
| Conversions 50% visible | 12.156 | 13.468 | +1.311 ± 0.433 | -1.196 ± 0.417 |
| Campaign budgets halved | 11.294 | 13.073 | +1.779 ± 0.248 | +1.613 ± 0.426 |
| Future CVR -40% | 3.196 | 4.110 | +0.914 ± 0.237 | +1.512 ± 0.325 |
| Combined adverse | 1.908 | 2.361 | +0.453 ± 0.238 | +1.563 ± 0.321 |

The comparison inside the v7 action stratum was also positive for v8 rank against the old uncertainty baseline in all six scenarios; full values are in `results/v8_paired.csv`.

## CRITICAL post-hoc negative control: the apparent VOI allocation gain disappears

After observing the primary results, we tested a **very simple control**: rank by historical posterior expected contribution per click, `posterior_mean_CVR × assumed_margin × AOV − CPC`, rather than by VOI. **It chose EXACTLY the same terms as the proposed v8 score in every one of the 180 held-out scenario/seed cohorts at BOTH the 5% and 10% quotas.** At 20%, it chose precisely the same set in 142 of 180 cohorts (approximately 99.65% mean per-term selection agreement).

Consequently, the apparent outperformance of v8 over the old uncertainty/VOI ranks **does not establish added value from Bayesian information acquisition**. At the primary quota, the outcome is indistinguishable from a profitability-first heuristic. The proposed v8 evidence-selection score is **not established as a new or better information strategy**. Its core model uses established beta-binomial posterior predictive and decision theory; no claim of algorithmic novelty is warranted.

Two further post-hoc controls ranked by profitability per CPC and estimated historical CVR. The pure modelled-information component alone was substantially worse than the full v8 rank in all six scenarios under the new action rule. Because these were devised after test inspection, they are not a confirmatory hold-out. Exact outcomes and paired differences are in `results/v8_posthoc_*.csv`.

## Separate action-rule result

Holding the v8 allocation selection fixed, the budget-aware three-action action rule beats the earlier v7 heuristic in **five** of six simulation environments but performs **worse when only 50% of conversions are visible**. The delayed-reporting loss is material and cannot be omitted. The v8 action rule itself is a stylised posterior-value choice, not a verified optimal policy. Its equal-budget-share heuristic omits actual sequential real-auction pacing and uses assumed rates.

## Threats to validity

- Model remains internally synthetic; no seller data, causal bid interventions, Amazon Ads auction calibration or real sales-lift validation.
- v7 outcome mechanics were fixed, but still share broad commercial assumptions with scoring (posterior CVR, common assumed costs and values).
- Post-hoc additional controls used the SAME test seeds after results were seen, so cannot establish independent replication.
- The case where incomplete conversion reporting harms the v8 action calls for explicit reporting-delay modelling and sensitivity, not claims of robustness.
- Forced quotas may favor choosing profitable terms for *short-term exploration revenue*, not gathering useful information. The exact-match control exposes this confounding.
- The gamma tuner maximised synthetic training profits using access to latent outcomes. No comparable real-world supervised calibration was performed for this project.
- Normal-approximation uncertainty intervals assume test-seed independence within a scenario and do not correct for multiple comparisons or simulator-selection uncertainty.
- No observed novelty, tested external utility or external recognition is established for UK Global Talent endorsement.

## Recommended direction — before any more algorithm development

1. Freeze this v8 package with its negative controls; request independent technical critique focused on whether exploration is actually valuable after controlling for predicted profitability.
2. Separate **economic ranking** from **information acquisition** by evaluating incremental decision improvement over profit-first, random and uncertainty allocations under equal budgets and action rules; use *genuinely untouched* new test seeds or independent outcome mechanisms.
3. Test explicit delayed-attribution models and budget safety constraints and measure welfare under alternative scale/maintain definitions, ideally with authorised, consented third-party validation.
4. Do not publish any performance/novelty or Global Talent recognition claims based on synthetic metrics alone.

## Reproduce

From a copy of the v7 research branch with the proposed v8 files added:

```bash
cd research/bayesian_voi
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python v8_budget_aware.py
python v8_posthoc_diagnostics.py
```

The locally packaged combined v4/v5/v7/v8 suite passed **71 tests**, including 14 added v8 unit tests. The scripts write seed-level CSVs and JSON config to `results/`.
