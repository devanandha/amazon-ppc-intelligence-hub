"""PPC Intelligence Hub v3 — clean rebuild by Devanandha VS.

- Uses the preserved ppc_engine.py calculations (not imports from v2 app UI).
- Starts with fictional data; uploads never leave the Streamlit session.
- Uses the isolated animated robot (ppc_buddy_component.py).
- ML output is exploratory and does not claim causal uplift or autonomous bidding.
"""
from __future__ import annotations

from html import escape
import io

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from create_synthetic_demo import make_synthetic_dataframe
from ppc_buddy_component import render_buddy
from ml_insights import analyse_search_terms
from decision_assurance import build_decision_ledger, acossensitivity
from ppc_engine import (
    COL, CURRENCY_SYMBOLS, load_report, clean_report, aggregate,
    add_metrics, build_action_tables, classify_actions, totals, make_export,
)


st.set_page_config(
    page_title="Devanandha VS | PPC Intelligence Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.html("""
<style>
/* Deliberately scoped v3 styling; avoid modifying the Plotly DOM. */
:root { --dvs-ink:#182442; --dvs-purple:#7064f5; --dvs-blue:#478aff; }
[data-testid="stAppViewContainer"] { background:#f5f7fc; }
[data-testid="stSidebar"] > div:first-child {
  background:#fff !important; border-right:1px solid #e6ebf4;
}
[data-testid="stHeader"]{background:rgba(245,247,252,.92);}
.block-container { max-width:1480px; padding-top:1.7rem;padding-bottom:4rem; }
h1,h2,h3,h4{letter-spacing:-.03em;}
[data-testid="stMetric"]{
  border:1px solid #e6ebf5;border-radius:17px;padding:18px;
  background:white;min-height:117px;
  box-shadow:0 8px 25px rgba(26,44,86,.035);
}
[data-testid="stMetricLabel"]{color:#677791;font-size:.82rem;}
[data-testid="stMetricValue"]{color:#172b4b;letter-spacing:-.06em;}
[data-testid="stTabs"] [role="tablist"] {
  display:flex !important;gap:10px !important;flex-wrap:nowrap !important;
  overflow-x:auto !important;overflow-y:hidden !important;
  padding:8px !important;border:1px solid #e6e9f3;
  background:white;border-radius:14px;scrollbar-width:thin;
}
[data-testid="stTabs"] button[role="tab"]{
  white-space:nowrap !important;flex:0 0 auto !important;
  min-width:max-content !important;padding:10px 19px !important;
  font-weight:650 !important;border-radius:9px;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{
  color:#5247d1 !important;background:#eeecff !important;
}
[data-testid="stTabs"] [role="tabpanel"]{padding-top:18px;}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {
  border:1px solid #e6ebf5;border-radius:16px;background:white;
}
.dvs-hero{
  position:relative;overflow:hidden;border-radius:25px;
  background:linear-gradient(115deg,#121c38 0%,#1b2c59 60%,#413d93 100%);
  padding:33px 38px;color:#fff;box-shadow:0 24px 45px rgba(25,43,96,.14);
  margin-bottom:16px;display:grid;grid-template-columns:minmax(0,1fr) 260px;
  gap:26px;align-items:center;
}
.dvs-hero:after{content:"";position:absolute;right:-125px;top:-160px;
  width:460px;height:460px;border-radius:50%;
  background:radial-gradient(circle,rgba(100,220,243,.25),transparent 65%);pointer-events:none;}
.dvs-left,.dvs-right{position:relative;z-index:1}
.dvs-brand{display:flex;align-items:center;gap:11px;flex-wrap:wrap;
  color:#b6d9fa;letter-spacing:.1em;font-size:.71rem;font-weight:850;}
.dvs-logo{width:38px;height:38px;display:flex;align-items:center;justify-content:center;
  font-size:.75rem;letter-spacing:0;border-radius:12px;
  background:linear-gradient(140deg,#798cff,#50d9ee);color:#fff;
  box-shadow:0 10px 20px rgba(71,115,217,.3);}
.dvs-hero h1{font-size:clamp(2.05rem,3.1vw,3.05rem);line-height:1.12;letter-spacing:-.055em;
  margin:17px 0 12px;color:#fff;}
.dvs-hero h1 strong{color:#a8c9ff;}
.dvs-hero p{max-width:700px;color:#c7d6ee;line-height:1.65;font-size:.92rem;margin:0;}
.dvs-badges{margin-top:18px;display:flex;flex-wrap:wrap;gap:8px;}
.dvs-badge{border:1px solid rgba(199,226,255,.22);background:rgba(255,255,255,.09);
  border-radius:99px;padding:7px 11px;color:#dfeeff;font-size:.7rem;font-weight:700;}
.dvs-right{background:rgba(255,255,255,.075);border:1px solid rgba(216,226,255,.18);
  padding:16px;border-radius:17px;}
.dvs-right small{display:block;color:#a7c5ed;font-size:.66rem;font-weight:850;
  letter-spacing:.11em;margin-bottom:14px;}
.dvs-flow{display:flex;flex-direction:column;gap:8px;}
.dvs-flow div{padding:9px 11px;border-radius:10px;border:1px solid rgba(208,227,255,.15);
  background:rgba(8,21,61,.27);font-size:.77rem;color:#e6edff;font-weight:700;}
.dvs-flow i{font-style:normal;margin-right:8px;color:#71ecdb;font-weight:900;}
.dvs-headerline{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;
  margin:21px 0 12px;flex-wrap:wrap;}
.dvs-headerline h2{margin:0;font-size:1.35rem;color:#1b2947;letter-spacing:-.04em;}
.dvs-headerline p{margin:5px 0 0;color:#6b7c94;font-size:.82rem;}
.dvs-eyebrow{display:block;color:#625cce;font-size:.67rem;letter-spacing:.14em;font-weight:850;margin-bottom:5px;}
.dvs-mode{background:#fff;border:1px solid #e5eafa;border-radius:13px;padding:12px 15px;
  font-size:.82rem;color:#556b89;display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:13px;}
.dvs-mode strong{color:#243653;}
.dvs-mode em{margin-left:auto;background:#e6f8f0;border-radius:99px;padding:5px 10px;
  font-size:.68rem;font-style:normal;color:#1d7854;font-weight:850;}
.dvs-foot{color:#7887a0;font-size:.75rem;margin:35px 0 0;border-top:1px solid #e2e9f3;padding:20px 0;}
@media(max-width:850px){.dvs-hero{grid-template-columns:1fr;padding:26px 24px;}
  .dvs-right{display:none;}.dvs-hero h1{font-size:2rem;}}
@media(max-width:520px){.dvs-hero{padding:21px 18px;}.dvs-mode em{margin-left:0;}
  [data-testid="stMetric"]{padding:12px;min-height:106px;}}
</style>
""")


def section(title: str, description: str, eyebrow: str = "WORKSPACE") -> None:
    st.html(
        '<div class="dvs-headerline"><div>'
        f'<span class="dvs-eyebrow">{escape(eyebrow)}</span>'
        f'<h2>{escape(title)}</h2><p>{escape(description)}</p>'
        '</div></div>'
    )


def draw_chart(fig: go.Figure, *, height: int = 385) -> None:
    fig.update_layout(
        template="plotly_white",
        title=None,
        height=height,
        margin=dict(l=30, r=32, t=30, b=76),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial", color="#33435f", size=12),
        legend=dict(
            orientation="h", x=0, y=1.13, yanchor="bottom",
            bgcolor="rgba(255,255,255,0)", font=dict(size=11),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


st.html("""
<header class="dvs-hero" aria-label="Devanandha VS PPC Intelligence Hub">
  <div class="dvs-left">
    <div class="dvs-brand"><span class="dvs-logo">DVS</span>
      DEVANANDHA VS &nbsp; / &nbsp; PPC INTELLIGENCE HUB V3</div>
    <h1>Smarter PPC insights.<br><strong>Decisions you can explain.</strong></h1>
    <p>Explore advertising performance with transparent rules, statistical uncertainty,
       exploratory machine learning and human-reviewed decision assurance.</p>
    <div class="dvs-badges"><span class="dvs-badge">Sponsored Products</span>
      <span class="dvs-badge">Experimental AI</span>
      <span class="dvs-badge">Evidence-first</span>
      <span class="dvs-badge">Built by Devanandha VS</span></div>
  </div>
  <div class="dvs-right">
    <small>HOW THE WORKSPACE THINKS</small>
    <div class="dvs-flow">
      <div><i>01</i> Observe advertising signals</div>
      <div><i>02</i> Check evidence quality</div>
      <div><i>03</i> Detect unusual patterns</div>
      <div><i>04</i> Recommend human review</div>
    </div>
  </div>
</header>
""")

with st.sidebar:
    st.markdown("### 🤖 DVS / PPC Studio")
    st.caption("Independent analytics workspace — built by Devanandha VS.")
    source_choice = st.radio(
        "Data source",
        [
            "Explore fictional demo",
            "Upload my own report",
            "Upload weekly campaign CSV",
        ],
        index=0,
        help="Search-term reports and weekly campaign CSVs are separate data types. "
             "Do not upload confidential account reports without permission.",
    )
    demo_mode = source_choice == "Explore fictional demo"
    campaign_mode = source_choice == "Upload weekly campaign CSV"
    uploaded = None
    if campaign_mode:
        uploaded = st.file_uploader(
            "Weekly Sponsored Products campaign CSV",
            type=["csv"],
            key="weekly_campaign_csv_upload",
        )
    elif not demo_mode:
        uploaded = st.file_uploader(
            "Sponsored Products Search Term report", type=["xlsx", "xls"]
        )
    st.divider()
    target_acos = st.number_input("Target ACOS (%)", min_value=1.0, max_value=200.0, value=25.0, step=1.0)
    negative_clicks = st.number_input("Clicks before negative review", min_value=1, max_value=500, value=15)
    min_orders = st.number_input("Minimum orders for positive review", min_value=1, max_value=100, value=3)
    st.divider()
    st.caption("AI anomaly signals are exploratory. No automatic changes are made to Amazon Ads.")
    st.markdown("[GitHub source](https://github.com/devanandha/amazon-ppc-intelligence-hub)")
    st.markdown("[Developer LinkedIn](https://www.linkedin.com/in/devanandhavs21)")


if campaign_mode:
    from campaign_intelligence import render_campaign_intelligence
    render_campaign_intelligence(uploaded, float(target_acos))
    st.stop()


if demo_mode:
    raw = make_synthetic_dataframe()
    st.html(
        '<div class="dvs-mode"><strong>Fictional demo active</strong>'
        '<span>All figures are generated for demonstration and do not represent real clients.</span>'
        '<em>SYNTHETIC DATA</em></div>'
    )
elif uploaded is None:
    st.info("Upload a Sponsored Products Search Term report in the sidebar to view your dashboard.")
    st.stop()
else:
    try:
        raw = load_report(uploaded.getvalue())
    except Exception as exc:
        st.error(f"Could not read the uploaded workbook: {exc}")
        st.stop()
    st.html(
        '<div class="dvs-mode"><strong>Uploaded report active</strong>'
        '<span>Keep search-term data confidential. No production automation is enabled.</span>'
        '<em>HUMAN REVIEW ONLY</em></div>'
    )

clean, missing = clean_report(raw)
if missing:
    st.error("The report is missing required Amazon fields: " + ", ".join(missing))
    st.stop()
if clean.empty:
    st.warning("The selected report contains no rows.")
    st.stop()

campaign_choices = sorted(clean[COL["campaign"]].dropna().astype(str).unique())
selected_campaigns = st.multiselect(
    "Campaign filter (optional)",
    options=campaign_choices,
    default=[],
    placeholder="All campaigns",
    help="The demo shows all campaigns by default.",
)
data = clean.loc[
    clean[COL["campaign"]].isin(selected_campaigns)
    if selected_campaigns else pd.Series(True, index=clean.index)
].copy()
if data.empty:
    st.warning("No rows match this filter.")
    st.stop()

currency = str(data["Currency"].dropna().iloc[0]).upper() if "Currency" in data and data["Currency"].notna().any() else "GBP"
symbol = CURRENCY_SYMBOLS.get(currency, "")
kpi = totals(data)
campaign = aggregate(data, [COL["campaign"]])
ad_group = aggregate(data, [COL["campaign"], COL["ad_group"]])
search, harvest, negatives, asins = build_action_tables(
    data, float(target_acos), int(negative_clicks), int(min_orders),
)
wasted = search[(search[COL["orders"]] == 0) & (search[COL["spend"]] > 0)].copy()
wasted_spend = float(wasted[COL["spend"]].sum())

# Dedicated HTML component (isolated iframe); guaranteed vertical space
# and a visible robot before any tabs or charts.
render_buddy(
    account_acos=float(kpi["ACOS"]),
    target_acos=float(target_acos),
    ad_sales=float(kpi["Sales"]),
    harvest_count=len(harvest),
    negative_count=len(negatives),
    demo_mode=bool(demo_mode),
)

section(
    "Performance at a glance",
    "The core metrics and opportunity signals from the selected report.",
    "01 / EXECUTIVE OVERVIEW",
)
metric_specs = [
    ("Ad spend", f"{symbol}{kpi['Spend']:,.2f}"),
    ("Attributed sales", f"{symbol}{kpi['Sales']:,.2f}"),
    ("Observed ACOS", f"{kpi['ACOS']:.2f}%" if kpi["Sales"] > 0 else "Undefined"),
    ("Observed ROAS", f"{kpi['ROAS']:.2f}x"),
]
for column, (label, value) in zip(st.columns(4), metric_specs):
    column.metric(label, value)

small_specs = [
    ("Attributed orders", f"{int(kpi['Orders']):,}"),
    ("Zero-order spend", f"{symbol}{wasted_spend:,.2f}"),
    ("CTR", f"{kpi['CTR']:.2f}%"),
    ("Observed orders / clicks", f"{kpi['CVR']:.2f}%"),
]
for column, (label, value) in zip(st.columns(4), small_specs):
    column.metric(label, value)

st.caption(
    "Zero-order spend is a screening metric, not verified waste. "
    "Attributed orders can exceed clicks; attribution must be reviewed before interpreting conversion rates."
)

# Campaign state is never inferred from historical search-term activity.
# A separate uploaded state roster can identify campaigns missing from the report.
from campaign_status import render_status_panel
campaign_status_data = campaign.rename(columns={
    COL["campaign"]: "Campaign",
    COL["spend"]: "Spend",
    COL["sales"]: "Sales",
    COL["clicks"]: "Clicks",
})
render_status_panel(campaign_status_data, float(target_acos), key="search_term")

section(
    "Explore your PPC intelligence",
    "Choose a workspace to inspect performance, recommendations, evidence or exports.",
    "02 / INTERACTIVE WORKSPACE",
)

overview_tab, action_tab, assurance_tab, export_tab = st.tabs([
    "📊 Overview", "🎯 Opportunities", "🧠 AI & Assurance", "📥 Scenarios & Export",
])

with overview_tab:
    left, right = st.columns(2)
    with left:
        st.markdown("#### Campaign spend vs attributed sales")
        st.caption("Two observed metrics, not predicted future performance.")
        top_campaigns = campaign.sort_values(COL["spend"], ascending=False).head(10)
        chart = px.bar(
            top_campaigns,
            x=COL["campaign"],
            y=[COL["spend"], COL["sales"]],
            barmode="group",
            labels={"value": currency, COL["campaign"]: "", "variable": "Metric"},
            color_discrete_sequence=["#7369f3", "#19b9c8"],
        )
        chart.update_xaxes(tickangle=-25, automargin=True)
        draw_chart(chart)
    with right:
        st.markdown("#### Efficiency map")
        st.caption("Reported sales versus ACOS; bubble size represents spend.")
        points = campaign[(campaign[COL["clicks"]] > 0) & campaign["ACOS %"].notna()].copy()
        if points.empty:
            st.info("No campaign has enough attributed sales to show ACOS.")
        else:
            fig = px.scatter(
                points, x="ACOS %", y=COL["sales"],
                size=COL["spend"], hover_name=COL["campaign"],
                labels={COL["sales"]: f"Attributed sales ({currency})"},
                color_discrete_sequence=["#746aff"],
            )
            fig.add_vline(
                x=float(target_acos), line_color="#ed8d6b",
                line_dash="dash", annotation_text="Target ACOS",
            )
            draw_chart(fig)

    if COL["date"] in data.columns and data[COL["date"]].notna().any():
        st.markdown("#### Daily advertising trend")
        st.caption("Historical attributed sales and spend in the selected period.")
        trend = aggregate(data.dropna(subset=[COL["date"]]), [COL["date"]]).sort_values(COL["date"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend[COL["date"]], y=trend[COL["spend"]],
            name="Spend", mode="lines", line=dict(color="#7369f3", width=3),
        ))
        fig.add_trace(go.Scatter(
            x=trend[COL["date"]], y=trend[COL["sales"]],
            name="Attributed sales", mode="lines", line=dict(color="#16b9c1", width=3),
        ))
        fig.update_yaxes(title_text=currency)
        draw_chart(fig, height=340)

    st.markdown("#### Campaign comparison")
    st.dataframe(
        campaign.sort_values(COL["spend"], ascending=False),
        use_container_width=True, hide_index=True,
    )

with action_tab:
    cards = st.columns(4)
    cards[0].metric("Search terms analysed", f"{len(search):,}")
    cards[1].metric("Potential harvest terms", f"{len(harvest):,}")
    cards[2].metric("Negative-review candidates", f"{len(negatives):,}")
    cards[3].metric("ASIN opportunities", f"{len(asins):,}")
    st.caption(
        "These are transparent rule-based screening categories, not automated "
        "keyword changes or independently validated results."
    )
    st.markdown("#### Search-term review queue")
    st.dataframe(
        search.sort_values(COL["spend"], ascending=False),
        use_container_width=True, hide_index=True,
    )
    lcol, rcol = st.columns(2)
    with lcol:
        st.markdown("#### Keyword harvest candidates")
        st.dataframe(harvest, use_container_width=True, hide_index=True)
    with rcol:
        st.markdown("#### Possible negative candidates")
        st.dataframe(negatives, use_container_width=True, hide_index=True)
    st.markdown("#### Potential ASIN opportunities")
    st.dataframe(asins, use_container_width=True, hide_index=True)

with assurance_tab:
    st.markdown("#### AI-assisted evidence review")
    st.caption(
        "An unsupervised Isolation Forest identifies unusual patterns within this "
        "report. It does not predict sales, profit or the effect of bid changes."
    )
    observed_clicks = search[COL["clicks"]].fillna(0)
    min_observed_clicks = int(observed_clicks.min()) if not search.empty else 0
    max_observed_clicks = int(observed_clicks.max()) if not search.empty else 0
    # Adjust the control to the scale of each report. Synthetic demo terms
    # contain many clicks; the old 1..40 slider could never change eligibility.
    slider_limit = max(
        100,
        min(1000, int(np.ceil(max_observed_clicks / 25.0) * 25)),
    )
    minimum_ml_clicks = st.slider(
        "Minimum clicks for model comparison",
        min_value=5, max_value=slider_limit, value=5, step=5,
        key="v3_minimum_ml_clicks",
        help="Search-term clicks are aggregated across the selected report. "
             "Raise the threshold to withhold low-evidence terms from the ML review.",
    )
    ml, meta = analyse_search_terms(search, min_clicks=int(minimum_ml_clicks))
    st.caption(
        f"Search terms in this report have between **{min_observed_clicks:,}** "
        f"and **{max_observed_clicks:,}** aggregated clicks. "
        "Only terms above the chosen threshold are considered by the model."
    )
    if int(meta["eligible_terms"]) == len(search):
        st.info(
            "Every search term currently meets this click threshold. "
            "Increase it above the lowest observed click count to see the "
            "ML review population change."
        )
    ledger = build_decision_ledger(
        search, ml,
        review_clicks=30, review_orders=5, max_interval_width_pp=15.0,
    )
    a, b, c = st.columns(3)
    a.metric("Model-eligible terms", int(meta["eligible_terms"]))
    b.metric("Unusual pattern flags", int(meta["flagged_terms"]))
    c.metric(
        "High-impact cases needing attention",
        int(
            (
                ledger["High-impact baseline action"]
                & ledger["Evidence status"].ne("Manual review ready")
            ).sum()
        ),
    )
    if not meta["trained"]:
        st.warning(meta["reason"])
    else:
        st.info(
            "AI anomalies are relative to this dataset. A flagged term is "
            "not necessarily underperforming or unsafe."
        )
    st.markdown("#### Auditable decision ledger")
    st.dataframe(ledger, use_container_width=True, hide_index=True)
    st.download_button(
        "Download decision evidence ledger (CSV)",
        data=ledger.to_csv(index=False).encode("utf-8"),
        file_name="DevanandhaVS_PPC_Decision_Ledger.csv",
        mime="text/csv",
    )
    st.caption(
        "Conversion-rate credible intervals use a simplified binomial model "
        "and may be inappropriate for Amazon's attributed-order counts."
    )

with export_tab:
    st.markdown("#### Target ACOS sensitivity")
    alternative = st.slider(
        "Alternative target ACOS (%)", 1, 100,
        value=min(100, max(1, int(target_acos) + 10)),
    )
    alt = classify_actions(
        search, float(alternative), int(negative_clicks), int(min_orders),
    )
    comparison = pd.DataFrame({
        "Search term": search[COL["search_term"]],
        "Observed ACOS %": search["ACOS %"],
        "Current rule action": search["Recommended Action"],
        "Alternative rule action": alt["Recommended Action"],
    })
    changed = comparison[
        comparison["Current rule action"] != comparison["Alternative rule action"]
    ]
    st.metric("Rule labels that would change", int(len(changed)))
    if changed.empty:
        st.info("No original rule labels change under this target.")
    else:
        st.dataframe(changed, use_container_width=True, hide_index=True)
    st.caption(
        "This is a sensitivity analysis of existing rules on fixed observations, "
        "not a sales forecast or counterfactual return estimate."
    )
    st.markdown("#### Export the eight-sheet PPC report")
    summary = pd.DataFrame(
        [{"Metric": key, "Value": value} for key, value in kpi.items()]
    )
    try:
        workbook = make_export(
            summary, campaign, ad_group, search,
            harvest, negatives, asins, wasted, symbol,
        )
        st.download_button(
            "Download PPC report (Excel)",
            data=workbook,
            file_name="DevanandhaVS_PPC_Intelligence_v3.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as exc:
        st.error(f"Export failed: {exc}")

st.html(
    '<footer class="dvs-foot"><strong>Devanandha VS</strong> · '
    'Independent PPC Intelligence Hub v3 · Experimental human-reviewed '
    'decision support · Not endorsed by Amazon. '
    '<a href="https://github.com/devanandha/amazon-ppc-intelligence-hub">'
    'Source code</a></footer>'
)
