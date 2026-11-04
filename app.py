"""Amazon Sponsored Products PPC Intelligence Hub.

Upload a Sponsored Products Search Term report exported from Amazon Ads.
The application analyses performance locally in the Streamlit session and
produces an explainable, downloadable action report.
"""

from __future__ import annotations

import io
import re
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from ui_theme import inject_styles, render_hero, render_empty_state, render_sidebar_brand, render_footer
from ml_insights import analyse_search_terms
from decision_assurance import build_decision_ledger, acossensitivity
from evidence_report import create_evidence_report
from create_synthetic_demo import make_synthetic_dataframe

COL = {
    "date": "Start Date",
    "portfolio": "Portfolio name",
    "currency": "Currency",
    "campaign": "Campaign Name",
    "ad_group": "Ad Group Name",
    "targeting": "Targeting",
    "match_type": "Match Type",
    "search_term": "Customer Search Term",
    "impressions": "Impressions",
    "clicks": "Clicks",
    "spend": "Spend",
    "sales": "7 Day Total Sales",
    "orders": "7 Day Total Orders (#)",
    "units": "7 Day Total Units (#)",
}

REQUIRED = [
    COL["campaign"], COL["ad_group"], COL["targeting"], COL["match_type"],
    COL["search_term"], COL["impressions"], COL["clicks"], COL["spend"],
    COL["sales"], COL["orders"],
]

NUMERIC = [
    COL["impressions"], COL["clicks"], COL["spend"], COL["sales"],
    COL["orders"], COL["units"],
]

CURRENCY_SYMBOLS = {"GBP": "£", "USD": "$", "EUR": "€", "CAD": "C$", "AUD": "A$"}


def safe_divide(numerator: pd.Series | float, denominator: pd.Series | float, multiplier: float = 1.0):
    """Divide safely, returning zero where the denominator is zero."""
    if isinstance(denominator, pd.Series):
        return np.where(denominator > 0, numerator / denominator * multiplier, 0.0)
    return numerator / denominator * multiplier if denominator > 0 else 0.0


@st.cache_data(show_spinner=False)
def load_report(file_bytes: bytes) -> pd.DataFrame:
    df = pd.read_excel(io.BytesIO(file_bytes))
    df.columns = df.columns.astype(str).str.replace("\u00a0", " ", regex=False).str.strip()
    return df


@st.cache_data(show_spinner=False)
def load_business_report(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(file_bytes))


