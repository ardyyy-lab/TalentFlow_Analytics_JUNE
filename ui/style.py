"""Look and feel: page style, banner and sidebar."""
import streamlit as st

from . import auth, profile

CSS = """
<style>
/* ---- page ---------------------------------------------------------------- */
.block-container{max-width:1600px;padding-top:1.2rem;padding-bottom:3rem}
h1,h2,h3,h4{letter-spacing:-.01em}
h3{margin-top:.4rem}
hr{margin:1.2rem 0}

/* ---- banner ---------------------------------------------------------------- */
.tf-banner{background:linear-gradient(120deg,#0f2d3a 0%,#164a5a 60%,#0e7a8c 100%);color:#fff;
    padding:24px 32px;border-radius:16px;margin-bottom:14px;display:flex;align-items:center;
    justify-content:space-between;gap:24px;flex-wrap:wrap}
.tf-banner h1{color:#fff;font-size:2rem;margin:0 0 4px 0;padding:0;line-height:1.15}
.tf-banner p{color:#c3d6df;margin:0;font-size:1rem}
.tf-chips{display:flex;gap:8px;flex-wrap:wrap}
.tf-chip{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.28);color:#fff;
    padding:5px 12px;border-radius:999px;font-size:.8rem;font-weight:600;white-space:nowrap}

/* ---- answer card ------------------------------------------------------------ */
.tf-hero{background:linear-gradient(120deg,#0e7a8c 0%,#0b5565 100%);color:#fff;border-radius:16px;
    padding:22px 28px;margin:6px 0 18px}
.tf-hero .lab{font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;opacity:.85;font-weight:700}
.tf-hero .main{font-size:1.9rem;font-weight:700;line-height:1.25;margin:6px 0 4px}
.tf-hero .sub{font-size:1.02rem;opacity:.95}

/* ---- metric cards: wide, never cut off --------------------------------------- */
div[data-testid="stMetric"]{background:rgba(14,122,140,.07);border:1px solid rgba(14,122,140,.22);
    border-left:4px solid #0e7a8c;border-radius:12px;padding:14px 18px;height:100%}
div[data-testid="stMetricValue"]{font-size:1.6rem;line-height:1.25}
div[data-testid="stMetricValue"] > div,div[data-testid="stMetricLabel"] p,
div[data-testid="stMetricDelta"] > div{white-space:normal !important;overflow:visible !important;
    text-overflow:clip !important;overflow-wrap:anywhere}
div[data-testid="stMetricLabel"] p{font-size:.86rem;font-weight:600}

/* ---- tabs ---------------------------------------------------------------------- */
button[data-baseweb="tab"]{font-weight:600;font-size:.98rem;padding:10px 16px}
div[data-baseweb="tab-list"]{gap:2px}

/* ---- bordered boxes, inputs, tables ------------------------------------------- */
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px}
div[data-testid="stNumberInput"] input,div[data-testid="stSelectbox"] div[data-baseweb="select"]{font-size:1rem}
div[data-testid="stDataFrame"]{border-radius:10px}
div[data-testid="stAlert"]{border-radius:12px}
.tf-step{display:inline-block;background:#0e7a8c;color:#fff;border-radius:999px;width:26px;height:26px;
    line-height:26px;text-align:center;font-weight:700;font-size:.85rem;margin-right:8px}
.tf-muted{opacity:.75;font-size:.9rem}

/* ---- sidebar: a little wider, with a compact profile header ------------------------ */
section[data-testid="stSidebar"][aria-expanded="true"]{min-width:380px;width:380px}
section[data-testid="stSidebar"] .tf-avatar{width:76px;height:76px;font-size:1.6rem}
section[data-testid="stSidebar"] .tf-avatar-img{width:76px;height:76px}
section[data-testid="stSidebar"] .tf-profile-name{font-size:1.2rem}

/* ---- profile -------------------------------------------------------------------- */
.tf-profile-head{text-align:center;padding:10px 0 14px}
.tf-avatar{width:92px;height:92px;border-radius:50%;margin:0 auto 12px;display:flex;align-items:center;
    justify-content:center;font-size:2rem;font-weight:700;color:#fff;
    background:linear-gradient(135deg,#0e7a8c 0%,#164a5a 100%)}
.tf-avatar-img{width:110px;height:110px;border-radius:50%;object-fit:cover;display:block;margin:0 auto 12px;
    border:3px solid rgba(14,122,140,.35)}
.tf-profile-name{font-size:1.45rem;font-weight:700;line-height:1.2}
.tf-profile-headline{opacity:.8;margin-top:4px}
.tf-edu{margin:6px 0 12px}
.tf-skills{display:flex;flex-wrap:wrap;gap:8px}
.tf-skill{background:rgba(14,122,140,.10);border:1px solid rgba(14,122,140,.28);border-radius:999px;
    padding:6px 14px;font-weight:600;font-size:.92rem}
.tf-skill small{opacity:.7;font-weight:500;margin-left:8px;padding-left:8px;border-left:1px solid rgba(14,122,140,.35)}
</style>
"""

BANNER = """
<div class="tf-banner">
  <div>
    <h1>TalentFlow Analytics</h1>
    <p>Plan monthly placements, find what holds revenue back, and size your interview team.</p>
  </div>
  <div class="tf-chips">
    <span class="tf-chip">Linear programming</span>
    <span class="tf-chip">Sensitivity analysis</span>
    <span class="tf-chip">Queueing model</span>
  </div>
</div>
"""


def apply_style() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def banner() -> None:
    st.markdown(BANNER, unsafe_allow_html=True)


def sidebar() -> None:
    with st.sidebar:
        st.markdown("### :material/insights: TalentFlow Analytics")
        st.caption("Prescriptive analytics for recruitment and staffing firms")
        st.divider()
        auth.account_box()
        profile.render_sidebar()
        st.divider()
        st.markdown("**How to use this app**")
        st.markdown(
            "1. Pick a tab at the top.\n"
            "2. Start from an example, then change the numbers.\n"
            "3. Read the answer at the top of the results.\n"
            "4. Open the other result tabs for profit gained, bottleneck fixes and details."
        )
        st.divider()
        with st.expander("Plain-language glossary", icon=":material/menu_book:"):
            st.markdown(
                "**Bottleneck** - a limit the plan uses completely. Raising it raises profit.\n\n"
                "**Net profit** - placement fees minus sourcing and recruiter costs.\n\n"
                "**Profit gained** - how much more net profit the best plan earns than today's plan.\n\n"
                "**Busy time** - the share of time an interviewer is occupied.\n\n"
                "**Average wait** - time a candidate spends in line before an interview starts."
            )
        st.caption("Results are estimates based on the numbers you enter. Check them against your own hiring "
                   "records before you act on them.")
