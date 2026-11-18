"""Interview queue page: your numbers, then the results in tabs."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from model import solve_queue

from .helpers import bullets, hero, metric_row, money_input, num, peso, section, show_table, signed_peso


@st.cache_data(show_spinner=False)
def run_queue(lam, mu, smax, target, util, costs, current):
    """costs = (hours per month, cost per interviewer hour, % lost per minute of wait, value per lost candidate) or None."""
    if costs is None:
        return solve_queue(lam, mu, smax, target, util / 100, current_servers=current)
    hrs, rate, drop_pct, value = costs
    return solve_queue(lam, mu, smax, target, util / 100, hrs, rate, drop_pct / 100, value, current_servers=current)


# --------------------------------------------------------------------------- #
#  Step 1: inputs                                                             #
# --------------------------------------------------------------------------- #
def render_inputs():
    section(":material/tune: 1. Enter your numbers", "Results update as you type.")
    left, right = st.columns([3, 2])
    with left:
        with st.container(border=True):
            st.markdown("**:material/groups: Candidates and interviewers**")
            a, b, c = st.columns(3)
            lam = a.number_input("Candidates arriving per hour", min_value=0.0, value=20.0, step=1.0)
            mu = b.number_input("Interviews per hour, per interviewer", min_value=0.0, value=25.0, step=1.0)
            smax = c.number_input("Compare up to (interviewers)", min_value=1, max_value=20, value=4, step=1)
    with right:
        with st.container(border=True):
            st.markdown("**:material/flag: Your targets**")
            a, b = st.columns(2)
            target = a.number_input("Longest acceptable wait (min)", min_value=0.0, value=1.0, step=0.5)
            util = b.number_input("Highest acceptable busy time (%)", min_value=1.0, max_value=99.0, value=85.0,
                                  step=1.0)

    with st.container(border=True):
        st.markdown("**:material/payments: Cost assumptions (optional)**")
        st.caption("These are placeholders. Replace them with your own figures, because the cost comparison is only "
                   "as good as these numbers.")
        use_cost = st.checkbox("Compare the monthly cost of each team size", value=True)
        a, b, c = st.columns(3)
        c_cur = a.number_input("Interviewers you have today", min_value=1, max_value=20, value=1, step=1,
                               disabled=not use_cost, help="Cost saved is measured against this team size.")
        c_hours = b.number_input("Interview hours per month", min_value=1.0, value=160.0, step=10.0,
                                 disabled=not use_cost)
        c_rate = money_input(c, "Cost per interviewer hour", min_value=0.0, value=150.0, step=10.0,
                                disabled=not use_cost)
        d, e, _ = st.columns(3)
        c_drop = d.number_input("Candidates lost per minute of wait (%)", min_value=0.0, max_value=100.0, value=0.5,
                                step=0.1, disabled=not use_cost,
                                help="For example 0.5 means a 4.8% loss when the average wait is 9.6 minutes.")
        c_value = money_input(e, "Fee value of each lost candidate", min_value=0.0, value=1000.0, step=100.0,
                                 disabled=not use_cost,
                                 help="A rough guide: monthly placement fees divided by candidates interviewed per month.")

    costs = (float(c_hours), float(c_rate), float(c_drop), float(c_value)) if use_cost else None
    return float(lam), float(mu), int(smax), float(target), float(util), costs, int(c_cur), use_cost


# --------------------------------------------------------------------------- #
#  Results tabs                                                               #
# --------------------------------------------------------------------------- #
def tab_recommendation(q, target, util):
    rows, rec = q["rows"], q["recommended"]
    best = rows[rec - 1] if rec else None
    one = rows[0]
    if rec:
        hero("Recommended interview team", f"{rec} interviewer{'s' if rec > 1 else ''}",
             f"Average wait {best['wq_min']:.1f} minutes &nbsp;·&nbsp; each interviewer busy "
             f"{best['utilization']:.0%} of the time")
    else:
        hero("Recommended interview team", "No option meets both targets yet",
             "Compare more interviewers, or relax a target.")
    metric_row([
        dict(label="Interviewers needed", value=str(rec) if rec else "Not yet"),
        dict(label="Average wait", value=f"{best['wq_min']:.1f} min" if best else "n/a"),
        dict(label="Wait with one interviewer", value=f"{one['wq_min']:.1f} min" if one["stable"] else "Never ends"),
        dict(label="Busy time per interviewer", value=f"{best['utilization']:.0%}" if best else "n/a"),
    ])
    st.write("")
    for line in q["insights"]:
        if line.startswith(("On cost", "Or keep")):
            st.info(line, icon=":material/savings:")
        else:
            (st.success if rec else st.warning)(line, icon=":material/check_circle:" if rec else ":material/warning:")


def tab_cost(q, use_cost):
    section(":material/savings: Cost saved (monthly)",
            "Interviewer pay plus the fees lost when waiting candidates drop out, for each team size.")
    cost = q["cost"]
    if not use_cost or not cost:
        st.info("Turn on **Compare the monthly cost of each team size** in the form above to see the cost saved.",
                icon=":material/info:")
        return
    if not cost["best"]:
        st.warning("No team size in the range can keep up with the arrivals, so there is no cost to compare.",
                   icon=":material/warning:")
        return
    cur_n = q["current_servers"]
    cur_txt = "one interviewer" if cur_n == 1 else f"your {cur_n} interviewers"
    plural = "s" if cost["best"] > 1 else ""
    if cost["saving_month"] is not None:
        hero(f"Cost saved against {cur_txt}", f"{peso(cost['saving_month'])} a month",
             f"{peso(cost['saving_year'])} a year &nbsp;·&nbsp; lowest-cost team: {cost['best']} interviewer{plural}")
    metric_row([
        dict(label="Lowest-cost team", value=f"{cost['best']} interviewer{plural}"),
        dict(label="Total monthly cost", value=peso(cost["best_total"]),
             help="Interviewer pay plus the fees lost when waiting candidates drop out."),
        dict(label=f"Cost saved vs {cur_txt}",
             value=peso(cost["saving_month"]) if cost["saving_month"] is not None else "n/a",
             help="Monthly cost of your current team minus the lowest-cost team."),
    ])
    if cost["saving_month"] is not None:
        st.write("")
        metric_row([
            dict(label=f"Monthly cost today ({cur_n})", value=peso(cost["current_total"])),
            dict(label="Interviewer pay change", value=signed_peso(cost["pay_change"]),
                 help="Extra interviewers cost more in pay. Negative means pay goes down."),
            dict(label="Lost-candidate cost saved", value=peso(cost["lost_saved"]),
                 help="Value of the candidates who no longer drop out while waiting."),
            dict(label="Candidates kept each month", value=num(cost["lost_candidates_saved"])),
        ], per_row=4)
    if cost["rec_total"] is not None and q["recommended"] and q["recommended"] != cost["best"]:
        extra = (f", which saves {peso(cost['rec_saving_month'])} against {cur_txt}"
                 if cost["rec_saving_month"] is not None and cost["rec_saving_month"] > 0 else "")
        st.caption(f":material/info: The team that meets your wait targets ({q['recommended']} interviewers) costs "
                   f"{peso(cost['rec_total'])} a month{extra}.")


def tab_fixes(q):
    section(":material/build_circle: Solutions for the wait",
            "Ways to meet your wait and busy-time targets, starting from the team you have today.")
    rows, rec, cost, fx = q["rows"], q["recommended"], q["cost"], q["fixes"]
    cur_n = q["current_servers"]
    cur_txt = "one interviewer" if cur_n == 1 else f"your {cur_n} interviewers"
    if fx["meets_now"]:
        st.success(f"Your {cur_n} interviewer{'s' if cur_n > 1 else ''} already meet your wait and busy-time targets, "
                   "so no fix is needed.", icon=":material/check_circle:")
        return
    st.caption(f"Starting from {cur_txt}:")
    opts = []
    if rec:
        opts.append({"Option": f"Go up to {rec} interviewers",
                     "What changes": f"{rec - cur_n:+d} interviewer(s)" if rec != cur_n else "None",
                     "Result": f"Average wait {rows[rec - 1]['wq_min']:.1f} min, busy {rows[rec - 1]['utilization']:.0%}"})
    if fx["needed_mu"] is not None:
        opts.append({"Option": "Make each interview faster",
                     "What changes": f"+{fx['speedup_pct']:.0f}% (to {fx['needed_mu']:.1f} interviews per hour)",
                     "Result": "Meets both targets without hiring"})
    if fx["max_arrival"] is not None:
        opts.append({"Option": "Spread out arrivals (book time slots)",
                     "What changes": f"Cap at {fx['max_arrival']:.1f} candidates per hour (−{fx['arrival_cut_pct']:.0f}%)",
                     "Result": "Meets both targets without hiring"})
    show_table(pd.DataFrame(opts))
    if cost and cost["best"] and rec and cost["best"] != rec:
        st.caption("Hiring is not the only route. Compare its cost on the Cost saved tab before you decide.")


def tab_compare(q, target, util):
    rows, cost = q["rows"], q["cost"]
    section(":material/table_chart: Interviewers compared",
            f"Targets: average wait of {target:g} minutes or less, interviewers busy {util:.0f}% of the time or less. "
            f"At least {q['min_servers']} interviewer{'s are' if q['min_servers'] > 1 else ' is'} needed for the "
            "line to stay stable.")
    table_rows = []
    for r in rows:
        if r["stable"]:
            row = {"Interviewers": r["servers"], "Busy time": r["utilization"] * 100,
                   "Chance of waiting": f"{r['p_wait']:.0%}", "Average wait (min)": round(r["wq_min"], 2),
                   "Candidates in line": round(r["lq"], 2), "Time to finish (min)": round(r["w_min"], 1),
                   "Meets targets": "✅ Yes" if r["meets"] else "❌ No"}
            if cost:
                row.update({"Interviewer pay (₱)": round(r["staff_cost"]), "Lost candidates": round(r["lost"], 1),
                            "Value of lost candidates (₱)": round(r["lost_value"]),
                            "Total monthly cost (₱)": round(r["total_cost"])})
        else:
            row = {"Interviewers": r["servers"], "Busy time": min(100.0, r["utilization"] * 100),
                   "Chance of waiting": "n/a", "Average wait (min)": None, "Candidates in line": None,
                   "Time to finish (min)": None, "Meets targets": "❌ Cannot keep up"}
            if cost:
                row.update({"Interviewer pay (₱)": None, "Lost candidates": None,
                            "Value of lost candidates (₱)": None, "Total monthly cost (₱)": None})
        table_rows.append(row)
    qdf = pd.DataFrame(table_rows)
    show_table(qdf, column_config={"Busy time": st.column_config.ProgressColumn("Busy time", min_value=0,
                                                                                max_value=100, format="%d%%")})
    stable = qdf.dropna(subset=["Average wait (min)"])
    if len(stable):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Average wait by team size (minutes)")
            st.bar_chart(stable.set_index("Interviewers")["Average wait (min)"])
        if cost:
            with c2:
                st.markdown("#### Monthly cost by team size (₱)")
                st.bar_chart(stable.set_index("Interviewers")[["Interviewer pay (₱)", "Value of lost candidates (₱)"]])
                st.caption("Interviewer pay plus the value of candidates lost to waiting. The shortest bar is the cheapest.")


# --------------------------------------------------------------------------- #
#  Page                                                                       #
# --------------------------------------------------------------------------- #
def render():
    lam, mu, smax, target, util, costs, current, use_cost = render_inputs()
    q = run_queue(lam, mu, smax, target, util, costs, current)

    st.divider()
    section(":material/analytics: 2. Your results")
    if not q["ok"]:
        st.error(q["error"], icon=":material/error:")
        return

    t_rec, t_cost, t_fix, t_cmp = st.tabs([
        ":material/emoji_events: Recommendation",
        ":material/savings: Cost saved",
        ":material/build_circle: Solutions for the wait",
        ":material/table_chart: Compare team sizes",
    ])
    with t_rec:
        tab_recommendation(q, target, util)
    with t_cost:
        tab_cost(q, use_cost)
    with t_fix:
        tab_fixes(q)
    with t_cmp:
        tab_compare(q, target, util)
