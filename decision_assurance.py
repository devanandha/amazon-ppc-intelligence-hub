"""Decision Assurance: evidence-gated, human-reviewed PPC action audit.

This is an explicit rule-based safety overlay. It does not validate the
underlying bid recommendations, claim causal impact, or output probabilities
that an action will improve ROI.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TERM = "Customer Search Term"
CLICKS = "Clicks"
ORDERS = "7 Day Total Orders (#)"
ACTIONS = "Recommended Action"
HIGH_IMPACT = frozenset({
    "Scale carefully",
    "Negative / pause review",
    "Reduce bid / pause review",
})
ML_FLAG = "Unusual pattern — review"

REQUIRED_RULES = (TERM, CLICKS, ORDERS, ACTIONS, "Bid Adjustment %", "Reason")
REQUIRED_ML = (TERM, "ML review flag", "CVR 90% lower", "CVR 90% upper", "Evidence note")


def build_decision_ledger(
    rule_actions: pd.DataFrame,
    ml_review: pd.DataFrame,
    *,
    review_clicks: int = 30,
    review_orders: int = 5,
    max_interval_width_pp: float = 15.0,
) -> pd.DataFrame:
    """Combine existing decisions, uncertainty and ML review signals.

    Inputs must be unique, aggregated search-term tables. An action label is
    *never* promoted to "approved": the strongest state is "Manual review ready".
    Human judgement and business context remain essential.
    """
    if review_clicks < 1 or review_orders < 1 or max_interval_width_pp <= 0:
        raise ValueError("Review thresholds must be positive.")
    for name, table, required in (
        ("rule_actions", rule_actions, REQUIRED_RULES),
        ("ml_review", ml_review, REQUIRED_ML),
    ):
        missing = set(required).difference(table.columns)
        if missing:
            raise ValueError(f"{name} missing: {', '.join(sorted(missing))}")
        if table[TERM].duplicated().any() or table[TERM].isna().any():
            raise ValueError(f"{name} must have unique, non-null aggregated search terms.")

    # Use a one-to-one keyed merge, not positional numpy assignment. Never
    # attribute a model flag to another customer's search term.
    ml_cols = list(REQUIRED_ML)
    for extra in ("Anomaly score", "Notable peer differences"):
        if extra in ml_review.columns:
            ml_cols.append(extra)
    ledger = rule_actions.merge(
        ml_review[ml_cols], on=TERM, validate="one_to_one",
        how="left", indicator=True,
    )
    if (ledger["_merge"] != "both").any() or len(ledger) != len(ml_review):
        raise ValueError("Rule actions and ML review do not cover the same unique search terms.")
    ledger = ledger.drop(columns=["_merge"])

    clicks = pd.to_numeric(ledger[CLICKS], errors="coerce").fillna(0)
    orders = pd.to_numeric(ledger[ORDERS], errors="coerce").fillna(0)
    lower = pd.to_numeric(ledger["CVR 90% lower"], errors="coerce")
    upper = pd.to_numeric(ledger["CVR 90% upper"], errors="coerce")
    width = upper - lower
    ledger["CVR interval width (pp)"] = width.round(2)

    ledger["High-impact baseline action"] = (
        ledger[ACTIONS].isin(HIGH_IMPACT)
        | (pd.to_numeric(ledger["Bid Adjustment %"], errors="coerce").abs() >= 15)
    )
    states, explanations, checks = [], [], []
    for i, row in ledger.iterrows():
        c, o = float(clicks.loc[i]), float(orders.loc[i])
        interval = float(width.loc[i]) if pd.notna(width.loc[i]) else np.nan
        anomaly = row["ML review flag"] == ML_FLAG
        high_impact = bool(row["High-impact baseline action"])

        if c <= 0:
            state, reason = "More evidence needed", "No observed clicks; cannot assess a conversion outcome."
        elif o > c:
            state, reason = "Check data quality", "Attributed orders exceed clicks; binomial CVR interval is invalid."
        elif high_impact and anomaly:
            state, reason = "Investigate model-rule conflict", "A high-impact rule action coincides with an unusual peer pattern."
        elif high_impact and c < review_clicks:
            state, reason = "More evidence needed", f"High-impact action with fewer than {review_clicks} clicks."
        elif high_impact and o == 0:
            state, reason = "Human validation required", "No attributed orders; check attribution, relevance and timing before negating."
        elif high_impact and o < review_orders:
            state, reason = "More evidence needed", f"High-impact action with fewer than {review_orders} orders."
        elif high_impact and (not np.isfinite(interval)):
            state, reason = "Review uncertainty assumptions", "A valid conversion uncertainty interval is unavailable."
        elif high_impact and interval > max_interval_width_pp:
            state, reason = "More evidence needed", f"Observed conversion uncertainty exceeds {max_interval_width_pp:g} percentage points."
        elif anomaly:
            state, reason = "Inspect unusual pattern", "An unusual peer pattern warrants manual investigation."
        else:
            state, reason = "Manual review ready", "Evidence gates did not identify a reason to defer review; no action is approved."

        states.append(state)
        explanations.append(reason)
        checks.append(
            "High-impact rule" if high_impact else "Routine rule"
        )
    ledger["Evidence status"] = states
    ledger["Evidence justification"] = explanations
    ledger["Action category"] = checks
    ledger["Decision system"] = "Devanandha VS · Decision Assurance prototype v0.1"
    return ledger


def acossensitivity(
    search: pd.DataFrame,
    classifier,
    target_acos: float,
    *,
    negative_clicks: int,
    min_orders: int,
) -> pd.DataFrame:
    """Show rule-label sensitivity to alternative user-defined ACOS targets.

    Sensitivity is not prediction, posterior confidence or expected uplift.
    """
    if target_acos <= 0:
        raise ValueError("Target ACOS must be positive.")
    multipliers = (0.6, 0.8, 1.0, 1.2, 1.4)
    baseline = search[ACTIONS].reset_index(drop=True)
    frame = pd.DataFrame({TERM: search[TERM].reset_index(drop=True)})
    comparisons = []
    for factor in multipliers:
        target = float(target_acos) * factor
        changed = classifier(search, target, negative_clicks, min_orders)[ACTIONS].reset_index(drop=True)
        comparisons.append(changed.eq(baseline).astype(int))
        frame[f"Target ACOS {factor:.0%} of current"] = changed
    frame["Unchanged across 5 scenarios"] = sum(comparisons).eq(len(multipliers))
    frame["Scenario agreement (of 5)"] = sum(comparisons)
    return frame