def clean_report(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    cleaned = df.copy()
    cleaned.columns = cleaned.columns.astype(str).str.replace("\u00a0", " ", regex=False).str.strip()
    missing = [column for column in REQUIRED if column not in cleaned.columns]
    if missing:
        return cleaned, missing

    for column in NUMERIC:
        if column not in cleaned.columns:
            cleaned[column] = 0
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce").fillna(0).clip(lower=0)

    for column in [COL["campaign"], COL["ad_group"], COL["targeting"], COL["match_type"], COL["search_term"]]:
        cleaned[column] = cleaned[column].fillna("Unknown").astype(str).str.strip()

    if COL["date"] in cleaned.columns:
        cleaned[COL["date"]] = pd.to_datetime(cleaned[COL["date"]], errors="coerce")
    return cleaned, []


def add_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["CTR %"] = safe_divide(result[COL["clicks"]], result[COL["impressions"]], 100)
    result["CPC"] = safe_divide(result[COL["spend"]], result[COL["clicks"]])
    result["CVR %"] = safe_divide(result[COL["orders"]], result[COL["clicks"]], 100)
    result["ACOS %"] = np.where(
        result[COL["sales"]] > 0,
        result[COL["spend"]] / result[COL["sales"]] * 100,
        np.nan,
    )
    result["ROAS"] = safe_divide(result[COL["sales"]], result[COL["spend"]])
    result["AOV"] = safe_divide(result[COL["sales"]], result[COL["orders"]])
    return result


def aggregate(df: pd.DataFrame, dimensions: Iterable[str]) -> pd.DataFrame:
    dimensions = list(dimensions)
    grouped = (
        df.groupby(dimensions, dropna=False)
        .agg({
            COL["impressions"]: "sum",
            COL["clicks"]: "sum",
            COL["spend"]: "sum",
            COL["sales"]: "sum",
            COL["orders"]: "sum",
            COL["units"]: "sum",
        })
        .reset_index()
    )
    return add_metrics(grouped)


def classify_actions(table: pd.DataFrame, target_acos: float, min_clicks: int, min_orders: int) -> pd.DataFrame:
    result = table.copy()
    actions, priorities, reasons, adjustments = [], [], [], []
    for _, row in result.iterrows():
        clicks, orders = row[COL["clicks"]], row[COL["orders"]]
        spend, sales, acos = row[COL["spend"]], row[COL["sales"]], row["ACOS %"]
        if clicks == 0:
            action, priority, reason, adjustment = "Collect data", "Low", "No clicks recorded", 0
        elif orders == 0 and clicks >= min_clicks:
            action, priority, reason, adjustment = "Negative / pause review", "High", f"{int(clicks)} clicks and spend with no orders", -100
        elif orders == 0:
            action, priority, reason, adjustment = "Monitor", "Medium", "No orders yet; evidence below negative threshold", 0
        elif orders < min_orders:
            action, priority, reason, adjustment = "Collect more data", "Low", f"Only {int(orders)} order(s)", 0
        elif acos <= target_acos * 0.8:
            action, priority, reason = "Scale carefully", "High", "ACOS materially below target with conversions"
            adjustment = min(30, max(5, round((target_acos / max(acos, 0.01) - 1) * 100)))
        elif acos <= target_acos:
            action, priority, reason, adjustment = "Maintain / harvest", "Medium", "Profitable at target ACOS", 0
        elif acos <= target_acos * 1.5:
            action, priority, reason = "Reduce bid", "Medium", "ACOS above target"
            adjustment = max(-30, min(-5, round((target_acos / acos - 1) * 100)))
        else:
            action, priority, reason = "Reduce bid / pause review", "High", "ACOS materially above target"
            adjustment = max(-50, round((target_acos / acos - 1) * 100))
        actions.append(action);
        priorities.append(priority);
        reasons.append(reason);
        adjustments.append(adjustment)

    result["Recommended Action"] = actions
    result["Priority"] = priorities
    result["Reason"] = reasons
    result["Bid Adjustment %"] = adjustments
    result["Suggested CPC"] = (result["CPC"] * (1 + result["Bid Adjustment %"] / 100)).clip(lower=0)
    return result


def add_health_status(table: pd.DataFrame, target_acos: float, min_clicks: int,
                      min_orders: int) -> pd.DataFrame:
    """Add an evidence-aware health status and plain-English explanation."""
    result = table.copy()
    statuses, explanations = [], []

    for _, row in result.iterrows():
        clicks, orders = row[COL["clicks"]], row[COL["orders"]]
        sales, acos = row[COL["sales"]], row["ACOS %"]

        if clicks < 5:
            status = "⚪ Insufficient Data"
            explanation = "Fewer than 5 clicks are available"
        elif orders == 0 and clicks >= min_clicks:
            status = "🔴 Unhealthy"
            explanation = f"{int(clicks)} clicks but no attributed orders"
        elif orders == 0:
            status = "🟠 Monitor"
            explanation = "No orders yet; evidence is below the action threshold"
        elif orders < min_orders:
            status = "🟠 Monitor"
            explanation = f"Only {int(orders)} attributed order(s)"
        elif sales > 0 and acos <= target_acos:
            status = "🟢 Healthy"
            explanation = f"ACOS {acos:.2f}% is within the {target_acos:.2f}% target"
        elif sales > 0 and acos <= target_acos * 1.25:
            status = "🟠 Monitor"
            explanation = f"ACOS {acos:.2f}% is slightly above target"
        else:
            status = "🔴 Unhealthy"
            explanation = "ACOS is materially above target"

        statuses.append(status)
        explanations.append(explanation)

    result["Health Status"] = statuses
    result["Health Explanation"] = explanations
    return result


def is_asin(value: str) -> bool:
    value = str(value).strip().upper()
    return bool(re.fullmatch(r"B[A-Z0-9]{9}", value))


def build_action_tables(df: pd.DataFrame, target_acos: float, negative_clicks: int, min_orders: int):
    search = aggregate(df, [COL["search_term"]])
    search["Is ASIN"] = search[COL["search_term"]].map(is_asin)
    search = classify_actions(search, target_acos, negative_clicks, min_orders)

    harvest = search[
        (~search["Is ASIN"])
        & (search[COL["orders"]] >= 3)
        & (search[COL["clicks"]] >= 10)
        & (search[COL["sales"]] >= 50)
        & search["ACOS %"].notna()
        & (search["ACOS %"] <= target_acos)
        ].sort_values([COL["sales"], COL["orders"]], ascending=False)
    negatives = search[
        (~search["Is ASIN"]) & (search[COL["orders"]] == 0)
        & (search[COL["clicks"]] >= negative_clicks)
        ].sort_values(COL["spend"], ascending=False)
    asins = search[
        search["Is ASIN"]
        & (search[COL["orders"]] >= 3)
        & (search[COL["sales"]] >= 50)
        & search["ACOS %"].notna()
        & (search["ACOS %"] <= target_acos)
        ].sort_values(COL["sales"], ascending=False)
    return search, harvest, negatives, asins


def totals(df: pd.DataFrame) -> dict[str, float]:
    spend, sales = df[COL["spend"]].sum(), df[COL["sales"]].sum()
    clicks, impressions = df[COL["clicks"]].sum(), df[COL["impressions"]].sum()
    orders, units = df[COL["orders"]].sum(), df[COL["units"]].sum()
    return {
        "Spend": spend, "Sales": sales, "Orders": orders, "Units": units,
        "Impressions": impressions, "Clicks": clicks,
        "ACOS": safe_divide(spend, sales, 100), "ROAS": safe_divide(sales, spend),
        "CTR": safe_divide(clicks, impressions, 100), "CVR": safe_divide(orders, clicks, 100),
        "CPC": safe_divide(spend, clicks), "AOV": safe_divide(sales, orders),
    }


def business_totals(df: pd.DataFrame):
    sales = pd.to_numeric(
        df["Ordered Product Sales"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False),
        errors="coerce"
    ).fillna(0).sum()

    units = pd.to_numeric(
        df["Units Ordered"],
        errors="coerce"
    ).fillna(0).sum()

    orders = pd.to_numeric(
        df["Total Order Items"],
        errors="coerce"
    ).fillna(0).sum()

    sessions = pd.to_numeric(
        df["Sessions - Total"]
        .astype(str)
        .str.replace(",", "", regex=False),
        errors="coerce"
    ).fillna(0).sum()

    conversion_rate = (
        orders / sessions * 100
        if sessions > 0
        else 0
    )

    return {
        "Total Sales": sales,
        "Units": units,
        "Orders": orders,
        "Sessions": sessions,
        "Conversion Rate": conversion_rate
    }


def format_excel_sheet(writer, sheet_name: str, frame: pd.DataFrame, currency_symbol: str):
    frame.to_excel(writer, sheet_name=sheet_name, index=False)
    workbook, worksheet = writer.book, writer.sheets[sheet_name]
    header = workbook.add_format({"bold": True, "font_color": "white", "bg_color": "#17365D", "border": 1})
    money = workbook.add_format(
        {"num_format": f'{currency_symbol}#,##0.00'}
    )
    for col_num, name in enumerate(frame.columns):
        worksheet.write(0, col_num, name, header)
        width = min(42, max(12, len(str(name)) + 2, *(len(str(v)) + 1 for v in frame[name].head(200))))
        cell_format = money if name in [COL["spend"], COL["sales"], "CPC", "AOV", "Suggested CPC"] else None
        worksheet.set_column(col_num, col_num, width, cell_format)
    worksheet.freeze_panes(1, 0)
    worksheet.autofilter(0, 0, max(len(frame), 1), max(len(frame.columns) - 1, 0))


def make_export(summary: pd.DataFrame, campaign: pd.DataFrame, ad_group: pd.DataFrame,
                search: pd.DataFrame, harvest: pd.DataFrame, negatives: pd.DataFrame,
                asins: pd.DataFrame, wasted: pd.DataFrame,
                currency_symbol: str) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, frame in [
            ("Executive Summary", summary), ("Campaign Performance", campaign),
            ("Ad Group Performance", ad_group), ("All Search Terms", search),
            ("Harvest Keywords", harvest), ("Negative Candidates", negatives),
            ("Winning ASINs", asins), ("Wasted Spend", wasted),
        ]:
            format_excel_sheet(writer, name, frame, currency_symbol)
    return output.getvalue()


def display_table(frame: pd.DataFrame, currency_symbol: str):
    currency_cols = [c for c in [COL["spend"], COL["sales"], "CPC", "AOV", "Suggested CPC"] if c in frame.columns]
    percent_cols = [c for c in ["CTR %", "CVR %", "ACOS %", "Bid Adjustment %"] if c in frame.columns]
    formats = {c: f"{currency_symbol}%.2f" for c in currency_cols}
    formats.update({c: "%.2f%%" for c in percent_cols})
    st.dataframe(frame, use_container_width=True, hide_index=True, column_config={
        "Reason": st.column_config.TextColumn(width="large"),
        "Recommended Action": st.column_config.TextColumn(width="medium"),
    })


st.set_page_config(page_title="Amazon PPC Intelligence Hub | Decision Intelligence", page_icon="📈", layout="wide")
inject_styles()
render_hero()

with st.sidebar:
    render_sidebar_brand()
    st.header("Analysis settings")
    target_acos = st.number_input("Target ACOS (%)", min_value=1.0, max_value=200.0, value=25.0, step=1.0)
    negative_clicks = st.number_input("Clicks before negative review", min_value=1, max_value=200, value=15)
    min_orders = st.number_input("Minimum orders for a winner", min_value=1, max_value=50, value=3)
    st.caption(
        "Recommendations are decision support. Review relevance, profitability, placement and campaign strategy before applying changes.")

st.markdown("### Choose how to explore")
demo_mode = st.toggle(
    "Explore the built-in fictional demo",
    value=False,
    help="Loads reproducible synthetic search-term data. No real Amazon account or client data is used.",
)
if demo_mode:
    st.success("Demo mode: all advertising activity shown is fictional and for illustration only.")
uploaded = st.file_uploader(
    "Upload an Amazon Sponsored Products Search Term report",
    type=["xlsx", "xls"],
    disabled=demo_mode,
)
business_uploaded = st.file_uploader(
    "Upload Business Report (Sales & Traffic By Date)",
    type=["csv"],
    disabled=demo_mode,
)
if not demo_mode and uploaded is None:
    render_empty_state()
    render_footer()
    st.caption(
        "Reports are analysed within this application session. Do not upload "
        "confidential employer or client data to a public demo."
    )
    st.stop()

if demo_mode:
    raw = make_synthetic_dataframe()
else:
    try:
        raw = load_report(uploaded.getvalue())
    except Exception as exc:
        st.error(f"The workbook could not be read: {exc}")
        st.stop()

df, missing = clean_report(raw)
business_kpi = None
if business_uploaded is not None and not demo_mode:
    business_df = load_business_report(
        business_uploaded.getvalue()
    )

    business_kpi = business_totals(
        business_df
    )

if missing:
    st.error("Required columns are missing: " + ", ".join(missing))
    st.stop()

with st.sidebar:
    campaigns = sorted(df[COL["campaign"]].unique())
    selected_campaigns = st.multiselect("Campaigns", campaigns, default=campaigns)
    match_types = sorted(df[COL["match_type"]].unique())
    selected_match_types = st.multiselect("Match types", match_types, default=match_types)

filtered = df[df[COL["campaign"]].isin(selected_campaigns) & df[COL["match_type"]].isin(selected_match_types)].copy()
if filtered.empty:
    st.warning("The selected filters contain no rows.")
    st.stop()

currency_code = str(filtered[COL["currency"]].mode().iloc[0]) if COL["currency"] in filtered and not filtered[
    COL["currency"]].mode().empty else "GBP"
symbol = CURRENCY_SYMBOLS.get(currency_code.upper(), currency_code + " ")

campaign = classify_actions(aggregate(filtered, [COL["campaign"]]), target_acos, negative_clicks, min_orders)
ad_group = classify_actions(aggregate(filtered, [COL["campaign"], COL["ad_group"]]), target_acos, negative_clicks,
                            min_orders)
campaign = add_health_status(campaign, target_acos, negative_clicks, min_orders)
ad_group = add_health_status(ad_group, target_acos, negative_clicks, min_orders)
search, harvest, negatives, asins = build_action_tables(filtered, target_acos, negative_clicks, min_orders)
wasted = search[(search[COL["orders"]] == 0) & (search[COL["clicks"]] >= negative_clicks)].sort_values(COL["spend"],
                                                                                                       ascending=False)
kpi = totals(filtered)
if business_kpi:
    total_sales = business_kpi["Total Sales"]
    organic_sales = max(
        0,
        total_sales - kpi["Sales"]
    )

    tacos = (
        (kpi["Spend"] / total_sales) * 100
        if total_sales > 0
        else 0
    )

    ad_contribution = (
        (kpi["Sales"] / total_sales) * 100
        if total_sales > 0
        else 0
    )

else:

    total_sales = 0
    organic_sales = 0
    tacos = 0
    ad_contribution = 0
wasted_total = wasted[COL["spend"]].sum()
waste_rate = safe_divide(wasted_total, kpi["Spend"], 100)
if business_kpi:
    st.subheader("Account Performance")
    account_cols = st.columns(7)

    account_cols[0].metric(
        "Total Sales",
        f"{symbol}{total_sales:,.2f}"
    )

    account_cols[1].metric(
        "Organic Sales",
        f"{symbol}{organic_sales:,.2f}"
    )

    account_cols[2].metric(
        "Ad Sales",
        f"{symbol}{kpi['Sales']:,.2f}"
    )

    account_cols[3].metric(
        "TACOS",
        f"{tacos:.2f}%"
    )

    account_cols[4].metric(
        "Ad Contribution",
        f"{ad_contribution:.2f}%"
    )

    account_cols[5].metric(
        "Sessions",
        f"{int(business_kpi['Sessions']):,}"
    )

    account_cols[6].metric(
        "Account CVR",
        f"{business_kpi['Conversion Rate']:.2f}%"
    )

st.subheader("Executive KPIs")

top = st.columns(6)
for box, label, value in zip(top, ["Ad Spend", "Ad Sales", "Orders", "ACOS", "ROAS", "Wasted Spend"],
                             [f"{symbol}{kpi['Spend']:,.2f}", f"{symbol}{kpi['Sales']:,.2f}", f"{int(kpi['Orders']):,}",
                              f"{kpi['ACOS']:.2f}%", f"{kpi['ROAS']:.2f}x", f"{symbol}{wasted_total:,.2f}"]):
    box.metric(label, value)
bottom = st.columns(6)
for box, label, value in zip(bottom, ["Impressions", "Clicks", "CTR", "CPC", "CVR", "AOV"],
                             [f"{int(kpi['Impressions']):,}", f"{int(kpi['Clicks']):,}", f"{kpi['CTR']:.2f}%",
                              f"{symbol}{kpi['CPC']:.2f}", f"{kpi['CVR']:.2f}%", f"{symbol}{kpi['AOV']:.2f}"]):
    box.metric(label, value)

st.info(
    f"The analysis found **{len(harvest):,}** profitable keyword-harvesting opportunities, "
    f"**{len(negatives):,}** negative candidates and **{len(asins):,}** winning ASIN targets. "
    f"Zero-order search terms account for **{waste_rate:.1f}%** of selected spend."
)

overview_tab, campaigns_tab, terms_tab, actions_tab, scenario_tab, ai_tab, studio_tab, quality_tab = st.tabs([
    "Overview", "Sponsored Products", "Search Terms", "Action Centre",
    "Scenario Lab", "AI Review", "Decision Studio", "Data Quality"
])

with overview_tab:
    left, right = st.columns(2)
    with left:
        chart_data = campaign.sort_values(COL["spend"], ascending=False).head(15)
        fig = px.bar(chart_data, x=COL["campaign"], y=[COL["spend"], COL["sales"]], barmode="group",
                     title="Top campaigns: spend vs sales", labels={"value": currency_code})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        scatter = campaign[campaign[COL["clicks"]] > 0].copy()
        fig = px.scatter(scatter, x="ACOS %", y=COL["sales"], size=COL["spend"], color="Priority",
                         hover_name=COL["campaign"], title="Campaign efficiency map")
        fig.add_vline(x=target_acos, line_dash="dash", line_color="red", annotation_text="Target ACOS")
        st.plotly_chart(fig, use_container_width=True)

    if COL["date"] in filtered.columns and filtered[COL["date"]].notna().any():
        trend = aggregate(filtered.dropna(subset=[COL["date"]]), [COL["date"]]).sort_values(COL["date"])
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=trend[COL["date"]],
                y=trend[COL["spend"]],
                name="Spend",
                mode="lines+markers"
            ),
            secondary_y=False
        )

        fig.add_trace(
            go.Scatter(
                x=trend[COL["date"]],
                y=trend[COL["sales"]],
                name="Sales",
                mode="lines+markers"
            ),
            secondary_y=True
        )

        fig.update_layout(
            title="Performance over time",
            hovermode="x unified"
        )

        fig.update_yaxes(
            title_text="Spend ($)",
            secondary_y=False
        )

        fig.update_yaxes(
            title_text="Sales ($)",
            secondary_y=True
        )

        st.plotly_chart(fig, use_container_width=True)

