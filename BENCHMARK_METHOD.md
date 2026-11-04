# PPC Intelligence Hub v3 — Campaign Benchmark Protocol

## Scope

This benchmark is **campaign-week level** for Amazon Sponsored Products-shaped data.
It is separate from the original **search-term** harvesting and negative-keyword
engine because the public ppc_weekly_2025.csv contains no customer search terms.
It must not be used to validate keyword recommendations.

The public example, sourced from
[priscilajrey/amazon-ppc-analysis](https://github.com/priscilajrey/amazon-ppc-analysis/blob/main/data/ppc_weekly_2025.csv),
is described as **simulated** weekly advertising data. It is not live account
activity. Check the source licence before copying or redistributing the dataset.
**Do not commit raw client/employer reports or benchmark outputs to GitHub.**

## Reproduce

1. Obtain a licensed/authorised weekly campaign CSV separately. Expected fields:
   Week, Campaign, Campaign_Type, Product, Impressions, Clicks, Spend, Orders, Sales.
2. Install requirements: python -m pip install -r requirements.txt.
3. Run from repository root:

   python benchmark_campaigns.py --input /path/to/ppc_weekly_2025.csv --output benchmark_output/ --target-acos 25 --min-clicks 15 --min-orders 3

4. Inspect locally generated summary.json, observation_comparison.csv,
   ml_sensitivity.csv and EVALUATION_NOTES.txt.
5. Alternatively open the **Weekly Campaign CSV → Benchmark & Evaluation** tab
   in the development Streamlit app and download the evidence ZIP.

## Frozen comparison

- **Transparent baseline**: weekly human-review screening based on minimum clicks,
  attributed orders and observed ACOS relative to the chosen target.
  High-priority cases are (a) spend without attributed sales and sufficient clicks
  and (b) ACOS greater than 150% of the target.
  Near-target and above-target weeks may be *monitored* without qualifying as
  high-priority review. This is **not** a previously validated expert policy.
- **Unsupervised model**: IsolationForest with 150 estimators; five numeric
  features (Impressions, Clicks, Spend, Orders, Sales), log1p, then
  RobustScaler; contamination 0.10; primary random seed 42.
- **Review-coverage comparison**: both flagged, rule only, ML only, neither.
- **Seed stability**: compare primary flags with seeds 43–46 by Jaccard similarity
  on the *same dataset*. This is not cross-account generalisation.
- **Alert-budget sensitivity**: rerun contamination settings of 0.05, 0.10,
  and 0.15. Flag counts are influenced by this parameter.
- **Minimum sample guard**: ML abstains if fewer than 20 weekly rows.

## Frozen first-run results on the public example

At ACOS target 25%, minimum clicks 15 and orders 3:

| Measure | Count |
|---|---:|
| Weekly observations | 416 |
| Campaigns | 8 |
| Unique weeks | 52 |
| High-priority baseline flags | 141 |
| ML anomaly flags (10%) | 42 |
| Both flags | 7 |
| Rules only | 134 |
| ML only | 35 |
| Neither | 240 |

Mean Jaccard similarity of ML flags across seeds 43–46 versus seed 42: **0.7783**.
At contamination 5% / 10% / 15%, anomaly counts are **21 / 42 / 63**.

## What these numbers **do not** prove

- Rules are not ground truth, so overlap cannot be called accuracy, recall or F1.
- The ML model does not predict sales, profit, next week's performance,
  bid impact, optimal actions or campaign activation.
- The dataset is synthetic and is not an independent real-world validation set.
- This is not a prospective A/B test, evidence of commercial ROI improvement,
  independent professional recognition, or a Global Talent endorsement criterion
  on its own.
- We do not know true profit margins, stock, listing eligibility, account goals,
  bid strategy or attribution completeness.

## What would improve the evidence

1. Document independent campaign-review labels on a **permission-cleared**
   sample. Sample cases from both/only/neither groups, blind the reviewer to
   model flags, record disagreements and rationales.
2. Predefine a review rubric and report review agreement / uncertainty.
3. Test generalisation on another licensed dataset (without fabricating fields).
4. Only compare outcomes in an authorised prospective experiment with appropriate
   controls. No claims of uplift until that evidence exists.
5. Keep original employer/client data confidential. External review requires
   explicit authorisation from the data owner.

The code and fictional unit-test fixtures are publishable; this repository
does not need to contain redistributed source data or confidential report rows.
