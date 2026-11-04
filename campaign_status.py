"""Campaign state snapshot reconciliation for Amazon PPC Studio.

An uploaded campaign-status export is a *snapshot*, never a live API connection.
Search-term and weekly performance history alone cannot establish current state.
"""
from __future__ import annotations

from io import BytesIO
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

NAME_COLUMNS = (
    "Campaign Name", "Campaign", "Campaign Name (Informational only)",
    "Campaign name (informational only)", "Campaign_Name",
)
STATE_COLUMNS = (
    "Campaign State (Informational only)", "Campaign Status", "Campaign State",
    "Serving Status", "Delivery Status", "Status", "State",
)
STATE_ALIASES = {
    "enabled": "Enabled",
    "active": "Enabled",
    "running": "Delivering",
    "delivering": "Delivering",
    "paused": "Paused",
    "pause": "Paused",
    "archived": "Archived",
    "ended": "Ended",
    "scheduled": "Scheduled",
    "pending": "Pending review",
    "pending review": "Pending review",
    "suspended": "Suspended",
    "rejected": "Rejected",
    "draft": "Draft",
    "out of budget": "Out of budget",
    "not delivering": "Not delivering",
    "ineligible": "Ineligible",
}


def _normal(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).replace("_", " ").replace("\u00a0", " ")).strip().casefold()


def _find_column(frame: pd.DataFrame, possibilities: Iterable[str]) -> str | None:
    columns = {_normal(c): str(c) for c in frame.columns}
    for c in possibilities:
        if _normal(c) in columns:
            return columns[_normal(c)]
    return None


def _campaign_key(value: object) -> str:
    return _normal(value)


def _select_sheet(content: bytes) -> pd.DataFrame:
    book = pd.ExcelFile(BytesIO(content))
    ordered = sorted(
        book.sheet_names,
        key=lambda s: (0 if "sponsored products campaign" in _normal(s) else 1),
    )
    for sheet in ordered:
        frame = pd.read_excel(book, sheet_name=sheet)
        if _find_column(frame, NAME_COLUMNS) and _find_column(frame, STATE_COLUMNS):
            return frame
    raise ValueError(
        "No sheet contains both a Campaign Name and a campaign State/Status. "
        "Try a campaign-status CSV with columns Campaign Name, Status."
    )


def parse_campaign_status(content: bytes, filename: str) -> pd.DataFrame:
    """Read a human-exported status roster, never an inferred current state."""
    if Path(filename).suffix.lower() == ".csv":
        frame = pd.read_csv(BytesIO(content), encoding="utf-8-sig")
    elif Path(filename).suffix.lower() in {".xlsx", ".xls"}:
        frame = _select_sheet(content)
    else:
        raise ValueError("Upload a .csv, .xlsx, or .xls campaign-status snapshot.")
    frame.columns = frame.columns.astype(str).str.replace("\u00a0", " ", regex=False).str.strip()
    name_col = _find_column(frame, NAME_COLUMNS)
    state_col = _find_column(frame, STATE_COLUMNS)
    if name_col is None or state_col is None:
        raise ValueError("Campaign Name and State (or Status) are required.")

    # Bulksheets contain child entities (ad groups, targeting, etc.) with
    # their own states. Never mistake those for campaign state.
    entity_col = _find_column(frame, ("Entity", "Record Type", "Record_Type"))
    if entity_col:
        is_campaign = frame[entity_col].fillna("").map(_normal).isin(
            {"campaign", "campaigns"}
        )
        frame = frame.loc[is_campaign].copy()
    product_col = _find_column(frame, ("Product", "Ad Product", "Ad Type"))
    if product_col:
        nonempty = frame[product_col].fillna("").map(_normal)
        if nonempty.str.contains("sponsored products", regex=False).any():
            frame = frame.loc[nonempty.str.contains("sponsored products", regex=False)].copy()

    result = pd.DataFrame({
        "Campaign": frame[name_col].fillna("").astype(str).str.strip(),
        "Reported state": frame[state_col].fillna("").astype(str).str.strip(),
    })
    result = result[result["Campaign"] != ""].copy()
    if result.empty:
        raise ValueError("No campaign rows were found in the status snapshot.")
    result["Campaign key"] = result["Campaign"].map(_campaign_key)

    def map_status(s: str) -> str:
        key = _normal(s)
        return STATE_ALIASES.get(key, "Unrecognised state") if key else "Not specified"

    result["Status classification"] = result["Reported state"].map(map_status)
    # Multiple child/duplicate rows or conflicting records are not resolved
    # by arbitrarily picking first/last (which could incorrectly show Enabled).
    variants = result.groupby("Campaign key")["Status classification"].nunique()
    ambiguous_keys = set(variants[variants > 1].index)
    result = result.drop_duplicates("Campaign key", keep="first")
    result.loc[result["Campaign key"].isin(ambiguous_keys), "Status classification"] = "Conflicting states"
    return result.reset_index(drop=True)


