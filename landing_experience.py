"""Premium product landing experience for Devanandha VS PPC Intelligence Hub.

Only trusted static HTML or escaped numeric values are interpolated. Controls
remain native Streamlit widgets. No images, fonts, trackers or network calls.
"""
from __future__ import annotations

import math
import streamlit as st

_PREMIUM_CSS = """
<style>
/* Distinct product styling; retain responsive, keyboard-accessible Streamlit controls. */
:root { --dv-ink:#101a30; --dv-blue:#635bff; --dv-cyan:#16c1d8; --dv-line:#e7ebf3; }
[data-testid="stAppViewContainer"] {background: #f7f9fd;}
[data-testid="stSidebar"] > div:first-child {
  background: #ffffff !important;
  border-right: 1px solid #e8edf6 !important;
}
[data-testid="stHeader"] {background: rgba(247,249,253,.9);}
.block-container {padding-top: 1.65rem; max-width: 1450px;}
[data-testid="stMetric"] {
  border:1px solid #e5ebf5;
  border-radius:18px;
  background: white;
  padding:20px 20px 19px;
  box-shadow:0 12px 28px rgba(27,44,76,.042);
  min-height:128px;
  transition: transform .2s ease, box-shadow .2s ease;
}
[data-testid="stMetric"]:hover {transform:translateY(-2px);box-shadow:0 16px 30px rgba(27,44,76,.075);}
[data-testid="stMetricValue"] {font-size:clamp(1.25rem,2vw,2rem);letter-spacing:-.055em;color:#17243a;}
[data-testid="stMetricLabel"] {color:#65768f;letter-spacing:.035em;text-transform:uppercase;font-size:.77rem;}
[data-testid="stTabs"] [role="tablist"] {
  border:1px solid #e8ebf3;
  background:white;
  box-shadow:0 5px 17px rgba(30,42,65,.035);
  padding:7px;gap:4px;border-radius:14px;
}
[data-testid="stTabs"] button[role="tab"] {font-size:.85rem;padding:10px 12px;border-radius:10px;}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background:#ebeaff;color:#4339c8;box-shadow:none;
}
[data-testid="stPlotlyChart"], [data-testid="stDataFrame"] {
  border:1px solid #e7ecf5;border-radius:16px;background:white;overflow:hidden;
}
[data-testid="stExpander"] {
  border:1px solid #e5ebf5;border-radius:14px;background:white;
}
.dv-landing {
  position:relative;
  border-radius:26px;
  padding:0;
  margin:0 0 22px;
  background:linear-gradient(113deg,#10182f 0%,#13264d 52%,#28347a 100%);
  overflow:hidden;
  box-shadow:0 25px 65px rgba(18,30,71,.15);
  color:#fff;
}
.dv-landing::before{
  content:"";position:absolute;inset:0;
  background:radial-gradient(ellipse at 97% 4%,rgba(139,112,255,.34),transparent 48%),
             radial-gradient(ellipse at 61% 95%,rgba(7,194,219,.17),transparent 46%);
  pointer-events:none;
}
.dv-grid {
  position:relative;z-index:1;
  display:grid;grid-template-columns:minmax(0,1.22fr) minmax(280px,.78fr);
  gap:30px;align-items:center;padding:33px 38px 31px;
}
.dv-brandline {
  display:flex;align-items:center;flex-wrap:wrap;gap:11px;
  font-size:.7rem;letter-spacing:.15em;text-transform:uppercase;
  color:#afbbe4;font-weight:800;margin-bottom:23px;
}
.dv-mark {
  width:36px;height:36px;display:inline-flex;align-items:center;justify-content:center;
  border-radius:11px;
  background:linear-gradient(140deg,#728dff,#54d7ef);
  box-shadow:0 7px 20px rgba(65,100,245,.35);
  color:white;font-size:.7rem;letter-spacing:.015em;font-weight:900;
}
.dv-flag {
  display:inline-flex;align-items:center;gap:6px;
  border:1px solid rgba(154,241,227,.25);
  background:rgba(38,185,181,.095);
  color:#a2f5e3;padding:5px 10px;border-radius:99px;font-weight:650;
  letter-spacing:.04em;text-transform:none;font-size:.68rem;
}
.dv-flag i {width:6px;height:6px;border-radius:99px;background:#4be7bf;display:inline-block;box-shadow:0 0 12px #4be7bf;}
.dv-landing h1{
  margin:0;color:white;font-size:clamp(2rem,3.5vw,3.35rem);
  line-height:1.08;letter-spacing:-.055em;font-weight:810;
  max-width:650px;
}
.dv-landing h1 .accent{color:#9dc5ff;}
.dv-landing .dv-desc {
  color:#bac9e1;line-height:1.72;font-size:.95rem;
  max-width:600px;margin:15px 0 20px;
}
.dv-tags{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 24px;}
.dv-tag{
  border:1px solid rgba(186,213,255,.22);
  background:rgba(255,255,255,.075);
  border-radius:9px;padding:7px 10px;color:#ecf3ff;
  font-size:.72rem;font-weight:700;
}
.dv-credit {display:flex;align-items:center;gap:8px;color:#9fb4d6;font-size:.79rem;}
.dv-credit strong{color:white;}
.dv-credit a{color:#8ee8ff;text-decoration:none;font-weight:750;}
.dv-credit a:hover{text-decoration:underline;}
.dv-visual{
  position:relative;
  min-height:264px;border:1px solid rgba(213,228,255,.17);
  border-radius:21px;
  background:linear-gradient(148deg,rgba(255,255,255,.1),rgba(255,255,255,.035));
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 26px 48px rgba(4,12,36,.24);
  padding:21px;
  backdrop-filter: blur(6px);
}
.dv-visual-top{display:flex;align-items:center;justify-content:space-between;gap:8px;}
.dv-visual-title{color:#e9f1ff;font-weight:780;font-size:.86rem;letter-spacing:.02em;}
.dv-visual-label{font-size:.64rem;font-weight:800;letter-spacing:.05em;color:#a9eadf;background:rgba(35,200,179,.13);padding:5px 9px;border:1px solid rgba(140,226,215,.21);border-radius:20px;}
.dv-visual svg{display:block;width:100%;height:auto;margin:5px 0 6px;}

.dv-signal-chart{margin:10px 0 13px;min-height:160px}
.dv-chart-guide{display:flex;align-items:center;justify-content:space-between;gap:10px;color:#b7c8e8;font-size:.65rem;font-weight:650;margin:12px 1px 8px}
.dv-chart-guide span:last-child{color:#859ecb;font-size:.6rem}
.dv-chart-area{
  height:112px;display:flex;gap:8px;align-items:flex-end;justify-content:space-between;
  position:relative;padding:8px 3px 1px;border-bottom:1px solid rgba(201,229,255,.18)
}
.dv-chart-grid{
  position:absolute;inset:8px 0 1px;pointer-events:none;
  background:repeating-linear-gradient(to bottom,
    transparent,transparent 24%,rgba(202,224,255,.11) 24.5%,transparent 25%);
}
.dv-bar-pair{display:flex;align-items:flex-end;gap:2px;height:100%;flex:1;position:relative;z-index:1}
.dv-bar{display:block;flex:1;min-width:3px;border-radius:4px 4px 0 0;opacity:.92}
.dv-bar-a{background:linear-gradient(to top,#4d68da,#a1a3ff)}
.dv-bar-b{background:linear-gradient(to top,#118da9,#53e4d1)}
.dv-chart-legend{display:flex;align-items:center;justify-content:flex-start;flex-wrap:wrap;gap:17px;margin:10px 3px 0}
.dv-chart-legend span{display:flex;align-items:center;gap:6px;color:#b9cbe9;font-size:.66rem}
.dv-chart-legend i{width:8px;height:8px;display:inline-block;border-radius:3px}
.dv-dot-a{background:#9195ff}
.dv-dot-b{background:#52e1cf}

.dv-visual-bottom{display:grid;grid-template-columns:1fr 1fr;gap:9px;}
.dv-mini{background:rgba(2,13,41,.3);padding:9px 11px;border:1px solid rgba(218,238,255,.11);border-radius:12px;}
.dv-mini small{display:block;color:#afc2db;font-size:.63rem;letter-spacing:.03em;}
.dv-mini strong{font-size:.86rem;color:#eaf7ff;}
.dv-strip {
  margin:9px 0 19px;display:flex;gap:13px;align-items:center;justify-content:space-between;
  flex-wrap:wrap;padding:13px 17px;border:1px solid #e2e9f5;background:#fff;
  border-radius:14px;box-shadow:0 8px 26px rgba(19,42,83,.025);
}
.dv-strip strong{font-size:.84rem;color:#1c3251;}
.dv-strip span{font-size:.79rem;color:#63758f;}
.dv-pill{
  display:inline-flex;align-items:center;gap:7px;border-radius:99px;
  padding:5px 10px;background:#e7f9f0;color:#176949;font-weight:750;font-size:.71rem;
}
.dv-pill:before{content:"";width:6px;height:6px;background:#20b57d;border-radius:50%;}
.dv-section{
  display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;
  margin:27px 0 14px;
}
.dv-section h2{font-size:1.38rem;letter-spacing:-.04em;color:#17233b;margin:0;}
.dv-section p{font-size:.86rem;color:#718098;margin:4px 0 0;}
.dv-section-eyebrow{font-size:.7rem;color:#685fe1;letter-spacing:.12em;font-weight:800;}
.dv-pulse{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:12px 0 22px;}
.dv-pulse-card{
  display:flex;justify-content:space-between;gap:12px;align-items:center;
  background:#fff;border:1px solid #e7ebf4;border-radius:16px;
  padding:17px 17px;box-shadow:0 8px 18px rgba(13,42,78,.03);
}
.dv-pulse-ico{width:41px;height:41px;display:flex;align-items:center;justify-content:center;border-radius:13px;font-size:1.2rem;}
.dv-pulse-ico.blue{background:#ebeaff;color:#554ff3;}
.dv-pulse-ico.teal{background:#e5f9f8;color:#079e9b;}
.dv-pulse-ico.amber{background:#fff2db;color:#b87c21;}
.dv-pulse-k{color:#64738a;font-size:.72rem;text-transform:uppercase;letter-spacing:.045em;font-weight:700;}
.dv-pulse-v{font-size:1.24rem;font-weight:830;color:#1c2944;line-height:1.2;letter-spacing:-.03em;}
.dv-pulse-caption{color:#8a95a8;font-size:.72rem;max-width:170px;text-align:right;}
@media(max-width:940px){
  .dv-grid{grid-template-columns:1fr;padding:28px;}
  .dv-visual{min-height:220px;max-width:580px;}
  .dv-pulse{grid-template-columns:1fr;}
}
@media(max-width:580px){
  .dv-landing{border-radius:19px;}
  .dv-grid{padding:23px 20px;gap:20px;}
  .dv-landing h1{font-size:2.1rem;}
  .dv-visual{display:none;}
  .dv-flag{font-size:.62rem;}
  .dv-strip{align-items:flex-start;}
  .dv-credit{flex-wrap:wrap;}
}
</style>
"""