with campaigns_tab:
    st.subheader("Campaign Health Summary")
    health_columns = st.columns(4)
    health_columns[0].metric("🟢 Healthy", int(campaign["Health Status"].eq("🟢 Healthy").sum()))
    health_columns[1].metric("🟠 Monitor", int(campaign["Health Status"].eq("🟠 Monitor").sum()))
    health_columns[2].metric("🔴 Unhealthy", int(campaign["Health Status"].eq("🔴 Unhealthy").sum()))
    health_columns[3].metric("⚪ Insufficient Data", int(campaign["Health Status"].eq("⚪ Insufficient Data").sum()))
    st.subheader("Campaign-level performance and recommendations")
    display_table(campaign.sort_values(COL["spend"], ascending=False), symbol)
    st.subheader("Ad-group-level performance")
    display_table(ad_group.sort_values(COL["spend"], ascending=False), symbol)

with terms_tab:
    st.subheader("Top-performing customer search terms")
    winners = search[(search[COL["orders"]] > 0)].sort_values([COL["sales"], COL["orders"]], ascending=False).head(100)
    display_table(winners, symbol)
    st.subheader("All aggregated search terms")
    st.caption("Repeated search terms are aggregated before KPIs and recommendations are calculated.")
    display_table(search.sort_values(COL["spend"], ascending=False), symbol)

