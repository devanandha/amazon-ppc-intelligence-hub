"""Self-contained, XSS-safe HTML decision-evidence report.

This is a user-initiated local download. It includes selected search-term data
and must NOT be redistributed without the relevant account owner's approval.
"""
from __future__ import annotations

from html import escape
import math

import pandas as pd

TERM = "Customer Search Term"


def _safe_text(value: object) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "Not available"
    return escape(str(value), quote=True)


def create_evidence_report(
    audit: pd.DataFrame,
    *,
    target_acos: float,
    synthetic_demo: bool,
    max_rows: int = 200,
) -> bytes:
    """Return a styled, self-contained, read-only HTML review report."""
    if max_rows < 1:
        raise ValueError("max_rows must be positive.")
    needed = {
        TERM, "Recommended Action", "Evidence status",
        "Evidence justification", "ML review flag",
        "High-impact baseline action",
    }
    if not needed.issubset(audit.columns):
        raise ValueError(f"Missing audit columns: {sorted(needed - set(audit.columns))}")
    count = len(audit)
    high = int(audit["High-impact baseline action"].sum())
    escalated = int((
        audit["High-impact baseline action"]
        & audit["Evidence status"].ne("Manual review ready")
    ).sum())
    flagged = int(audit["ML review flag"].eq("Unusual pattern — review").sum())
    rows = []
    for _, row in audit.head(max_rows).iterrows():
        cells = [
            row[TERM], row["Recommended Action"], row["Evidence status"],
            row["Evidence justification"], row["ML review flag"],
        ]
        rows.append("<tr>" + "".join(
            f"<td>{_safe_text(v)}</td>" for v in cells
        ) + "</tr>")
    origin = "FICTIONAL SYNTHETIC DEMO" if synthetic_demo else "USER-UPLOADED ACCOUNT REPORT"
    confidentiality = (
        "Synthetic illustrative data; no genuine account performance is claimed."
        if synthetic_demo
        else "Contains account-specific search terms and performance details. "
             "Treat as confidential and share only with explicit permission."
    )
    html = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Decision Assurance | Devanandha VS</title>
<style>
:root{--navy:#101e38;--blue:#3972e9;--ink:#1a2944;--line:#e0e8f3}
*{box-sizing:border-box}
body{margin:0;background:#f4f7fc;color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
.wrap{max-width:1150px;margin:0 auto;padding:26px 25px 60px}
.hero{border-radius:22px;background:linear-gradient(115deg,#0d1930,#254f8a);padding:30px 35px;color:white}
.hero small{color:#9adbf7;letter-spacing:.14em;font-weight:800;text-transform:uppercase}
.hero h1{font-size:2rem;letter-spacing:-.035em;margin:9px 0}
.hero p{margin:4px 0;color:#d4e1f3}
.author{margin-top:17px;font-weight:650;font-size:.86rem}
.boxes{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:21px 0}
.metric{background:#fff;border:1px solid var(--line);border-radius:15px;padding:18px}
.metric .n{display:block;font-size:1.9rem;font-weight:750;color:#183158}
.metric small{color:#69768d}
.panel{background:white;border:1px solid var(--line);border-radius:15px;padding:21px;margin-top:16px}
h2{margin:0 0 13px;font-size:1.2rem}
table{width:100%;border-collapse:collapse;font-size:.84rem}
th,td{padding:10px 9px;border-bottom:1px solid #e6edf5;text-align:left;vertical-align:top}
th{background:#e9f0fa;color:#27436d}
.scroll{overflow-x:auto}
.note{border-left:4px solid #3972e9;background:#f0f5fe;border-radius:7px;padding:13px;margin:12px 0}
footer{color:#738198;font-size:.82rem;margin-top:24px}
@media(max-width:700px){.boxes{grid-template-columns:repeat(2,1fr)}.hero{padding:23px}.wrap{padding:12px}}
</style>
</head>
<body><div class="wrap">
<section class="hero">
<small>Devanandha VS · Applied AI &amp; Advertising Analytics</small>
<h1>Decision Assurance Report</h1>
<p>Amazon PPC Intelligence Hub | Explainable rules, uncertainty and exploratory ML signals</p>
<div class="author">Independently developed by Devanandha Vellaramkuzhiyil Shaji</div>
</section>
<div class="boxes">
<div class="metric"><span class="n">__COUNT__</span><small>Terms analysed</small></div>
<div class="metric"><span class="n">__HIGH__</span><small>High-impact rule suggestions</small></div>
<div class="metric"><span class="n">__ESCALATED__</span><small>High-impact cases needing review</small></div>
<div class="metric"><span class="n">__FLAGGED__</span><small>ML unusual-pattern flags</small></div>
</div>
<section class="panel">
<h2>Review context</h2>
<p><b>Data source:</b> __SOURCE__ &nbsp; | &nbsp; <b>Configured target ACOS:</b> __ACOS__%</p>
<div class="note">__CONFIDENTIALITY__</div>
<p>This prototype does not approve or execute campaign changes. Anomaly status is not a
probability of fraud, unprofitability or advertising uplift. Conversion intervals
are model-dependent and may be invalid for some attribution arrangements.</p>
</section>
<section class="panel">
<h2>Evidence ledger</h2>
<p>Showing up to __LIMIT__ rows, in the order supplied by the application.</p>
<div class="scroll"><table>
<thead><tr><th>Search term</th><th>Original rule</th><th>Review state</th>
<th>Evidence explanation</th><th>ML screen</th></tr></thead>
<tbody>__ROWS__</tbody></table></div>
</section>
<section class="panel">
<h2>Method and limitations</h2>
<p><b>Rules:</b> explicit target ACOS, clicks, orders and bid-adjustment thresholds.
<b>Statistical evidence:</b> approximate 90% Jeffreys-binomial credible
intervals on orders per click where applicable.
<b>Machine learning:</b> in-dataset Isolation Forest screening, not an externally validated
forecasting or optimisation model.
<b>Assurance:</b> transparent additional human-review gates based on observations,
uncertainty and unusual patterns. This report does not establish predictive accuracy,
revenue uplift, independent adoption or technology-sector recognition.</p>
<p><a href="https://github.com/devanandha/amazon-ppc-intelligence-hub">View project source</a></p>
</section>
<footer>Devanandha VS · Independent prototype · Not affiliated with or endorsed by Amazon</footer>
</div></body></html>"""
    replacements = {
        "__COUNT__": str(count), "__HIGH__": str(high),
        "__ESCALATED__": str(escalated), "__FLAGGED__": str(flagged),
        "__SOURCE__": _safe_text(origin), "__ACOS__": _safe_text(round(target_acos, 2)),
        "__CONFIDENTIALITY__": _safe_text(confidentiality),
        "__LIMIT__": str(min(max_rows, count)), "__ROWS__": "\n".join(rows),
    }
    for old, value in replacements.items():
        html = html.replace(old, value)
    return html.encode("utf-8")
