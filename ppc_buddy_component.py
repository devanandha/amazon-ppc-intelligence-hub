"""Visible, animated PPC Buddy for Streamlit dashboards.

Uses a self-contained Streamlit components HTML iframe so its CSS animation is
not affected by st.html sanitisation. No external assets, script, AI API, or
uploaded report text is used. Its guidance comes from transparent metrics.
"""
from __future__ import annotations

from html import escape
import math

import streamlit.components.v1 as components


def buddy_message(
    *, account_acos: float, target_acos: float, ad_sales: float
) -> str:
    """Give a careful, human-reviewed interpretation of observed account ACOS."""
    acos = float(account_acos)
    target = float(target_acos)
    sales = float(ad_sales)
    if sales <= 0 or not math.isfinite(sales) or not math.isfinite(acos):
        return (
            "No attributed ad sales are available for a meaningful account "
            "ACOS comparison yet. Let's check the underlying evidence."
        )
    if target <= 0 or not math.isfinite(target):
        return "Set a valid target ACOS before interpreting account efficiency."
    gap = abs(acos - target)
    if acos > target:
        return (
            f"Observed ACOS is {gap:.1f} percentage points above your target. "
            "Let's examine individual search terms before considering bid changes."
        )
    return (
        f"Observed ACOS is {gap:.1f} percentage points below your target. "
        "Let's check evidence quality before scaling successful terms."
    )


