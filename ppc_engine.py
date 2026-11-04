"""PPC Intelligence Hub core: report cleaning, aggregation, decisions and export.

Extracted without changing the original algorithms, allowing a clean v3 UI.
This module has no application entrypoint or top-level Streamlit layout.
"""

from __future__ import annotations

import io
import re
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

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


