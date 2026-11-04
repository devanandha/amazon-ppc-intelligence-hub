"""Weekly campaign-level Amazon Sponsored Products analytics.

This is a distinct analysis workflow. Campaign-level observations must never be
converted into invented search-term data or keyword recommendations.
"""
from __future__ import annotations

from io import BytesIO
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from html import escape
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from ppc_buddy_component import render_buddy

FIELDS = (
    "Week", "Campaign", "Campaign_Type", "Product",
    "Impressions", "Clicks", "Spend", "Orders", "Sales",
)
NUMERIC = ("Impressions", "Clicks", "Spend", "Orders", "Sales")


def weekly_section(title: str, description: str, eyebrow: str) -> None:
    """Reuse the visual language of the main search-term dashboard."""
    st.html(
        '<div class="dvs-headerline"><div>'
        f'<span class="dvs-eyebrow">{escape(eyebrow)}</span>'
        f'<h2>{escape(title)}</h2><p>{escape(description)}</p>'
        '</div></div>'
    )


def weekly_chart(fig, height: int = 385) -> None:
    fig.update_layout(
        template="plotly_white", title=None, height=height,
        margin=dict(l=30, r=32, t=30, b=76),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial", color="#33435f", size=12),
        legend=dict(
            orientation="h", x=0, y=1.13, yanchor="bottom",
            bgcolor="rgba(255,255,255,0)", font=dict(size=11),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def parse_campaign_csv(content: bytes) -> pd.DataFrame:
    """Validate a campaign-level CSV. No fabricated search-term fields."""
    df = pd.read_csv(BytesIO(content), encoding="utf-8-sig")
    df.columns = df.columns.astype(str).str.strip()
    missing = [field for field in FIELDS if field not in df]
    if missing:
        raise ValueError("Missing fields: " + ", ".join(missing))
    df = df.loc[:, list(FIELDS)].copy()
    if df.empty:
        raise ValueError("The CSV contains no campaign rows.")
    df["Week"] = pd.to_datetime(df["Week"], errors="coerce")
    if df["Week"].isna().any():
        raise ValueError("One or more Week values are not valid dates.")
    for name in NUMERIC:
        df[name] = pd.to_numeric(df[name], errors="coerce")
        if df[name].isna().any() or (df[name] < 0).any():
            raise ValueError(f"{name} must contain non-negative numbers.")
    for name in ("Campaign", "Campaign_Type", "Product"):
        df[name] = df[name].fillna("").astype(str).str.strip()
        if (df[name] == "").any():
            raise ValueError(f"{name} has a missing value.")
    if (df["Clicks"] > df["Impressions"]).any():
        raise ValueError("One or more rows have more clicks than impressions.")
    return df


def add_campaign_rates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ACOS %"] = np.where(out["Sales"] > 0, 100 * out["Spend"] / out["Sales"], np.nan)
    out["ROAS"] = np.where(out["Spend"] > 0, out["Sales"] / out["Spend"], np.nan)
    out["CTR %"] = np.where(out["Impressions"] > 0, 100 * out["Clicks"] / out["Impressions"], np.nan)
    out["CPC"] = np.where(out["Clicks"] > 0, out["Spend"] / out["Clicks"], np.nan)
    out["Orders / clicks %"] = np.where(out["Clicks"] > 0, 100 * out["Orders"] / out["Clicks"], np.nan)
    return out


def flag_weekly_outliers(df: pd.DataFrame, min_rows: int = 20) -> pd.DataFrame:
    """Relative Isolation Forest review flags, never causal or bid decisions."""
    out = df.copy()
    out["ML pattern flag"] = "Not evaluated"
    if len(out) < min_rows:
        return out
    columns = ["Impressions", "Clicks", "Spend", "Orders", "Sales"]
    feature = np.log1p(out[columns].astype(float).to_numpy())
    model = IsolationForest(n_estimators=150, contamination=0.10, random_state=42)
    scaled = RobustScaler().fit_transform(feature)
    out["ML pattern flag"] = np.where(model.fit_predict(scaled) == -1, "Review unusual pattern", "Typical in this report")
    return out


def sum_campaigns(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["Impressions", "Clicks", "Spend", "Orders", "Sales"]
    result = df.groupby(["Campaign", "Campaign_Type", "Product"], as_index=False)[cols].sum()
    return add_campaign_rates(result)


def render_campaign_intelligence(uploaded, target_acos: float) -> None:
    weekly_section(
        "Weekly Campaign Intelligence",
        "Experimental Sponsored Products campaign analysis. The weekly CSV does not "
        "contain search terms, so keyword harvesting and negative-keyword "
        "recommendations are deliberately unavailable.",
        "CAMPAIGN-LEVEL ANALYSIS",
    )
    if uploaded is None:
        st.info("Choose your ppc_weekly_2025.csv file using the CSV uploader in the sidebar.")
        st.caption("Expected fields: " + ", ".join(FIELDS))
        st.stop()
    try:
        df = parse_campaign_csv(uploaded.getvalue())
    except Exception as exc:
        st.error(f"Cannot read weekly campaign dataset: {exc}")
        st.stop()

    st.info(
        "Dataset provenance: The publicly shared example is simulated Amazon "
        "Sponsored Products campaign data, not live account performance. "
        "Review licences and permissions before redistributing source data."
    )
    campaigns = sorted(df["Campaign"].unique())
    selected = st.multiselect("Filter campaigns (optional)", campaigns, default=[], key="campaign_csv_filter")
    if selected:
        df = df[df["Campaign"].isin(selected)].copy()
    if df.empty:
        st.warning("No rows match your selection.")
        st.stop()

    df = add_campaign_rates(df)
    totals = df[list(NUMERIC)].sum()
    spend, sales, clicks = float(totals["Spend"]), float(totals["Sales"]), float(totals["Clicks"])
    acos = 100 * spend / sales if sales > 0 else np.nan
    roas = sales / spend if spend > 0 else np.nan
    ctr = 100 * clicks / float(totals["Impressions"]) if totals["Impressions"] > 0 else np.nan
    # Compute anomaly flags only once. Reuse these evidence counts in Buddy
    # and the AI review; model flags remain exploratory, not action labels.
    reviewed = flag_weekly_outliers(df)
    anomaly_count = int((reviewed["ML pattern flag"] == "Review unusual pattern").sum())

    render_buddy(
        account_acos=float(acos),
        target_acos=float(target_acos),
        ad_sales=sales,
        harvest_count=0,
        negative_count=0,
        demo_mode=False,
        weekly_campaign_mode=True,
        campaign_count=int(df["Campaign"].nunique()),
        anomaly_count=anomaly_count,
    )
    weekly_section(
        "Campaign performance at a glance",
        "Observed historical campaign metrics, not predictions or live account state.",
        "01 / EXECUTIVE OVERVIEW",
    )
    metric_labels = [
        ("Ad spend", f"{spend:,.2f}"),
        ("Attributed sales", f"{sales:,.2f}"),
        ("Observed ACOS", f"{acos:.2f}%" if np.isfinite(acos) else "Undefined"),
        ("Observed ROAS", f"{roas:.2f}x" if np.isfinite(roas) else "Undefined"),
    ]
    for col, (label, value) in zip(st.columns(4), metric_labels):
        col.metric(label, value)
    supplementary = [
        ("Attributed orders", f"{int(totals['Orders']):,}"),
        ("Observed CTR", f"{ctr:.2f}%"),
        ("Weekly campaign records", f"{len(df):,}"),
        ("Unusual weekly patterns", f"{anomaly_count:,}"),
    ]
    for col, (label, value) in zip(st.columns(4), supplementary):
        col.metric(label, value)
    st.caption(
        f"{df['Campaign'].nunique()} campaigns · {df['Week'].nunique()} observed weeks · "
        "Currency is not supplied by this CSV: spend and sales use unspecified currency units. "
        "These are historical, simulated campaign records, not live Amazon account statuses."
    )

    from campaign_status import render_status_panel
    snapshot_performance = (
        df.groupby("Campaign", as_index=False)[["Spend", "Sales", "Clicks"]].sum()
    )
    render_status_panel(snapshot_performance, float(target_acos), key="weekly_campaign")

    weekly_section(
        "Explore campaign intelligence",
        "Review weekly history, unusual behaviour, campaign status evidence and exports.",
        "02 / INTERACTIVE WORKSPACE",
    )
    overview, assurance, export, benchmark_tab = st.tabs(
        [
            "📊 Campaign trends", "🧠 Weekly anomaly review",
            "📥 Evidence & export", "🧪 Benchmark & Evaluation",
        ]
    )
    with overview:
        st.markdown("#### Observed weekly spend and attributed sales")
        st.caption("Historical weekly sums; not a forward-looking model.")
        weekly = df.groupby("Week", as_index=False)[["Spend", "Sales"]].sum().sort_values("Week")
        chart = px.line(
            weekly, x="Week", y=["Spend", "Sales"], markers=True,
            labels={"value": "Reported currency units", "variable": "Metric"},
            color_discrete_sequence=["#7369f3", "#19b9c8"],
        )
        weekly_chart(chart)
        st.markdown("#### Campaign comparison")
        st.caption("Campaign-level aggregates across the selected weeks.")
        campaigns_table = sum_campaigns(df).sort_values("Spend", ascending=False)
        compact = ["Campaign", "Campaign_Type", "Product", "Spend", "Sales",
                   "Orders", "ACOS %", "ROAS"]
        st.dataframe(
            campaigns_table[compact].round(3), hide_index=True, use_container_width=True
        )
        with st.expander("All campaign metrics"):
            st.dataframe(
                campaigns_table.round(3), hide_index=True, use_container_width=True
            )

    with assurance:
        st.markdown("#### Unsupervised review — weekly observations")
        st.caption(
            "Isolation Forest highlights unusual combinations of impressions, clicks, "
            "spend, orders and attributed sales relative to this uploaded dataset. "
            "Flags are not predictions, proof of poor performance, or automatic bid actions."
        )
        count = anomaly_count
        c1, c2, c3 = st.columns(3)
        c1.metric("Eligible weekly observations", len(reviewed) if len(reviewed) >= 20 else 0)
        c2.metric("Relative anomaly flags", count)
        c3.metric("Campaigns in scope", df["Campaign"].nunique())
        if len(df) < 20:
            st.warning("At least 20 weekly observations are needed for this exploratory model.")
        display_cols = [
            "Week", "Campaign", "Product", "Spend", "Sales", "Orders",
            "ACOS %", "ROAS", "ML pattern flag",
        ]
        st.dataframe(
            reviewed.loc[reviewed["ML pattern flag"] == "Review unusual pattern", display_cols]
            .sort_values("Week").round(3),
            hide_index=True, use_container_width=True,
        )
        with st.expander("Full weekly evidence table"):
            st.dataframe(reviewed[display_cols].round(3), hide_index=True, use_container_width=True)

    with export:
        st.markdown("#### Campaign-level target sensitivity")
        st.caption(
            "Screening comparison only. A campaign above target ACOS is not necessarily "
            "unprofitable; target profitability, attribution and strategy require human review."
        )
        summary = sum_campaigns(df)
        summary["Target ACOS %"] = target_acos
        summary["Review status"] = np.where(
            summary["Sales"] <= 0, "Review: no attributed sales",
            np.where(summary["ACOS %"] > target_acos, "Above target: review", "At or below target"),
        )
        st.metric("Campaigns above target ACOS", int((summary["Review status"] == "Above target: review").sum()))
        st.dataframe(
            summary[["Campaign", "Spend", "Sales", "ACOS %", "ROAS", "Review status"]].round(3),
            hide_index=True, use_container_width=True,
        )
        evaluated = reviewed
        st.download_button(
            "Download campaign evidence CSV",
            data=evaluated.to_csv(index=False).encode("utf-8"),
            file_name="PPC_Weekly_Campaign_Evidence.csv",
            mime="text/csv",
        )
        st.caption(
            "Generated analysis is for exploratory reproducibility, not independent proof "
            "of sales uplift or production advertising improvements."
        )

    with benchmark_tab:
        from benchmark_ui import render_benchmark_panel
        render_benchmark_panel(
            df, float(target_acos),
            min_clicks=15, min_orders=3,
        )

