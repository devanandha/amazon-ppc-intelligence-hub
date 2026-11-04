# Exploratory machine-learning review — technical methodology

**Project owner:** Devanandha Vellaramkuzhiyil Shaji (Devanandha VS)  
**Application:** Amazon PPC Intelligence Hub  
**Status:** Development prototype; technical validation and independent evaluation pending.

## What the model does

The `AI Review` tab analyses **aggregated** Amazon Sponsored Products customer search terms from the currently loaded report. It uses scikit-learn's **Isolation Forest**, an unsupervised anomaly-detection model, to identify combinations of metrics that are unusual *relative to other terms in that same report*.

The model is exploratory and **not** trained to predict ROAS, profit, bid performance, fraud, click quality, or advertising uplift. The score is not a probability and a flag is not a recommendation to pause an ad.

The underlying existing PPC recommendations remain transparent threshold rules, with independent anomaly signals shown next to those actions. A hybrid review note draws an analyst's attention to unusual data that might warrant checking before following a favourable rule-based recommendation.

## Inputs and preprocessing

- Report rows are first aggregated by customer search term in the original application.
- A term is scored if it has at least the user-selected minimum click count and positive impressions.
- For the ML feature matrix we use **clicks, spend, orders, sales, CTR, orders per click, and ROAS**; volume/count and ROAS features use `log1p` transformation.
- `RobustScaler` normalises the features. `IsolationForest(n_estimators=150, contamination=0.10, random_state=42)` is fitted on those observations.
- At least **12 eligible search terms** are required; otherwise the model explicitly reports that it has not been fitted.
- Outlier flags, raw anomaly scores and descriptive differences from feature medians are displayed. These descriptive comparisons **are not formal explanations of model attributions**.

The `contamination=0.10` setting asks the model to identify approximately the most unusual 10% of eligible observations. This is a **chosen review budget**, not evidence that 10% of search terms are actually problematic.

## Conversion-rate uncertainty

The companion statistical calculation uses a **Jeffreys prior** `Beta(0.5, 0.5)` and a binomial approximation to produce **90% equal-tailed posterior credible intervals** for observed orders per click.

This is a modelling assumption, not a guarantee that Amazon's attribution counts are independent Bernoulli outcomes. If attributed orders exceed clicks, the binomial approximation is inconsistent with the data, and the interval is intentionally **withheld**. No-click terms also do not receive an interval.

Intervals should be read as uncertainty *under this model*, not as confidence that a bid change will improve performance.

## What the app deliberately does not claim

- No real-world uplift or benchmark superiority.
- No automatic bid changes, keyword exclusions or Sponsored Products account access.
- No inference that anomaly status means an advert is unprofitable.
- No calibration or external validation of anomaly scores.
- No causal prediction from Scenario Lab; that tool only reapplies existing rules under another target ACOS.
- No inference that adding ML by itself establishes novel research, an award-worthy innovation or Global Talent recognition.

## Reproducibility and evaluation

- Use the **one-click fictional demo**; it contains only generated data and a fixed random seed.
- Run `python -m unittest discover -s tests -v`.
- Inspect `tests/test_ml_insights.py` for deterministic model behaviour, interval safeguards and the under-sampled-data pathway.
- Evaluate with independent PPC practitioners and report errors and negative findings as well as potential usefulness.
- With appropriate consent, assess a separate time-based, account-level holdout and compare against simpler rules **before** claiming predictive or commercial benefits.

## Planned next step

Develop a separately validated, evidence-aware decision-gating module with held-out temporal and account data, explicit missing-evidence handling and a human-review mechanism. This is planned work, not a deployed capability.
