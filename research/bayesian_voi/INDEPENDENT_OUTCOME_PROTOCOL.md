# Portfolio auction-response and delayed-attribution evaluation — v7 protocol

**Date:** 19 October 2026. **Status:** exploratory internally constructed synthetic simulation, not an externally calibrated market model, real Amazon Ads evidence, or an independent review. The outcome simulator is intentionally structurally different from the v5 VOI decision equation; it is *not* an independently obtained dataset. No hypothesis was preregistered.

## Question and hypotheses

Does the **unchanged v5 Bayesian value-of-information (VOI) ranking** select sponsored-search terms for ten-click evidence collection more profitably than simpler allocation rankings when an *independently specified synthetic outcome process* includes auction-price variation, bid-dependent volume, variable realised margins, delayed observed conversions, a finite campaign budget and a MAINTAIN action?

Null expectations are not presupposed to be false; the evidence-aware policy may lose. This is a **stress test of transfer** from a simplified theoretical decision objective, not a demonstration of algorithmic novelty.

## Freeze and information control

- The v5 ranking is imported as-is from `fair_baselines.voi_increment` and uses only historical clicks/orders, CPC, AOV and the fixed v5-training-selected prior Beta(2,18).
- No v7 outcome is used for feature selection, prior training, thresholds or ranking calibration. The v7 test seed range **23000–23039** is separate from the v5 training seeds 6000–6019 and test seeds 12000–12029.
- Competing allocation ranks: (1) reproducible random; (2) fewest historical clicks; (3) posterior probability of profitability nearest 0.5; (4) v5 VOI ranking.
- Common exact term-selection quotas **5%, 10% (primary), and 20%**; each allocates 10 exploratory clicks per chosen term. Shared exploratory overhead is **2 fictional units per selected term**, separate from ad-spend budgets. The fixed quotas may compel an economically harmful exploration choice. There are also *separately labelled unmatched* controls with no exploration and with v5 model-positive-VOI-only exploration.
- All allocation rankings use only the same observable historical columns. Unknown true CVR, true margins, future auction competition, future demand and future conversion draws are only visible to the simulator during outcome assessment. No future observations are used to rank terms initially.

## Independent synthetic outcome generator

Each seed yields **180 search terms across 6 campaigns (30 terms each)**. Historical CVRs originate from a four-segment Beta mixture rather than the v5 uniform-CVR cohort, and true margins range from **14% to 39%** (decision logic assumes 25%). Historical clicks span 5–160, historical CPC 0.35–1.55, AOV 18–78, base future demand from a Poisson draw, and cost perturbation via a lognormal auction shock. These numbers are illustrative only and not claimed to represent actual marketplace distributions.

A common **three-action follow-up policy** applies to every ranking: SCALE if posterior expected contribution per click exceeds 18% of reported CPC; MAINTAIN if it is at least −25% of reported CPC; NEGATIVE otherwise. These thresholds were set as a transparent heuristic and are not learned or commercially validated. SCALE increases prospective clicks by a factor of 1.40 and CPC by 1.16, while reducing prospective CVR by the scenario-specific quality factor (0.85 or 0.90). MAINTAIN uses baseline traffic and CPC and NEGATIVE buys no further clicks. The shared posterior updates after exploration can change final actions and campaign priority.

Each selected term explores first at base auction-adjusted CPC; realised purchases are generated from fixed term-specific random uniforms and added to **economic outcomes**, but only a stated share is immediately **visible** to the decision-maker. Then terms are served in each campaign by common estimated-profit priority; clicks stop at a **strict campaign budget**. Baseline cap: **440 fictional ad-spend units per campaign**; budget-stress cap is half. Overhead is charged to outcome profit but outside ad spend. Profit includes **all matured realised conversions** and subtracts spent ad budget and exploration overhead. Reporting-delay tests only censor information at decision time, not final realised revenue.

## Six predefined scenarios

1. Mixture reference: unchanged future CVR, baseline auction costs, 100% reported conversions, budget 440 per campaign, SCALE quality 0.90.
2. Auction costs +35%: auction costs multiplied by 1.35, SCALE quality 0.85.
3. Conversions 50% visible: half of historical/follow-up orders observed before the decision, with eventual outcomes scored in full.
4. Campaign budgets halved: spending cap 220 per campaign.
5. Future CVR −40%: future conversion probabilities are 60% of their historical levels.
6. Combined adverse: future CVR −40%, costs +35%, 50% visible orders, budget cap 264, SCALE quality 0.85.

Scenarios are sensitivity constructions, not statistically independent populations; each scenario uses the same 40 seed IDs and scenario-specific transformations.

## Metrics, inference and verification

Primary endpoint is **mean realised synthetic net contribution per term** (higher is better) across 40 paired test cohorts. Secondary measures: ad spend per term, cap utilisation, observed deferral fraction, exploration fulfilment and percentage of MAINTAIN decisions. Paired differences are v5 VOI **minus** the uncertainty rank; a *negative* difference means lower VOI profit. Descriptive 95% half-widths equal `1.96 × sd(paired difference across 40 seeds) / √40`. The half-widths do not correct for multiple comparisons, simulator-design uncertainty, non-normal cohorts or post hoc research selection. They cannot establish real-world significance.

Automated tests verify reproducible cohorts, seed separation, latent-outcome masking in ranks, exact nominal deferral quotas, action coverage, budget-cap enforcement, incomplete attribution and result pairing. Reproduction requires `numpy`, `pandas`, `scipy` and the v5 `fair_baselines.py`, `misspecification_experiment.py`, `adaptive_policy.py`. These v5 files already exist in the approved research branch.

```bash
cd research/bayesian_voi
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python independent_outcomes.py
```

## Limits and potential failure mechanisms

- Auction-price/click-volume mechanics and budgets are **stylised and uncalibrated**: no real Amazon auction, relevance auction, placements, query matching, campaign-level feedback or intertemporal pacing.
- A simulator designed by this research team cannot be called independent external validation. The target is independent **from the v5 policy's utility formula**, not independent of researchers' modelling judgments.
- The unchanged v5 VOI formula assumes a **binary SCALE/NEGATIVE action set**, whereas the v7 evaluation adds MAINTAIN and budget competition. This mismatch is deliberate and can disadvantage v5 VOI; a retrained multi-action and budget-aware VOI policy remains future work.
- Selection quotas are exact but ad spend differs across policies; ranking differences may also change campaign priority, budget saturation and selected traffic, which is part of this portfolio stress test rather than a controlled single-term effect.
- Exploratory click opportunities are guaranteed (100% probe completion in sampled main comparisons), even though real auctions cannot guarantee exactly 10 new clicks promptly.
- No multiple-hypothesis correction, empirical calibration, uncertainty around simulator assumptions, actual seller utility testing, causal field experiment or external methodological certification.
- The old v5 and new v7 outcomes measure **different economic constructs** (v5: synthetic regret against a stylised oracle; v7: matured realised portfolio contribution). Their absolute numbers should never be compared directly.
- No confidential customer, employer or seller data were used; the work remains an experimental framework, not verified production bid advice.