def reconcile_campaigns(performance: pd.DataFrame, status: pd.DataFrame | None,
                        target_acos: float) -> pd.DataFrame:
    """Coverage comparison: roster may include campaigns absent in report.

    performance columns: Campaign, Spend, Sales, Clicks (all aggregated).
    """
    needed = {"Campaign", "Spend", "Sales", "Clicks"}
    missing = needed - set(performance.columns)
    if missing:
        raise ValueError("Missing performance columns: " + ", ".join(sorted(missing)))
    perf = performance[list(needed)].copy()
    perf["Campaign key"] = perf["Campaign"].map(_campaign_key)
    perf = perf.groupby("Campaign key", as_index=False).agg(
        {"Campaign": "first", "Spend": "sum", "Sales": "sum", "Clicks": "sum"}
    )
    perf["Seen in performance report"] = True

    if status is None:
        merged = perf.copy()
        merged["Reported state"] = ""
        merged["Status classification"] = "Not verified"
        merged["From status roster"] = False
    else:
        roster = status[["Campaign key", "Campaign", "Reported state", "Status classification"]].copy()
        roster = roster.rename(columns={"Campaign": "Roster name"})
        merged = perf.merge(roster, on="Campaign key", how="outer", validate="one_to_one")
        merged["From status roster"] = merged["Roster name"].notna()
        merged["Seen in performance report"] = merged["Seen in performance report"].fillna(False).astype(bool)
        merged["Campaign"] = merged["Campaign"].fillna(merged["Roster name"])
        merged["Reported state"] = merged["Reported state"].fillna("")
        merged["Status classification"] = merged["Status classification"].fillna("Not verified")
        merged = merged.drop(columns=["Roster name"])
    for n in ("Spend", "Sales", "Clicks"):
        merged[n] = merged[n].fillna(0)
    merged["ACOS %"] = np.where(
        merged["Sales"] > 0, 100.0 * merged["Spend"] / merged["Sales"], np.nan
    )
    merged["Report coverage"] = np.where(
        merged["Seen in performance report"],
        "Present in selected period",
        "Missing from selected report",
    )

    def strategy(row: pd.Series) -> tuple[str, str]:
        state = row["Status classification"]
        seen = row["Seen in performance report"]
        spend, sales, clicks = row["Spend"], row["Sales"], row["Clicks"]
        acos = row["ACOS %"]
        if state == "Conflicting states":
            return "Verify source", "Conflicting status entries. Export a fresh campaign-level roster."
        if state in ("Unrecognised state", "Not specified"):
            return "Verify status", "Unknown state. Check Campaign Manager before making decisions."
        if state == "Not verified":
            return "Status unknown", "Campaign appears in history but has no matching status row. Check name/ID and current state."
        if state == "Archived":
            return "Archive review", "Do not attempt to reactivate an archived campaign; assess a new campaign if needed."
        if state == "Paused":
            return "Paused review", "Confirm why paused and whether there is business justification to resume."
        if state in ("Ended", "Scheduled", "Pending review", "Suspended", "Rejected", "Draft", "Out of budget", "Not delivering", "Ineligible"):
            return "Delivery review", "Check schedule, policy, budget, billing and product eligibility in Amazon Ads."
        if not seen:
            return "Coverage gap", (
                "Enabled/delivering in status snapshot but absent from the selected period. "
                "Check reporting dates, budget, targeting, product availability, "
                "Featured Offer eligibility and delivery in Campaign Manager."
            )
        if spend <= 0 or clicks <= 0:
            return "Delivery check", "No spend or clicks in selected report. Verify impressions, campaign delivery, targeting and budget."
        if sales <= 0:
            return "Conversion review", "Spend without attributed sales. Review sample size, listing conversion, queries and attribution."
        if np.isfinite(acos) and acos > target_acos:
            return "Efficiency review", "Observed ACOS above chosen target. Review margin, attribution and targeting before any bid changes."
        return "Maintain / investigate", "At or below target on historical observations. Check data sufficiency before scaling."

    recommendations = merged.apply(strategy, axis=1)
    merged["Strategy status"] = recommendations.map(lambda v: v[0])
    merged["Human review suggestion"] = recommendations.map(lambda v: v[1])
    return merged.sort_values(
        ["From status roster", "Seen in performance report", "Campaign"],
        ascending=[False, True, True],
    ).reset_index(drop=True)


