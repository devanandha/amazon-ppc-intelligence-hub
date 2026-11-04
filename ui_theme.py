"""Presentation helpers for the PPC Intelligence Hub.

Uses static, trusted HTML/CSS only. Report values remain in native Streamlit
widgets, not unsanitized HTML.
"""

import streamlit as st


_STYLES = """
<style>
:root {
  --ppc-navy: #111c35;
  --ppc-ink: #17253d;
  --ppc-muted: #61718b;
  --ppc-line: #e4ebf5;
  --ppc-blue: #4068e8;
  --ppc-cyan: #37c5ea;
}
[data-testid="stAppViewContainer"] {
  background: #f5f7fc;
}
[data-testid="stHeader"] {
  background: rgba(245, 247, 252, 0.92);
}
[data-testid="stSidebar"] > div:first-child {
  background: #eef3fb;
  border-right: 1px solid #dce6f4;
}
.block-container {
  max-width: 1500px;
  padding-top: 2.3rem;
  padding-bottom: 3.5rem;
}
h1, h2, h3, h4, p, label {
  letter-spacing: -0.015em;
}
h2, h3 { color: #17253d; }
[data-testid="stMetric"] {
  background: #ffffff;
  border: 1px solid #e4ebf5;
  border-radius: 17px;
  padding: 18px 20px;
  box-shadow: 0 7px 22px rgba(24, 50, 90, 0.045);
  min-height: 118px;
}
[data-testid="stMetricLabel"] {
  font-weight: 600;
  color: #61718b;
}
[data-testid="stMetricValue"] {
  font-weight: 760;
  color: #17253d;
  letter-spacing: -0.045em;
}
[data-testid="stTabs"] [role="tablist"] {
  gap: 7px;
  background: #eaf0f9;
  border-radius: 12px;
  padding: 6px 7px;
}
[data-testid="stTabs"] button[role="tab"] {
  border-radius: 9px;
  padding: 9px 17px;
  font-weight: 650;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background: #ffffff;
  box-shadow: 0 3px 10px rgba(14, 34, 70, 0.09);
}
[data-testid="stFileUploader"] {
  background: #fff;
  border: 1px solid #e4ebf5;
  padding: 8px 12px 14px;
  border-radius: 16px;
}
[data-testid="stDataFrame"], [data-testid="stPlotlyChart"] {
  border-radius: 15px;
  overflow: hidden;
}
[data-testid="stButton"] button[kind="primary"],
[data-testid="stDownloadButton"] button[kind="primary"] {
  background: #3159dc;
  border-radius: 10px;
  border: 1px solid #3159dc;
  font-weight: 650;
}
.ppc-hero {
  position: relative;
  overflow: hidden;
  border-radius: 23px;
  padding: 31px 35px 29px;
  background: linear-gradient(117deg, #101b34 0%, #1b2f57 59%, #1e4b83 100%);
  box-shadow: 0 20px 38px rgba(20, 39, 77, 0.16);
  color: #fff;
  margin: 0 0 27px;
}
.ppc-hero::after {
  content: "";
  position: absolute;
  width: 380px;
  height: 380px;
  right: -125px;
  top: -185px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(52, 203, 233, .32), rgba(52, 203, 233, 0) 67%);
  pointer-events: none;
}
.ppc-hero .eyebrow {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 9px;
  margin-bottom: 15px;
  font-size: .73rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: .16em;
  color: #92e4fa;
}
.ppc-hero h1 {
  position: relative;
  z-index: 1;
  color: #ffffff;
  margin: 0 0 12px;
  font-size: clamp(1.95rem, 3.1vw, 2.8rem);
  letter-spacing: -.045em;
  font-weight: 790;
  line-height: 1.15;
}
.ppc-hero p {
  position: relative;
  z-index: 1;
  color: #c4d2e9;
  max-width: 760px;
  font-size: 1.02rem;
  margin: 0 0 19px;
  line-height: 1.6;
}
.ppc-tags {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.ppc-tag {
  background: rgba(255,255,255,.1);
  border: 1px solid rgba(184,222,254,.23);
  color: #e6f4ff;
  font-size: .73rem;
  font-weight: 650;
  padding: 7px 11px;
  border-radius: 99px;
}
.ppc-empty {
  background: #ffffff;
  border: 1px solid var(--ppc-line);
  border-radius: 19px;
  padding: 24px 28px;
  margin-top: 20px;
}
.ppc-empty h3 { margin: 0 0 15px; font-size: 1.1rem; }
.ppc-steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 15px;
}
.ppc-step {
  border: 1px solid #e6ecf5;
  background: #f8faff;
  border-radius: 13px;
  padding: 17px;
}
.ppc-step strong { display: block; color: #182b4d; margin-bottom: 6px; }
.ppc-step p { color: #64738b; font-size: .84rem; line-height: 1.5; margin: 0; }
.ppc-step-num {
  color: #3159dc;
  font-weight: 850;
  font-size: .73rem;
  letter-spacing: .09em;
  display: block;
  margin-bottom: 9px;
}
@media (max-width: 740px) {
  .ppc-hero { padding: 24px 22px; border-radius: 17px; }
  .ppc-steps { grid-template-columns: 1fr; }
  [data-testid="stMetric"] { min-height: 104px; padding: 13px; }
}
</style>
"""


