"""Independent moving PPC Buddy preview.

Deploy this file as a *separate Streamlit app* on the development branch if
the main PPC dashboard's UI makes it difficult to diagnose the robot.
All figures are fictional, and no account uploads are necessary.
"""
import streamlit as st

from ppc_buddy_component import render_buddy, buddy_message


st.set_page_config(
    page_title="Meet PPC Buddy | Devanandha VS",
    page_icon="🤖",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(130deg, #f5f6ff, #f7fbff);
    }
    .block-container {
        max-width: 1150px;
        padding-top: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.caption("DEVANANDHA VS · PPC INTELLIGENCE HUB / ANIMATED MASCOT PROTOTYPE")
st.title("Meet PPC Buddy 🤖")
st.write(
    "This is a separate **visual test page** for the moving robot. "
    "It uses fictional figures and has no access to Amazon accounts. "
    "The production PPC app is unaffected."
)

with st.expander("Change the fictional PPC scenario", expanded=False):
    target_acos = st.slider("Target ACOS (%)", 5, 80, 25)
    account_acos = st.slider("Observed ACOS (%)", 0, 100, 33)
    ad_sales = st.number_input(
        "Fictional attributed ad sales (£)", min_value=0, value=31580,
        step=500,
    )
    harvest = st.slider("Possible keyword harvest candidates", 0, 30, 7)
    negatives = st.slider("Negative review candidates", 0, 30, 3)
    animate = st.toggle("Animate PPC Buddy", value=True)

if "animate" not in locals():
    target_acos, account_acos, ad_sales = 25, 33, 31580
    harvest, negatives, animate = 7, 3, True

render_buddy(
    account_acos=account_acos,
    target_acos=target_acos,
    ad_sales=ad_sales,
    harvest_count=harvest,
    negative_count=negatives,
    demo_mode=True,
    animated=animate,
)

st.info(
    "Watch PPC Buddy float, blink and wave. The animation is CSS-based "
    "and will stop if your device has reduced-motion accessibility enabled."
)
st.markdown(
    "[Open PPC Intelligence Hub v2](https://devanandha-ppc-intelligence-v2.streamlit.app/)"
)
