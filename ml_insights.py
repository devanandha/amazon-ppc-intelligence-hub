"""Exploratory ML-assisted review of aggregate sponsored-search observations.

This is unsupervised pattern detection, not supervised revenue prediction,
automatic bid optimisation or evidence of real-world uplift.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import beta as beta_distribution
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

TERM = "Customer Search Term"
IMPRESSIONS = "Impressions"
CLICKS = "Clicks"
SPEND = "Spend"
ORDERS = "7 Day Total Orders (#)"
SALES = "7 Day Total Sales"
MIN_MODEL_TERMS = 12

REQUIRED = (TERM, IMPRESSIONS, CLICKS, SPEND, ORDERS, SALES)


def analyse_search_terms(
    aggregated_search: pd.DataFrame,
    min_clicks: int = 5,
    min_model_terms: int = MIN_MODEL_TERMS,
) -> tuple[pd.DataFrame, dict]:
    """Rank unusual *observed* search-term patterns and show CVR uncertainty.

    For model fitting, compares log-scaled volume / sales features and observed
    efficiency rates using an unsupervised Isolation Forest on *the current
    dataset only*. Fixed random state makes the exploratory results repeatable.
    A review signal is not evidence of poor profitability or of a causal issue.

    Conversion-rate intervals are 90% equal-tailed Jeffreys posterior
    credible intervals under a binomial approximation. Attributed orders
    and clicks may not satisfy that assumption in real Ads reports.
    """
    missing = [column for column in REQUIRED if column not in aggregated_search]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    if min_clicks < 1 or min_model_terms < 3:
        raise ValueError("Minimum clicks must be positive and min_model_terms >= 3")

    result = aggregated_search[list(REQUIRED)].copy().reset_index(drop=True)
    for col in (IMPRESSIONS, CLICKS, SPEND, ORDERS, SALES):
        result[col] = pd.to_numeric(result[col], errors="coerce").fillna(0).clip(lower=0)

    # Some advertising reports count multiple attributed orders per click.
    # Never silently shrink that field: explain that the binomial assumption
    # does not hold for the affected rows, and withhold the CVR interval.
    valid_orders = result[ORDERS] <= result[CLICKS]
    eligible_uncertainty = (result[CLICKS] > 0) & valid_orders
    result["CVR 90% lower"] = np.nan
    result["CVR 90% upper"] = np.nan
    alpha = result.loc[eligible_uncertainty, ORDERS].astype(float) + 0.5
    beta = (
        result.loc[eligible_uncertainty, CLICKS]
        - result.loc[eligible_uncertainty, ORDERS]
    ).astype(float) + 0.5
    result.loc[eligible_uncertainty, "CVR 90% lower"] = (
        beta_distribution.ppf(0.05, alpha, beta) * 100
    )
    result.loc[eligible_uncertainty, "CVR 90% upper"] = (
        beta_distribution.ppf(0.95, alpha, beta) * 100
    )
    result["Evidence note"] = np.select(
        [
            ~valid_orders,
            result[CLICKS] == 0,
            result[CLICKS] < 30,
            (result["CVR 90% upper"] - result["CVR 90% lower"]) >= 15,
        ],
        [
            "Orders exceed clicks; interval not applicable",
            "No click evidence",
            "Limited click evidence; wide uncertainty possible",
            "Conversion estimate remains uncertain",
        ],
        default="Review attribution and time-window assumptions",
    )
    result["ML review flag"] = "Not evaluated"
    result["Anomaly score"] = np.nan
    result["Notable peer differences"] = ""
    meta = {
        "trained": False,
        "eligible_terms": 0,
        "flagged_terms": 0,
        "reason": "",
        "method": "IsolationForest + Jeffreys binomial conversion intervals",
    }

    model_mask = (result[CLICKS] >= min_clicks) & (result[IMPRESSIONS] > 0)
    eligible = result.loc[model_mask]
    meta["eligible_terms"] = int(len(eligible))
    if len(eligible) < min_model_terms:
        meta["reason"] = (
            f"Only {len(eligible)} search terms have at least {min_clicks} "
            f"clicks and positive impressions; {min_model_terms} are required."
        )
        return result, meta

    # Modest, robust per-account signals, not external predictive features.
    clicks = eligible[CLICKS].to_numpy(dtype=float)
    impressions = eligible[IMPRESSIONS].to_numpy(dtype=float)
    orders = eligible[ORDERS].to_numpy(dtype=float)
    sales = eligible[SALES].to_numpy(dtype=float)
    spend = eligible[SPEND].to_numpy(dtype=float)
    observables = pd.DataFrame(
        {
            "Click volume": clicks,
            "Spend": spend,
            "Orders": orders,
            "Sales": sales,
            "CTR": np.divide(
                clicks, impressions, out=np.zeros_like(clicks),
                where=impressions > 0
            ),
            "Orders per click": np.divide(
                orders, clicks, out=np.zeros_like(clicks), where=clicks > 0
            ),
            "ROAS": np.divide(
                sales, spend, out=np.zeros_like(sales), where=spend > 0
            ),
        },
        index=eligible.index,
    )
    transformed = observables.copy()
    for name in ("Click volume", "Spend", "Orders", "Sales", "ROAS"):
        transformed[name] = np.log1p(observables[name])
    scaler = RobustScaler()
    scaled = scaler.fit_transform(transformed)
    detector = IsolationForest(
        n_estimators=150,
        contamination=0.10,
        random_state=42,
        n_jobs=1,
    )
    flags = detector.fit_predict(scaled)
    scores = -detector.decision_function(scaled)
    result.loc[eligible.index, "ML review flag"] = np.where(
        flags == -1, "Unusual pattern — review", "Typical within dataset"
    )
    result.loc[eligible.index, "Anomaly score"] = scores
    medians = np.median(scaled, axis=0)
    deviations = np.abs(scaled - medians)
    for position, row_index in enumerate(eligible.index):
        # Descriptive peer differences, NOT an attribution of model scores.
        top = np.argsort(deviations[position])[-2:][::-1]
        parts = []
        for col_position in top:
            name = observables.columns[col_position]
            direction = "above" if scaled[position, col_position] > medians[col_position] else "below"
            parts.append(f"{name} {direction} peer median")
        result.at[row_index, "Notable peer differences"] = "; ".join(parts)
    meta["trained"] = True
    meta["flagged_terms"] = int((flags == -1).sum())
    meta["reason"] = (
        "Unsupervised model fitted to this dataset; its outliers have "
        "not been independently validated."
    )
    return result, meta