def inject_styles() -> None:
    st.html(_STYLES)


def render_hero() -> None:
    st.html(
        """
        <section class="ppc-hero" aria-label="Amazon PPC Intelligence Hub">
          <div class="eyebrow">◆  DEVANANDHA VS / APPLIED AI &amp; ECOMMERCE</div>
          <h1>Amazon PPC Intelligence Hub</h1>
          <p>Go beyond dashboard metrics. Inspect campaign health, find
             search-term opportunities and understand the evidence behind
             every suggested action.</p>
          <div class="ppc-tags">
            <span class="ppc-tag">Sponsored Products</span>
            <span class="ppc-tag">Explainable recommendations</span>
            <span class="ppc-tag">Explainable rules + ML-assisted review</span>
            <span class="ppc-tag">Excel-ready insights</span>
          </div>
          <div style="position:relative;z-index:1;margin-top:20px;color:#d7e5ff;font-size:.87rem">
            Independently developed by <strong>Devanandha Vellaramkuzhiyil Shaji</strong>
            &nbsp;·&nbsp;
            <a href="https://www.linkedin.com/in/devanandhavs21" style="color:#8ee4ff;text-decoration:none">Developer profile ↗</a>
          </div>
        </section>
        """
    )


def render_empty_state() -> None:
    st.html(
        """
        <section class="ppc-empty" aria-label="Getting started">
          <h3>Your decision workspace is ready</h3>
          <div class="ppc-steps">
            <div class="ppc-step">
              <span class="ppc-step-num">STEP 01</span>
              <strong>Upload a search-term report</strong>
              <p>Use an Amazon Sponsored Products export. Synthetic data is
                 recommended for public demonstrations.</p>
            </div>
            <div class="ppc-step">
              <span class="ppc-step-num">STEP 02</span>
              <strong>Set your decision thresholds</strong>
              <p>Adjust target ACOS, click evidence and minimum orders in
                 the settings panel.</p>
            </div>
            <div class="ppc-step">
              <span class="ppc-step-num">STEP 03</span>
              <strong>Explore &amp; compare scenarios</strong>
              <p>Inspect recommendations, test sensitivity to ACOS targets,
                 and export a transparent action report.</p>
            </div>
          </div>
        </section>
        """
    )



def render_sidebar_brand() -> None:
    st.html(
        """
        <section aria-label="Developer identity" style="
          border-radius:17px;padding:19px 17px 18px;margin-bottom:23px;
          color:white;background:linear-gradient(135deg,#121d3b,#2a3478);
          box-shadow:0 15px 30px rgba(15,30,66,.11);">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:13px">
            <span style="display:flex;align-items:center;justify-content:center;
                         width:36px;height:36px;border-radius:11px;
                         font-size:.72rem;font-weight:900;background:#6b6afa;color:white">DVS</span>
            <div>
              <div style="font-weight:850;font-size:.83rem;letter-spacing:.025em">DEVANANDHA VS</div>
              <div style="color:#a2b6e7;font-size:.68rem;letter-spacing:.06em">PPC INTELLIGENCE / V2</div>
            </div>
          </div>
          <div style="font-size:1.12rem;line-height:1.25;font-weight:790;letter-spacing:-.04em">
            Your decision<br>intelligence workspace.
          </div>
          <div style="margin-top:12px;color:#b9d0f2;font-size:.76rem;line-height:1.5">
            Transparent analytics, experimental AI and human-reviewed recommendations.
          </div>
        </section>
        """
    )


def render_footer() -> None:
    st.html("""<footer style="border-top:1px solid #dfe7f2;padding:22px 0 8px;margin-top:30px;font-size:.83rem;color:#63728a">
    Amazon PPC Intelligence Hub · Independently developed by Devanandha Vellaramkuzhiyil Shaji ·
    <a href="https://github.com/devanandha/amazon-ppc-intelligence-hub">Source code</a> ·
    Not affiliated with or endorsed by Amazon. All recommendations require human review.
    </footer>""")
