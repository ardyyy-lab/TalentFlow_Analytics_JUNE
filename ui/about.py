"""About tab: how the models work and what they assume."""
import streamlit as st

from .helpers import section


def render():
    section(":material/menu_book: How the models work")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("#### :material/groups: Placement planner")
            st.markdown(
                "Uses **Linear Programming**: it chooses how many hires of each job type to make so that total "
                "placement fees are as high as possible without breaking any limit.\n\n"
                "- **Limits:** recruiter hours, qualified candidates, an optional sourcing budget, and optional "
                "minimum or maximum hires per job type.\n"
                "- **Shadow prices:** what one more hour, candidate or peso of budget is worth.\n"
                "- **Ranges:** how far a limit or a fee can change before the best plan changes.\n"
                "- **Profit gained:** the best plan compared with the hires you make today (optional column).\n"
                "- **Bottleneck solutions:** the planner raises a limit only where the extra fees beat the extra "
                "cost, up to the most you say you could add, and shows the best plan after the fix.\n"
                "- Works with **any number of job types**, solved with SciPy's HiGHS solver.")
    with c2:
        with st.container(border=True):
            st.markdown("#### :material/schedule: Interview queue")
            st.markdown(
                "Uses an **M/M/s : (FCFS / ∞ / ∞)** queueing model: candidates arrive at random, are interviewed "
                "first come, first served, and each interviewer works at a steady average pace.\n\n"
                "- **Busy time:** the share of time each interviewer is occupied.\n"
                "- **Chance of waiting:** the probability that a candidate finds every interviewer busy.\n"
                "- **Average wait:** time in line before the interview starts.\n"
                "- The line only stays stable if arrivals are below total interview capacity.\n"
                "- **Cost saved:** the lowest-cost team compared with the team you have today.\n"
                "- **Solutions for the wait:** more interviewers, faster interviews, or spreading out arrivals.")

    with st.container(border=True):
        st.markdown("#### :material/rule: What to keep in mind")
        st.markdown(
            "- Fees, hours and limits are treated as fixed within the month.\n"
            "- Fractions of a hire are allowed in the main plan. A whole-number plan is shown when they differ.\n"
            "- Real arrival and interview rates change during the day. Check the results against your own data.\n"
            "- The effect of waiting on candidate dropouts is not modeled and should be validated with company data.\n"
            "- Profit gained, cost saved and the cost of added capacity depend on the placeholder costs you enter. "
            "Replace them with your own figures before acting on them.\n"
            "- Added capacity is assumed to be available at the cost and amount you enter, and fees per hire stay "
            "the same.")

    with st.expander("Where the project files live", icon=":material/folder:"):
        st.markdown(
            "- `app.py` - starts the page.\n"
            "- `model.py` - the math: linear programming, sensitivity analysis, queueing.\n"
            "- `ui/` - one file per page (planner, queue, about), the sidebar profile (`profile.py`), sign-in (`auth.py`) and "
            "the shared look and feel.\n"
            "- `data/profile.json` - the saved profile.\n"
            "- `test_model.py` - checks the math against the Excel results.")