def buddy_html(
    *, account_acos: float, target_acos: float, ad_sales: float,
    harvest_count: int, negative_count: int,
    demo_mode: bool, animated: bool = True,
) -> str:
    """Build a standalone, responsive robot display; output does not include user text."""
    message = escape(
        buddy_message(
            account_acos=account_acos,
            target_acos=target_acos,
            ad_sales=ad_sales,
        )
    )
    source = "FICTIONAL DEMO" if demo_mode else "YOUR UPLOADED REPORT"
    harvest = max(0, int(harvest_count))
    negative = max(0, int(negative_count))
    motion = "motion-on" if animated else "motion-off"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{{color-scheme:light}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;min-height:100%;background:transparent;
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Arial,sans-serif}}
.panel{{width:100%;min-height:272px;padding:21px 30px;overflow:hidden;position:relative;
  border-radius:22px;border:1px solid #dfe5f8;
  display:grid;grid-template-columns:178px minmax(0,1fr);
  gap:28px;align-items:center;
  background:linear-gradient(111deg,#ecf0ff 1%,#f7faff 49%,#e8fbff 100%);
  box-shadow:0 12px 32px rgba(26,48,100,.055)}}
.panel:before{{content:"";position:absolute;right:-115px;top:-170px;width:390px;height:390px;
  border-radius:50%;background:rgba(114,109,255,.055)}}
.stage{{position:relative;height:205px;display:flex;align-items:center;justify-content:center}}
.halo{{position:absolute;width:165px;height:165px;border-radius:50%;
  background:radial-gradient(circle,#bdc7ff 0%,#dce8ff 43%,transparent 70%);
  animation:haloGlow 4s ease-in-out infinite}}
.shadow{{position:absolute;bottom:3px;left:50%;transform:translateX(-50%);
  width:90px;height:13px;border-radius:50%;background:rgba(49,66,128,.13);
  filter:blur(4px);animation:shadowPulse 3.4s ease-in-out infinite}}
.robot{{position:relative;width:124px;height:169px;z-index:2;
  animation:floatBot 3.4s ease-in-out infinite;transform-origin:50% 90%}}
.antenna{{position:absolute;z-index:1;width:7px;height:27px;top:0;left:59px;
  border-radius:7px;background:#5e6fc9}}
.antenna:before{{content:"";position:absolute;width:16px;height:16px;left:-5px;top:-10px;
  border:3px solid #fff;border-radius:50%;background:#69e5d7;
  box-shadow:0 0 0 2px #6e80df,0 0 20px 5px rgba(75,235,216,.38);
  animation:antennaGlow 2.5s ease-in-out infinite}}
.ear{{position:absolute;top:53px;width:17px;height:31px;
  border:3px solid #6479d2;background:#9bb4ff;border-radius:10px}}
.ear.left{{left:5px}}.ear.right{{right:5px}}
.head{{position:absolute;z-index:4;top:24px;left:18px;width:89px;height:83px;
  border:4px solid #6979cb;border-radius:27px;
  background:linear-gradient(130deg,#fff,#d8e5ff);
  box-shadow:inset 0 8px 10px rgba(255,255,255,.9),0 8px 17px rgba(67,82,150,.18)}}
.face{{position:absolute;left:10px;right:10px;top:14px;height:46px;
  border-radius:18px;background:linear-gradient(140deg,#172755,#344984);
  box-shadow:inset 0 3px 7px rgba(0,0,0,.22)}}
.eye{{position:absolute;top:12px;width:13px;height:15px;
  border-radius:50%;background:#94fff4;box-shadow:0 0 11px rgba(75,246,237,.62);
  animation:blink 5.4s ease-in-out infinite}}
.eye.left{{left:13px}}.eye.right{{right:13px;animation-delay:.03s}}
.mouth{{position:absolute;left:calc(50% - 7px);top:28px;width:14px;height:8px;
  border-bottom:3px solid #80efe5;border-radius:0 0 13px 13px}}
.cheek{{position:absolute;top:59px;width:13px;height:7px;background:#ffb3d6;border-radius:50%;opacity:.86}}
.cheek.left{{left:11px}}.cheek.right{{right:11px}}
.arm{{position:absolute;top:113px;width:18px;height:38px;
  border:3px solid #657bd3;border-radius:12px;background:#d9e9ff}}
.arm.left{{left:10px;transform:rotate(19deg)}}
.arm.right{{right:8px;z-index:5;transform-origin:40% 18%;animation:wave 1.9s ease-in-out infinite}}
.torso{{position:absolute;left:31px;top:102px;width:64px;height:57px;z-index:3;
  border:4px solid #6979cb;border-radius:19px 19px 25px 25px;
  background:linear-gradient(140deg,#ecf6ff,#b9ccff);
  box-shadow:0 9px 15px rgba(84,105,174,.12)}}
.heart{{position:absolute;left:21px;top:17px;width:15px;height:15px;border-radius:6px;
  background:#59d9c9;box-shadow:0 0 0 5px rgba(88,220,201,.19);
  animation:heartBeat 2.2s ease-in-out infinite}}
.spark{{position:absolute;z-index:3;width:10px;height:10px;
  background:#7f78ec;clip-path:polygon(50% 0,62% 37%,100% 50%,62% 63%,50% 100%,38% 63%,0 50%,38% 37%);
  animation:sparkle 3s ease-in-out infinite}}
.spark.one{{top:28px;left:14px}}.spark.two{{top:18px;right:14px;animation-delay:1.4s;background:#31bcb0}}
.copy{{position:relative;z-index:2;min-width:0}}
.eyebrow{{font-size:10px;font-weight:900;letter-spacing:.16em;color:#625bc8;margin-bottom:7px}}
h2{{font-size:clamp(20px,2.1vw,29px);color:#202d50;letter-spacing:-.045em;margin:0 0 9px;line-height:1.2}}
h2 span{{color:#6e62e6}}
p{{margin:0;color:#4b6182;font-size:14px;line-height:1.65;max-width:740px}}
.pills{{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0 10px}}
.pill{{background:#fff;border:1px solid #dce6f8;border-radius:100px;
  padding:7px 11px;color:#395073;font-size:11px;font-weight:730}}
.source{{color:#5362ac;font-size:10px;font-weight:800;letter-spacing:.09em}}
.foot{{margin-top:7px;font-size:10px;color:#7989a0;line-height:1.4}}
@keyframes floatBot{{0%,100%{{transform:translateY(0) rotate(-1deg)}}50%{{transform:translateY(-11px) rotate(2deg)}}}}
@keyframes wave{{0%,100%{{transform:rotate(-25deg)}}35%{{transform:rotate(-73deg)}}70%{{transform:rotate(-36deg)}}}}
@keyframes blink{{0%,41%,45%,100%{{transform:scaleY(1)}}43%{{transform:scaleY(.12)}}}}
@keyframes haloGlow{{0%,100%{{opacity:.72;transform:scale(.98)}}50%{{opacity:1;transform:scale(1.08)}}}}
@keyframes shadowPulse{{0%,100%{{opacity:.7;transform:translateX(-50%) scaleX(1)}}50%{{opacity:.4;transform:translateX(-50%) scaleX(.78)}}}}
@keyframes antennaGlow{{0%,100%{{box-shadow:0 0 0 2px #6e80df,0 0 12px rgba(75,235,216,.35)}}50%{{box-shadow:0 0 0 2px #6e80df,0 0 23px 5px rgba(75,235,216,.66)}}}}
@keyframes heartBeat{{0%,100%{{transform:scale(1)}}45%{{transform:scale(1.14)}}}}
@keyframes sparkle{{0%,100%{{opacity:.2;transform:scale(.8) rotate(0)}}50%{{opacity:1;transform:scale(1.2) rotate(90deg)}}}}
.motion-off *, .motion-off *:before, .motion-off *:after{{animation:none !important}}
@media(prefers-reduced-motion:reduce){{
  *,*:before,*:after{{animation:none !important}}
}}
@media(max-width:600px){{
  .panel{{padding:15px;grid-template-columns:100px minmax(0,1fr);gap:10px;min-height:250px}}
  .stage{{transform:scale(.75);transform-origin:left center;width:132px;margin-right:-33px}}
  h2{{font-size:18px}}p{{font-size:12px}}.pills{{gap:5px}}.pill{{font-size:10px;padding:5px 7px}}
}}
</style>
</head>
<body>
<section class="panel {motion}" aria-label="PPC Buddy evidence companion">
  <div class="stage" aria-hidden="true">
    <div class="halo"></div><div class="shadow"></div>
    <div class="spark one"></div><div class="spark two"></div>
    <div class="robot">
      <div class="antenna"></div><div class="ear left"></div><div class="ear right"></div>
      <div class="head"><div class="face"><span class="eye left"></span>
      <span class="eye right"></span><span class="mouth"></span></div>
      <div class="cheek left"></div><div class="cheek right"></div></div>
      <div class="arm left"></div><div class="arm right"></div>
      <div class="torso"><div class="heart"></div></div>
    </div>
  </div>
  <div class="copy">
    <div class="eyebrow">DEVANANDHA VS / YOUR PPC COMPANION</div>
    <h2><span>Hi! 👋</span> I'm PPC Buddy.</h2>
    <p>{message}</p>
    <div class="pills">
      <span class="pill">↗ {harvest:,} harvest candidates</span>
      <span class="pill">◎ {negative:,} negative-review candidates</span>
    </div>
    <div class="source">{source}</div>
    <div class="foot">Animated demo companion. Summaries are rule-based, not a generative AI chatbot or automatic bidding advice.</div>
  </div>
</section>
</body></html>"""


def render_buddy(
    *, account_acos: float, target_acos: float, ad_sales: float,
    harvest_count: int, negative_count: int,
    demo_mode: bool, animated: bool = True,
) -> None:
    """Render in an isolated HTML iframe with guaranteed widget height."""
    components.html(
        buddy_html(
            account_acos=account_acos,
            target_acos=target_acos,
            ad_sales=ad_sales,
            harvest_count=harvest_count,
            negative_count=negative_count,
            demo_mode=demo_mode,
            animated=animated,
        ),
        height=293,
        scrolling=False,
    )