_HERO = """
<section class="dv-landing" aria-label="Amazon PPC Intelligence Hub product overview">
  <div class="dv-grid">
    <div>
      <div class="dv-brandline">
        <span class="dv-mark" aria-hidden="true">DVS</span>
        <span>Devanandha VS / Applied AI Studio</span>
        <span class="dv-flag"><i></i> Experimental AI</span>
      </div>
      <h1>Make every advertising<br><span class="accent">decision defensible.</span></h1>
      <p class="dv-desc">
        Amazon PPC Intelligence Hub unifies campaign analytics, explainable recommendations,
        machine-learning pattern review and evidence-aware decision safeguards—
        all in one independent analysis workspace.
      </p>
      <div class="dv-tags">
        <span class="dv-tag">Sponsored Products</span>
        <span class="dv-tag">Decision Assurance</span>
        <span class="dv-tag">AI-assisted Review</span>
        <span class="dv-tag">Scenario Lab</span>
      </div>
      <div class="dv-credit">
        <span>Independently developed by <strong>Devanandha Vellaramkuzhiyil Shaji</strong></span>
        <a href="https://www.linkedin.com/in/devanandhavs21" target="_blank" rel="noopener noreferrer">Profile ↗</a>
      </div>
    </div>
    <div class="dv-visual" aria-label="Decorative visualisation of an evidence-review workflow">
      <div class="dv-visual-top">
        <span class="dv-visual-title">DECISION INTELLIGENCE</span>
        <span class="dv-visual-label">HUMAN IN CONTROL</span>
      </div>
      <div class="dv-signal-chart" role="img" aria-label="Decorative chart of fictional advertising signals. Not actual account measurements.">
        <div class="dv-chart-guide"><span>Illustrative signals</span><span>Relative patterns · not real data</span></div>
        <div class="dv-chart-area">
          <div class="dv-chart-grid"></div>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:24%"></i><i class="dv-bar dv-bar-b" style="height:45%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:36%"></i><i class="dv-bar dv-bar-b" style="height:40%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:30%"></i><i class="dv-bar dv-bar-b" style="height:54%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:48%"></i><i class="dv-bar dv-bar-b" style="height:58%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:43%"></i><i class="dv-bar dv-bar-b" style="height:49%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:64%"></i><i class="dv-bar dv-bar-b" style="height:72%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:55%"></i><i class="dv-bar dv-bar-b" style="height:70%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:70%"></i><i class="dv-bar dv-bar-b" style="height:64%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:66%"></i><i class="dv-bar dv-bar-b" style="height:80%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:82%"></i><i class="dv-bar dv-bar-b" style="height:74%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:76%"></i><i class="dv-bar dv-bar-b" style="height:95%"></i></span>
          <span class="dv-bar-pair" aria-hidden="true"><i class="dv-bar dv-bar-a" style="height:96%"></i><i class="dv-bar dv-bar-b" style="height:87%"></i></span>
        </div>
        <div class="dv-chart-legend"><span><i class="dv-dot-a"></i>Observed pattern</span><span><i class="dv-dot-b"></i>Review signal</span></div>
      </div>
      <div class="dv-visual-bottom">
        <div class="dv-mini"><small>01 / OBSERVE</small><strong>Campaign signals</strong></div>
        <div class="dv-mini"><small>02 / VERIFY</small><strong>Evidence gates</strong></div>
      </div>
    </div>
  </div>
</section>
"""