def render_status_panel(performance: pd.DataFrame, target_acos: float, key: str) -> None:
    """Show a separate optional status snapshot and missing-campaign strategy."""
    import streamlit as st

    with st.expander("📡 Campaign status & missing-campaign strategy (optional)", expanded=False):
        st.caption(
            "Historical performance does not reveal whether a campaign is live right now. "
            "Upload a current Campaign Manager / Sponsored Products bulksheet export "
            "for a point-in-time snapshot. Enabled is not a guarantee of delivering."
        )
        template = "Campaign Name,Status\nDemo campaign A,Enabled\nDemo campaign B,Paused\n"
        st.download_button(
            "Download example status CSV format (fictional campaigns)",
            data=template, file_name="PPC_Status_Snapshot_Example.csv", mime="text/csv",
            key=f"{key}_status_template",
        )
        upload = st.file_uploader(
            "Campaign status export (CSV or Excel)", type=["csv", "xlsx", "xls"],
            key=f"{key}_campaign_status_snapshot",
            help="Use campaign-level records, not ad-group or keyword states. "
                 "Do not upload confidential account files without permission.",
        )
        status = None
        if upload is not None:
            try:
                status = parse_campaign_status(upload.getvalue(), upload.name)
            except Exception as exc:
                st.error(f"Could not read campaign status snapshot: {exc}")
                return
        else:
            st.info(
                "No status snapshot uploaded. All campaign states remain 'Not verified'; "
                "the performance report alone cannot identify currently active campaigns."
            )
        result = reconcile_campaigns(performance, status, float(target_acos))
        if status is not None:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Enabled / delivering (snapshot)", int(
                result["Status classification"].isin(["Enabled", "Delivering"]).sum()
            ))
            c2.metric("Paused / archived", int(
                result["Status classification"].isin(["Paused", "Archived"]).sum()
            ))
            c3.metric("Roster campaigns missing from report", int((
                (~result["Seen in performance report"]) & result["From status roster"]
            ).sum()))
            c4.metric("Report campaigns not in roster", int((
                result["Seen in performance report"] & (~result["From status roster"])
            ).sum()))
            st.warning(
                "Statuses are captured only as of your uploaded export, NOT a live sync. "
                "Name mismatches, report filters, differing dates or portfolios can produce false gaps."
            )
        shown = [
            "Campaign", "Reported state", "Status classification", "Report coverage",
            "Spend", "Sales", "ACOS %", "Strategy status", "Human review suggestion",
        ]
        st.dataframe(result[shown].round(2), use_container_width=True, hide_index=True)
        st.download_button(
            "Download campaign status & strategy audit CSV",
            data=result[shown].to_csv(index=False).encode("utf-8"),
            file_name="PPC_Campaign_Status_Strategy_Audit.csv",
            mime="text/csv", key=f"{key}_status_audit",
        )