with actions_tab:
    a, b, c, d = st.tabs(["Harvest", "Negatives", "Winning ASIN targets", "Wasted spend"])
    with a:
        st.caption("Search terms with sufficient orders and ACOS at or below target. Review for exact-match campaigns.")
        display_table(harvest, symbol)
    with b:
        st.caption(
            "Non-ASIN terms above the selected click threshold with no attributed orders. Check relevance before negating.")
        display_table(negatives, symbol)
    with c:
        st.caption("Converting ASIN search terms at or below target ACOS. Review as product-targeting opportunities.")
        display_table(asins, symbol)
    with d:
        display_table(wasted, symbol)

with scenario_tab:
    st.subheader("Scenario Lab: target ACOS sensitivity")
    st.caption(
        "Compare how the same observed search-term data would be classified "
        "under another target ACOS. This is a sensitivity check, not a "
        "forecast of sales or proof of improved performance."
    )
    scenario_target = st.slider(
        "Alternative target ACOS (%)",
        min_value=1,
        max_value=200,
        value=min(200, max(1, int(round(target_acos)) + 10)),
        step=1,
        help="Only the target ACOS changes. Click and order thresholds stay fixed.",
    )
    simulated_search = classify_actions(
        search, float(scenario_target), negative_clicks, min_orders
    )
    comparison = pd.DataFrame({
        "Search Term": search[COL["search_term"]],
        "Clicks": search[COL["clicks"]],
        "Orders": search[COL["orders"]],
        "ACOS %": search["ACOS %"],
        "Current action": search["Recommended Action"],
        "Scenario action": simulated_search["Recommended Action"],
        "Current bid adjustment %": search["Bid Adjustment %"],
        "Scenario bid adjustment %": simulated_search["Bid Adjustment %"],
    })
    action_changed = comparison[
        comparison["Current action"] != comparison["Scenario action"]
    ].copy()
    bid_changed = (
        comparison["Current bid adjustment %"]
        != comparison["Scenario bid adjustment %"]
    ).sum()
    stat_a, stat_b, stat_c = st.columns(3)
    stat_a.metric("Search terms evaluated", f"{len(comparison):,}")
    stat_b.metric("Actions changed", f"{len(action_changed):,}")
    stat_c.metric("Bid suggestions changed", f"{int(bid_changed):,}")
    st.markdown("#### Changed recommendations")
    if action_changed.empty:
        st.success(
            "No action labels change under this target. Bid suggestions "
            "may still differ, as indicated above."
        )
    else:
        st.dataframe(
            action_changed.sort_values(["Clicks", "Orders"], ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    with st.expander("What this scenario does and does not show"):
        st.markdown(
            "- Reapplies the existing transparent rules to the same "
            "observations under an alternative target ACOS.\n"
            "- Does **not** predict changes in clicks, sales, demand or profit.\n"
            "- Does **not** account for attribution lag, competition, "
            "seasonality, placement, contribution margin or budget constraints.\n"
            "- Suggestions must be reviewed before changing live bids."
        )


with ai_tab:
    st.subheader("AI-assisted search-term review")
    st.caption(
        "An exploratory unsupervised machine-learning model flags unusual "
        "patterns within the uploaded data. It does not forecast sales, "
        "determine wasted spend, or automatically change bids."
    )
    ml_min_clicks = st.slider(
        "Minimum clicks for ML comparison", 1, 40, 5,
        help="Search terms with fewer clicks are withheld from ML scoring.",
    )
    ml_data, ml_meta = analyse_search_terms(
        search, min_clicks=int(ml_min_clicks)
    )
    # Triangulate the original transparent action with an independent
    # exploratory outlier signal. This is a review queue, not auto-optimisation.
    ml_data["Existing rule action"] = search["Recommended Action"].to_numpy()
    favourable = ml_data["Existing rule action"].isin(
        ["Scale carefully", "Maintain / harvest"]
    )
    unusual = ml_data["ML review flag"].eq("Unusual pattern — review")
    ml_data["Hybrid review note"] = np.select(
        [
            unusual & favourable,
            unusual,
        ],
        [
            "Check unusual evidence before scaling or harvesting",
            "Unusual pattern: inspect the underlying observations",
        ],
        default="Use normal human review; no unusual ML signal",
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Search terms with usable evidence", f"{ml_meta['eligible_terms']:,}")
    c2.metric("Flagged for human review", f"{ml_meta['flagged_terms']:,}")
    c3.metric("Model status", "Analysed" if ml_meta["trained"] else "Not fitted")
    st.info(
        "An Isolation Forest detects unusual combinations of click volume, "
        "spend, attributed orders, sales and efficiency rates. It is fitted "
        "only to this uploaded dataset. Its scores are **not** validated "
        "probabilities or measures of profitability."
    )
    if not ml_meta["trained"]:
        st.warning(ml_meta["reason"])
    else:
        flagged = ml_data[ml_data["ML review flag"] == "Unusual pattern — review"]
        st.markdown("#### Human-review queue: statistical signals + existing actions")
        if flagged.empty:
            st.success("No unusual patterns met the model's review threshold.")
        else:
            st.dataframe(
                flagged.sort_values("Anomaly score", ascending=False),
                use_container_width=True,
                hide_index=True,
            )
        st.caption(
            "The hybrid review note pairs an existing rule action with an "
            "unsupervised flag; it is not a trained action recommender. "
            "The peer differences are descriptive comparisons, "
            "not exact feature attributions explaining the model's output."
        )
    with st.expander("Conversion-rate uncertainty and evidence notes"):
        st.write(
            "90% Bayesian credible intervals estimate uncertainty in the "
            "observed orders-per-click rate using a Jeffreys prior. They "
            "assume a binomial model; some Ads attribution patterns violate "
            "this assumption, so intervals are withheld where orders exceed clicks."
        )
        st.dataframe(
            ml_data[
                [
                    "Customer Search Term",
                    "Clicks",
                    "7 Day Total Orders (#)",
                    "CVR 90% lower",
                    "CVR 90% upper",
                    "Evidence note",
                    "ML review flag",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    st.download_button(
        "Download AI review audit (CSV)",
        data=ml_data.to_csv(index=False).encode("utf-8"),
        file_name="PPC_Exploratory_ML_Review.csv",
        mime="text/csv",
        key="download_ml_review",
    )
    st.caption(
        "This is an experimental model-driven screening feature. Every "
        "suggestion requires human validation before any real-world action."
    )



with studio_tab:
    st.subheader("Decision Assurance Studio")
    st.caption(
        "A transparent human-review workflow: combine the existing "
        "threshold rules with statistical uncertainty and exploratory "
        "ML signals. An evidence gate never approves or executes a bid change."
    )
    st.markdown("#### Review policy")
    policy1, policy2, policy3 = st.columns(3)
    with policy1:
        review_clicks = st.number_input(
            "Minimum clicks for high-impact review", 5, 300, 30, 5,
            key="assurance_review_clicks",
        )
    with policy2:
        review_orders = st.number_input(
            "Minimum attributed orders for high-impact review", 1, 50, 5, 1,
            key="assurance_review_orders",
        )
    with policy3:
        max_width = st.number_input(
            "Maximum 90% CVR interval width (pp)", 1.0, 80.0, 15.0, 1.0,
            key="assurance_width",
        )

    # The model is unsupervised and fitted only within the supplied report.
    assurance_ml, assurance_meta = analyse_search_terms(search, min_clicks=5)
    audit = build_decision_ledger(
        search, assurance_ml,
        review_clicks=int(review_clicks),
        review_orders=int(review_orders),
        max_interval_width_pp=float(max_width),
    )
    attention = audit[
        (audit["High-impact baseline action"])
        & (audit["Evidence status"] != "Manual review ready")
    ]
    conflicts = audit[
        audit["Evidence status"] == "Investigate model-rule conflict"
    ]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Search terms audited", f"{len(audit):,}")
    c2.metric("High-impact rule suggestions", f"{int(audit['High-impact baseline action'].sum()):,}")
    c3.metric("High-impact actions needing review", f"{len(attention):,}")
    c4.metric("ML–rule attention flags", f"{len(conflicts):,}")
    st.caption(
        "These numbers describe a review queue on the current report, "
        "not real-world improvement, predictive accuracy or approval rates."
    )
    st.markdown("#### Review queue")
    queue = audit[[
        COL["search_term"], COL["clicks"], COL["orders"],
        "Recommended Action", "High-impact baseline action",
        "Evidence status", "Evidence justification",
        "ML review flag", "CVR interval width (pp)",
    ]].copy()
    st.dataframe(
        queue.sort_values(["High-impact baseline action", COL["clicks"]],
                          ascending=[False, False]),
        use_container_width=True, hide_index=True,
    )
    st.markdown("#### Inspect a decision")
    terms_to_inspect = audit[COL["search_term"]].astype(str).tolist()
    selected_term = st.selectbox(
        "Select an aggregated search term",
        terms_to_inspect, key="assurance_selected_term",
    )
    case = audit.loc[audit[COL["search_term"]].astype(str) == selected_term].iloc[0]
    a, b, c = st.columns(3)
    a.metric("Observed clicks", f"{int(case[COL['clicks']]):,}")
    b.metric("Attributed orders", f"{int(case[COL['orders']]):,}")
    c.metric("Observed ACOS", f"{case['ACOS %']:.2f}%" if pd.notna(case["ACOS %"]) else "Undefined")
    st.markdown(f"**Existing rule:** {case['Recommended Action']}")
    st.markdown(f"**Evidence gate:** {case['Evidence status']}")
    st.write(case["Evidence justification"])
    st.markdown(f"**ML review:** {case['ML review flag']}")
    st.caption(
        "A ML anomaly is a relative pattern difference, not an attribution "
        "of profitability or proof a recommendation is wrong."
    )
    if pd.notna(case["CVR 90% lower"]):
        st.info(
            f"Observed orders-per-click model: 90% Bayesian interval "
            f"{case['CVR 90% lower']:.1f}% to {case['CVR 90% upper']:.1f}%. "
            "Assumes a simplified binomial attribution model."
        )
    else:
        st.warning(
            "No valid conversion-rate interval is available for this term. "
            "Do not substitute missing statistical evidence with an AI score."
        )

    st.markdown("#### Decision sensitivity map")
    stability = acossensitivity(
        search, classify_actions, target_acos,
        negative_clicks=negative_clicks, min_orders=min_orders,
    )
    scenario_columns = [
        name for name in stability.columns
        if name.startswith("Target ACOS ")
    ]
    top_names = (
        search.sort_values(COL["spend"], ascending=False)
        [COL["search_term"]].astype(str).head(15).tolist()
    )
    show_stability = stability[
        stability[COL["search_term"]].astype(str).isin(top_names)
    ].copy()
    show_stability["_sort"] = show_stability[COL["search_term"]].astype(str).map(
        {name: i for i, name in enumerate(top_names)}
    )
    show_stability = show_stability.sort_values("_sort")
    if not show_stability.empty:
        # 1 = same rule label as current setting, 0 = different label.
        labels = show_stability[scenario_columns].eq(
            show_stability["Target ACOS 100% of current"], axis=0
        ).astype(int)
        fig = px.imshow(
            labels.to_numpy(),
            x=["60%", "80%", "100%", "120%", "140%"],
            y=show_stability[COL["search_term"]].astype(str).to_list(),
            zmin=0, zmax=1,
            labels={"x": "ACOS target relative to current", "y": "Search term",
                    "color": "Same action"},
            title="Does the rule recommendation change when the target changes?",
            aspect="auto",
            color_continuous_scale=[[0, "#f5ad97"], [0.49, "#f5ad97"],
                                    [0.5, "#79d9dd"], [1, "#79d9dd"]],
        )
        fig.update_layout(height=max(350, 35 * len(show_stability) + 135))
        st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Teal = original rule label stays the same; orange = rule label changes. "
        "This checks sensitivity to five ACOS thresholds on unchanged historic "
        "observations. It is not causal simulation or a sales forecast."
    )
    st.download_button(
        "Download decision evidence ledger (CSV)",
        audit.to_csv(index=False).encode("utf-8"),
        "PPC_DevanandhaVS_Decision_Assurance_Audit.csv",
        "text/csv",
        key="download_assurance_ledger",
    )
    st.download_button(
        "Download branded review report (HTML)",
        create_evidence_report(
            audit, target_acos=float(target_acos),
            synthetic_demo=bool(demo_mode),
        ),
        file_name="DevanandhaVS_PPC_Decision_Assurance.html",
        mime="text/html",
        key="download_branded_assurance_html",
    )
    if not demo_mode:
        st.warning(
            "The HTML report includes real uploaded search terms and "
            "performance information. Do not share without permission."
        )
    st.caption(
        "Devanandha VS · Experimental decision assurance prototype. "
        "All marketing and bid changes require qualified human judgement."
    )


with quality_tab:
    duplicate_rows = int(raw.duplicated().sum())
    zero_click_rows = int((df[COL["clicks"]] == 0).sum())
    st.write({
        "Uploaded rows": len(raw), "Analysed rows after filters": len(filtered),
        "Exact duplicate rows": duplicate_rows, "Rows with zero clicks": zero_click_rows,
        "Detected currency": currency_code,
    })
    st.caption(
        "Rates such as ACOS, ROAS, CTR and CVR are recalculated from aggregated totals rather than averaged from report rows.")

summary_metrics = {
    "Spend": kpi["Spend"], "Sales": kpi["Sales"], "Orders": kpi["Orders"], "Units": kpi["Units"],
    "Impressions": kpi["Impressions"], "Clicks": kpi["Clicks"], "ACOS": kpi["ACOS"], "ROAS": kpi["ROAS"],
    "CTR": kpi["CTR"], "CVR": kpi["CVR"], "CPC": kpi["CPC"], "AOV": kpi["AOV"], "Wasted Spend": wasted_total,
    "Waste Rate %": waste_rate, "Harvest Opportunities": len(harvest), "Negative Candidates": len(negatives),
    "Winning ASINs": len(asins)
}

if business_kpi:
    summary_metrics.update({
        "Total Sales": total_sales, "Organic Sales": organic_sales, "TACOS %": tacos,
        "Ad Contribution %": ad_contribution, "Sessions": business_kpi["Sessions"],
        "Account Conversion Rate %": business_kpi["Conversion Rate"]
    })

summary = pd.DataFrame(
    summary_metrics.items(),
    columns=["KPI", "Value"]
)
export = make_export(summary, campaign, ad_group, search, harvest, negatives, asins, wasted, symbol)
st.download_button("Download PPC Intelligence Action Report", export, "PPC_Intelligence_Action_Report.xlsx",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")

with st.expander("Methodology and limitations"):
    st.markdown("""

        - KPIs (ACOS, ROAS, CTR, CVR and AOV) are recalculated from aggregated totals to ensure accuracy.

        - Search terms are aggregated before recommendations are generated, preventing duplicate terms from being analysed separately.

        - Harvest opportunities require:
                - Minimum 3 orders
                - Minimum 10 clicks
                - Minimum 50 sales
                - ACOS at or below the selected target

            - Negative candidates require:
                - Zero orders
                - Clicks at or above the selected negative-review threshold

            - Winning ASIN targets require:
                - Minimum 3 orders
                - Minimum 50 sales
                - ACOS at or below the selected target

            - Suggested bid adjustments are directional recommendations only and are not applied automatically.

            - Attribution windows, organic sales, contribution margin, placement performance, budget constraints and seasonality are not available within the Search Term Report and should be considered before making changes.
    """)

render_footer()