def inject_experience_styles() -> None:
    st.html(_PREMIUM_CSS)


def render_landing() -> None:
    st.html(_HERO)


def render_data_context(*, demo_mode: bool) -> None:
    if demo_mode:
        st.html(
            '<div class="dv-strip"><div><strong>Fictional demo workspace</strong>'
            ' <span> · Instantly explore the product using generated advertising data.</span></div>'
            '<span class="dv-pill">SYNTHETIC DATA</span></div>'
        )
    else:
        st.html(
            '<div class="dv-strip"><div><strong>Uploaded-report workspace</strong>'
            ' <span> · Your own report is active. Keep account data confidential.</span></div>'
            '<span class="dv-pill">PRIVATE SESSION</span></div>'
        )


def render_section(title: str, description: str, eyebrow: str = "WORKSPACE") -> None:
    from html import escape
    st.html(
        f'<div class="dv-section"><div>'
        f'<div class="dv-section-eyebrow">{escape(eyebrow)}</div>'
        f'<h2>{escape(title)}</h2><p>{escape(description)}</p>'
        f'</div></div>'
    )


def render_action_pulse(harvest_count: int, negative_count: int, waste_rate: float) -> None:
    # Only Python-derived counts are inserted; no uploaded strings in markup.
    n_harvest = max(0, int(harvest_count))
    n_negative = max(0, int(negative_count))
    rate = float(waste_rate)
    if not math.isfinite(rate):
        rate = 0.0
    st.html(
        f'<div class="dv-pulse">'
        f'<div class="dv-pulse-card"><div><div class="dv-pulse-k">Harvest candidates</div>'
        f'<div class="dv-pulse-v">{n_harvest:,}</div></div>'
        f'<div class="dv-pulse-ico blue">↗</div></div>'
        f'<div class="dv-pulse-card"><div><div class="dv-pulse-k">Negative review candidates</div>'
        f'<div class="dv-pulse-v">{n_negative:,}</div></div>'
        f'<div class="dv-pulse-ico amber">◎</div></div>'
        f'<div class="dv-pulse-card"><div><div class="dv-pulse-k">Zero-order spend share*</div>'
        f'<div class="dv-pulse-v">{rate:.1f}%</div></div>'
        f'<div class="dv-pulse-ico teal">◈</div></div>'
        f'</div>'
    )
