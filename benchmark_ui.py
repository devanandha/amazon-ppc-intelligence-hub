"""Streamlit front end for the reproducible campaign benchmark.

Executed explicitly by the user; no third-party uploads or background tasks.
"""
from __future__ import annotations

from io import BytesIO
import hashlib
import json
import zipfile

import pandas as pd
import streamlit as st

from benchmark_campaigns import run_benchmark


def _as_zip(result: dict) -> bytes:
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("summary.json", json.dumps(result["summary"], indent=2, sort_keys=True))
        archive.writestr("observation_comparison.csv", result["observations"].to_csv(index=False))
        archive.writestr("ml_sensitivity.csv", result["sensitivity"].to_csv(index=False))
        archive.writestr(
            "METHOD.md",
            "# Weekly PPC benchmark — simulated/authorised data only\n\n"
            "Baseline: simple threshold-based campaign-week review screen. "
            "It is **not** a human-labelled truth set.\n\n"
            "ML: Isolation Forest on log1p(Impressions, Clicks, Spend, Orders, Sales), "
            "RobustScaler, 150 trees, contamination 0.1, seeds 42–46.\n\n"
            "Seed Jaccard compares flag membership on the same dataset; "
            "contamination sensitivity explores an imposed review budget.\n\n"
            "Agreement is NOT classification accuracy. "
            "No outcome labels, experiment, commercial uplift, predictive bidding "
            "performance, independent validation or causal conclusion are established.\n\n"
            "Data rows in this ZIP originate from the CSV uploaded to this app "
            "session. Keep the export private unless redistribution is authorised.\n",
        )
    return stream.getvalue()


def render_benchmark_panel(df: pd.DataFrame, target_acos: float,
                           min_clicks: int = 15, min_orders: int = 3) -> None:
    st.markdown("#### Reproducible baseline vs ML evaluation")
    st.caption(
        "This is an investigation of coverage and stability, not a claim that AI "
        "beats a rule-based system. The source dataset is simulated and contains "
        "no human-reviewed correct action labels."
    )
    st.info(
        "Method: identify high-priority ACOS/evidence cases with transparent rules, "
        "compare them with Isolation Forest anomaly flags, then vary the random seed "
        "and contamination setting to test stability."
    )
    # Use per-session state to retain results after downloading or navigating tabs.
    signature = hashlib.sha256(
        pd.util.hash_pandas_object(df, index=True).values.tobytes()
        + f"|{target_acos}|{min_clicks}|{min_orders}".encode()
    ).hexdigest()
    if st.button("Run reproducible evaluation", key="run_campaign_evaluation"):
        with st.spinner("Comparing weekly review signals across five model seeds..."):
            try:
                result = run_benchmark(
                    df, float(target_acos), int(min_clicks), int(min_orders)
                )
            except Exception as exc:
                st.error(f"Benchmark failed: {exc}")
            else:
                st.session_state["weekly_campaign_benchmark"] = (signature, result)
    stored = st.session_state.get("weekly_campaign_benchmark")
    if not stored or stored[0] != signature:
        st.caption(
            "Choose Run reproducible evaluation to generate metrics and a "
            "downloadable evidence package. Nothing is submitted to Amazon Ads."
        )
        return

    result = stored[1]
    summary = result["summary"]
    st.markdown("#### Review coverage")
    stats = [
        ("High-priority rule flags", summary["baseline_priority_review_rows"]),
        ("ML anomaly flags", summary["ml_anomaly_rows"]),
        ("Both", summary["overlap_rule_and_ml"]),
        ("ML only", summary["ml_only"]),
    ]
    for column, (label, value) in zip(st.columns(4), stats):
        column.metric(label, f"{value:,}")
    st.caption(
        f"{summary['dataset_rows']:,} weekly observations · "
        f"{summary['campaigns']} campaigns · "
        f"{summary['weeks']} weeks. "
        f"Seed agreement: average Jaccard similarity "
        f"{summary['seed_jaccard_mean_vs_primary']:.3f} "
        "(same data, different random seeds)."
    )
    cover = pd.DataFrame([
        {"Review coverage": "Both rule and ML", "Weekly observations": summary["overlap_rule_and_ml"]},
        {"Review coverage": "Rule only", "Weekly observations": summary["rule_only"]},
        {"Review coverage": "ML only", "Weekly observations": summary["ml_only"]},
        {"Review coverage": "Neither", "Weekly observations": summary["neither"]},
    ])
    st.bar_chart(cover, x="Review coverage", y="Weekly observations")
    st.markdown("#### Model sensitivity")
    st.dataframe(result["sensitivity"].round(3), hide_index=True, use_container_width=True)
    st.caption(
        "The ML anomaly count is partly set by the contamination parameter. "
        "Flag count and agreement do not measure business value or correctness."
    )
    with st.expander("Inspect observation-level comparison"):
        columns = [
            "Week", "Campaign", "Spend", "Sales", "ACOS %",
            "Baseline screen", "Baseline priority review",
            "ML anomaly flag", "ML seed agreement %", "Review overlap",
        ]
        st.dataframe(
            result["observations"][columns].round(3),
            hide_index=True, use_container_width=True,
        )
    st.download_button(
        "Download reproducible evaluation ZIP",
        data=_as_zip(result),
        file_name="PPC_Campaign_Benchmark_Exploratory.zip",
        mime="application/zip",
        key="weekly_benchmark_export",
    )
    st.warning(
        "This benchmark cannot establish predictive accuracy or advertising "
        "improvement without independently labelled decisions and prospective tests. "
        "Do not republish downloaded data unless its licence permits it."
    )
