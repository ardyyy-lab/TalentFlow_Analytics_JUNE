"""Placement planner page: your numbers, then the results in tabs."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from model import Expansion, Job, Problem, improve_placement, region_2d, solve_placement

from .helpers import (TEAL, amount, bullets, clean, esc, hero, metric_row, money_input, num, peso, section,
                      show_table, signed_num, signed_peso)

# --------------------------------------------------------------------------- #
#  Examples and the editable table                                            #
# --------------------------------------------------------------------------- #
COLS = ["Job type", "Fee per hire (₱)", "Recruiter hours per hire", "Sourcing cost per hire (₱)",
        "Minimum hires", "Maximum hires", "Current hires (optional)"]

PRESETS = {
    "Basic case": dict(
        jobs=[["Technical", 60000, 20, None, None, None, 20],
              ["Support", 40000, 10, None, None, None, 50]],
        hours=1000, pool=70, budget=None, rate=200),
    "With extra limits": dict(
        jobs=[["Technical", 60000, 20, 5000, None, 45, 20],
              ["Support", 40000, 10, 3000, 10, None, 40]],
        hours=1000, pool=70, budget=300000, rate=200),
    "Three job types (new example)": dict(
        jobs=[["Technical", 60000, 20, 5000, None, 45, 20],
              ["Support", 40000, 10, 3000, 10, None, 30],
              ["Management", 90000, 35, 9000, None, 12, 8]],
        hours=1500, pool=90, budget=450000, rate=250),
}

FIX_ADVICE = {
    "hours": "Add recruiter capacity: hire or contract a recruiter, approve overtime, or cut the hours per hire "
             "with screening templates and shared interview slots.",
    "pool": "Widen sourcing: more job-board postings, employee referrals, or an agency partner that brings in "
            "qualified candidates.",
    "budget": "Ask for a bigger sourcing budget. Every peso is spent on hires that earn more in fees than they cost.",
}


def table_to_jobs(df: pd.DataFrame):
    """Turn the editable table into a tuple of plain tuples (hashable, so results can be cached)."""
    jobs = []
    for _, r in df.iterrows():
        name = clean(r.get(COLS[0]))
        if name is None or str(name).strip() == "":
            continue
        mx = clean(r.get(COLS[5]))
        cur = clean(r.get(COLS[6]))
        jobs.append((str(name).strip(), float(clean(r.get(COLS[1])) or 0), float(clean(r.get(COLS[2])) or 0),
                     float(clean(r.get(COLS[3])) or 0), float(clean(r.get(COLS[4])) or 0),
                     None if mx is None else float(mx), None if cur is None else float(cur)))
    return tuple(jobs)


@st.cache_data(show_spinner="Solving the model...")
def run_placement(jobs_t, hours, pool, budget, rate, fix):
    """fix = (hours cost, hours max, candidate cost, candidate max, budget max) or None to skip the bottleneck solutions."""
    p = Problem(tuple(Job(*j) for j in jobs_t), hours, pool, budget, rate)
    res = solve_placement(p)
    imp = improve_placement(p, Expansion(*fix), res) if (res.ok and fix is not None) else None
    return res, (region_2d(p) if res.ok else None), imp


# --------------------------------------------------------------------------- #
#  Step 1: inputs                                                             #
# --------------------------------------------------------------------------- #
def render_inputs():
    section(":material/tune: 1. Enter your numbers",
            "Pick an example to fill the form, then change any number. Results update as you type.")

    preset_name = st.selectbox("Start from an example", list(PRESETS), key="preset")
    preset = PRESETS[preset_name]
    k = list(PRESETS).index(preset_name)          # new keys per example, so the form resets cleanly

    with st.container(border=True):
        st.markdown("**:material/work: Job types**")
        st.caption("One row per type of job you fill. Use the empty last row to add a job, or select a row and press "
                   "Delete to remove it. Leave minimum or maximum blank if there is none. Fill in current hires to see "
                   "the profit gained over today's plan (the example values are made up).")
        table = st.data_editor(
            pd.DataFrame(preset["jobs"], columns=COLS), num_rows="dynamic", hide_index=True, key=f"jobs_{k}",
            column_config={
                COLS[0]: st.column_config.TextColumn("Job type", required=True, width="medium"),
                COLS[1]: st.column_config.NumberColumn(COLS[1], min_value=0, step=1000, format="₱%d", width="medium"),
                COLS[2]: st.column_config.NumberColumn(COLS[2], min_value=0, step=1, format="%g", width="medium"),
                COLS[3]: st.column_config.NumberColumn(COLS[3], min_value=0, step=500, format="₱%d", width="medium",
                                                       help="Only used if you set a sourcing budget."),
                COLS[4]: st.column_config.NumberColumn(COLS[4], min_value=0, step=1, format="%g", width="small"),
                COLS[5]: st.column_config.NumberColumn(COLS[5], min_value=0, step=1, format="%g", width="small"),
                COLS[6]: st.column_config.NumberColumn(COLS[6], min_value=0, step=1, format="%g", width="medium",
                                                       help="Hires you make per month today. Used to show the profit "
                                                            "gained and cost saved by switching to the best plan."),
            })

    left, right = st.columns([2, 3])
    with left:
        with st.container(border=True):
            st.markdown("**:material/event_available: Monthly limits**")
            hours = st.number_input("Recruiter hours available", min_value=0.0, value=float(preset["hours"]),
                                    step=10.0, key=f"hours_{k}")
            pool = st.number_input("Qualified candidates available", min_value=0.0, value=float(preset["pool"]),
                                   step=1.0, key=f"pool_{k}")
            use_budget = st.checkbox("Limit the sourcing budget", value=preset["budget"] is not None,
                                     key=f"usebudget_{k}")
            budget = money_input(st, "Monthly sourcing budget", min_value=0.0,
                                     value=float(preset["budget"] or 300000), step=10000.0,
                                     key=f"budget_{k}", disabled=not use_budget)
            rate = money_input(st, "Recruiter cost per hour", min_value=1.0, value=float(preset["rate"]), step=10.0,
                               key=f"rate_{k}", help="Required. Recruiter pay for the hours the plan uses. It goes into "
                                                     "costs, net profit and cost per hire.")
    with right:
        with st.container(border=True):
            st.markdown("**:material/build_circle: Fix the bottlenecks (optional)**")
            st.caption("Say how much extra capacity you could add and what it would cost. The planner adds capacity "
                       "only where it pays for itself. The costs are placeholders: replace them with your own.")
            find_fix = st.checkbox("Find the best plan after fixing the bottlenecks", value=True, key=f"fix_{k}")
            a, b = st.columns(2)
            h_max = a.number_input("Most extra recruiter hours", min_value=0.0,
                                   value=float(round(0.3 * preset["hours"])), step=10.0, key=f"hmax_{k}",
                                   disabled=not find_fix)
            h_cost = money_input(b, "Extra cost per added hour", min_value=0.0, value=150.0, step=10.0,
                                    key=f"hcost_{k}", disabled=not find_fix,
                                    help="On top of normal recruiter pay, for example an overtime premium or agency fee.")
            c, d = st.columns(2)
            p_max = c.number_input("Most extra candidates", min_value=0.0, value=float(round(0.3 * preset["pool"])),
                                   step=1.0, key=f"pmax_{k}", disabled=not find_fix)
            p_cost = money_input(d, "Extra cost per added candidate", min_value=0.0, value=2000.0, step=100.0,
                                    key=f"pcost_{k}", disabled=not find_fix,
                                    help="Advertising, referral or agency cost of finding one more qualified candidate.")
            b_max = money_input(st, "Most extra sourcing budget", min_value=0.0,
                                    value=float(round(0.3 * (preset["budget"] or 0))), step=10000.0,
                                    key=f"bmax_{k}", disabled=not find_fix or not use_budget,
                                    help="Only used when the sourcing budget is limited. The money is counted when "
                                         "it is spent on hires.")

    jobs_t = table_to_jobs(table)
    fix = (float(h_cost), float(h_max), float(p_cost), float(p_max),
           float(b_max) if use_budget else 0.0) if find_fix else None
    return jobs_t, float(hours), float(pool), float(budget) if use_budget else None, float(rate), fix


# --------------------------------------------------------------------------- #
#  Chart                                                                      #
# --------------------------------------------------------------------------- #
def clip_line(a, b, c, X, Y):
    """Where the line a*x + b*y = c crosses the box [0, X] x [0, Y]."""
    pts = []

    def add(x, y):
        if -1e-9 <= x <= X + 1e-9 and -1e-9 <= y <= Y + 1e-9:
            if not any(abs(x - q[0]) < 1e-6 and abs(y - q[1]) < 1e-6 for q in pts):
                pts.append((x, y))

    if abs(b) > 1e-12:
        add(0, c / b)
        add(X, (c - a * X) / b)
    if abs(a) > 1e-12:
        add(c / a, 0)
        add((c - b * Y) / a, Y)
    return pts[:2] if len(pts) >= 2 else None


def region_figure(res, region):
    verts = region["vertices"]
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    X = max(max(xs) * 1.2, 1.0)
    Y = max(max(ys) * 1.2, 1.0)
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=110)
    ax.fill(xs, ys, color=TEAL, alpha=0.18, label="Feasible region", zorder=1)
    ax.plot(xs + [xs[0]], ys + [ys[0]], color=TEAL, lw=1.4, zorder=2)
    palette = ["#0e5a6b", "#c4510c", "#7b4fa3", "#2f7d5b", "#8a6d00", "#b3261e"]
    for k, (a, b, c, name) in enumerate(region["lines"]):
        seg = clip_line(a, b, c, X, Y)
        if seg:
            ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], color=palette[k % len(palette)],
                    lw=2.2, label=name, zorder=3)
    best_x, best_y = res.hires[0], res.hires[1]
    seg = clip_line(region["fees"][0], region["fees"][1], res.revenue, X, Y)
    if seg:
        ax.plot([seg[0][0], seg[1][0]], [seg[0][1], seg[1][1]], color="#333", lw=1.3, ls="--",
                label="Best-fee line", zorder=3)
    ax.scatter(xs, ys, s=28, color="white", edgecolor="#333", zorder=4)
    ax.scatter([best_x], [best_y], s=130, color="#f2a900", edgecolor="#333", linewidth=1.6, zorder=5,
               label="Best plan")
    ax.annotate(f"Best: {num(best_x)}, {num(best_y)}", (best_x, best_y), textcoords="offset points",
                xytext=(10, 10), fontsize=10, fontweight="bold", color="#222")
    ax.set_xlim(0, X)
    ax.set_ylim(0, Y)
    ax.set_xlabel(f"{res.names[0]} hires (x)")
    ax.set_ylabel(f"{res.names[1]} hires (y)")
    ax.grid(alpha=0.25)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(loc="upper right", fontsize=8, frameon=True, framealpha=0.9)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
#  Results tabs                                                               #
# --------------------------------------------------------------------------- #
def tab_best_plan(res, imp, jobs_t):
    fees = {j[0]: j[1] for j in jobs_t}
    total_hires = sum(res.hires)
    bottlenecks = [l for l in res.limits if l["binding"] and abs(l["shadow"]) > 0]
    hours_row = next(l for l in res.limits if l["key"] == "hours")

    plan_html = " + ".join(f"{num(h)} {esc(n)}" for n, h in zip(res.names, res.hires))
    hero("Best monthly plan", plan_html,
         f"{peso(res.revenue)} in placement fees &nbsp;·&nbsp; {peso(res.net_profit)} net profit "
         f"&nbsp;·&nbsp; {res.margin:.0%} margin")
    if res.whole_hires is not None and any(abs(h - round(h)) > 1e-6 for h in res.hires):
        whole = ", ".join(f"{h} {n.lower()}" for n, h in zip(res.names, res.whole_hires))
        st.caption(f"Counting whole hires only: {whole}, for {peso(res.whole_revenue)} in fees.")

    metric_row([
        dict(label="Monthly placement fees", value=peso(res.revenue)),
        dict(label="Costs", value=peso(res.total_cost),
             help="Sourcing cost of the hires plus recruiter pay for the hours used."),
        dict(label="Net profit", value=peso(res.net_profit), help="Placement fees minus the costs entered."),
        dict(label="Net margin", value=f"{res.margin:.0%}"),
    ])
    st.write("")
    metric_row([
        dict(label="Total hires", value=num(total_hires)),
        dict(label="Cost per hire", value=peso(res.cost_per_hire) if res.total_cost > 0 else "n/a"),
        dict(label="Bottlenecks", value=str(len(bottlenecks)), help="Limits the plan uses completely."),
        dict(label="Recruiter hours used", value=f"{hours_row['used'] / hours_row['limit']:.0%}"),
    ])
    st.caption(f":material/info: The plan is chosen to maximize placement fees, then costs are subtracted "
               f"(sourcing {peso(res.sourcing_cost)}, recruiter pay {peso(res.recruiter_cost)}). "
               "Other overhead is not included.")

    st.markdown("#### Hires by job type")
    per_row = 4
    for start in range(0, len(res.names), per_row):
        cols = st.columns(per_row)
        for col, name, h in zip(cols, res.names[start:start + per_row], res.hires[start:start + per_row]):
            col.metric(f"{name} hires", num(h))
            col.caption(f"{peso(h * fees[name])} in fees")

    with st.container(border=True):
        st.markdown("**:material/lightbulb: What this means**")
        st.markdown(bullets(res.insights))

    out = pd.DataFrame({"Job type": res.names + ["Total"], "Hires": res.hires + [total_hires],
                        "Fees (PHP)": [h * fees[n] for n, h in zip(res.names, res.hires)] + [res.revenue]})
    out.loc[len(out)] = ["Costs (PHP)", None, res.total_cost]
    out.loc[len(out)] = ["Net profit (PHP)", None, res.net_profit]
    if res.current is not None:
        out.loc[len(out)] = ["Net profit today (PHP)", None, res.current["net_profit"]]
        out.loc[len(out)] = ["Profit gained per month (PHP)", None, res.current["profit_gain_month"]]
    if imp is not None:
        out.loc[len(out)] = ["Net profit with bottleneck fixes (PHP)", None, imp["net_profit"]]
        out.loc[len(out)] = ["Profit gained by fixes per month (PHP)", None, imp["gain_month"]]
        for f in imp["fixes"]:
            out.loc[len(out)] = [f"Extra cost to add {num(f['add'])} {f['unit']} (PHP)", None, f["cost_total"]]
    st.download_button(":material/download: Download plan (CSV)", out.to_csv(index=False).encode("utf-8"),
                       file_name="placement_plan.csv", mime="text/csv")


def tab_profit(res, imp, jobs_t):
    cur = res.current
    section(":material/trending_up: Profit gained and cost saved",
            "How much better the best plan is than the hires you make today, and what the bottleneck fixes add on top.")

    if cur is None:
        st.info("Enter the hires you make today in the **Current hires** column of the job table to see the profit "
                "gained and the cost per hire saved by switching to the best plan.", icon=":material/info:")
    else:
        hero("Profit gained by switching to the best plan", f"{peso(cur['profit_gain_month'])} a month",
             f"{peso(cur['profit_gain_year'])} a year &nbsp;·&nbsp; {peso(cur['fees_gain'])} more in placement fees "
             "each month")
        saved = cur["cost_per_hire_saved"]
        metric_row([
            dict(label="Net profit today", value=peso(cur["net_profit"])),
            dict(label="Net profit, best plan", value=peso(res.net_profit),
                 delta=signed_peso(cur["profit_gain_month"]) if abs(cur["profit_gain_month"]) >= 0.5 else None),
            dict(label="Cost per hire saved",
                 value="n/a" if saved is None or res.total_cost == 0 else peso(saved),
                 help="Today's cost per hire minus the best plan's. A negative number means the best plan spends "
                      "more per hire, for example because it shifts to hires that cost more to source."),
        ])
        if cur["breaks"]:
            st.warning("Today's plan goes past these limits: " + ", ".join(cur["breaks"]) +
                       ". Check the current hires you entered.", icon=":material/warning:")

    if imp is not None:
        st.markdown("#### Adding capacity on top")
        base_ref = cur["net_profit"] if cur is not None else imp["base_net"]
        total = imp["net_profit"] - base_ref
        metric_row([
            dict(label="Extra profit from fixes, per month", value=peso(imp["gain_month"]),
                 help="Net profit with the bottleneck fixes minus net profit of the best plan."),
            dict(label="Extra profit from fixes, per year", value=peso(imp["gain_year"])),
            dict(label="Total gain vs today, per month" if cur is not None else "Net profit with fixes",
                 value=peso(total) if cur is not None else peso(imp["net_profit"]),
                 help="Best plan with the fixes against today's plan." if cur is not None else None),
        ])

    st.markdown("#### Side by side")
    cols = ["Measure"] + (["Today"] if cur is not None else []) + ["Best plan"] + (["With fixes"] if imp else [])
    na = "n/a"

    def cph(total_cost, hires):
        return peso(total_cost / hires) if hires > 0 and total_cost > 0 else na

    sets = {
        "Total hires": (num(cur["total_hires"]) if cur else None, num(sum(res.hires)),
                        num(imp["total_hires"]) if imp else None),
        "Placement fees": (peso(cur["fees"]) if cur else None, peso(res.revenue), peso(imp["fees"]) if imp else None),
        "Sourcing cost": (peso(cur["sourcing_cost"]) if cur else None, peso(res.sourcing_cost),
                          peso(imp["sourcing_cost"]) if imp else None),
        "Recruiter pay": (peso(cur["recruiter_cost"]) if cur else None, peso(res.recruiter_cost),
                          peso(imp["recruiter_cost"]) if imp else None),
        "Cost of added capacity": (peso(0) if cur else None, peso(0), peso(imp["expansion_cost"]) if imp else None),
        "Total cost": (peso(cur["total_cost"]) if cur else None, peso(res.total_cost),
                       peso(imp["total_cost"]) if imp else None),
        "Net profit": (peso(cur["net_profit"]) if cur else None, peso(res.net_profit),
                       peso(imp["net_profit"]) if imp else None),
        "Cost per hire": (cph(cur["total_cost"], cur["total_hires"]) if cur else None,
                          cph(res.total_cost, sum(res.hires)),
                          cph(imp["total_cost"], imp["total_hires"]) if imp else None),
    }
    rows = []
    for label, (today, best, fixed) in sets.items():
        row = {"Measure": label}
        if cur is not None:
            row["Today"] = today
        row["Best plan"] = best
        if imp:
            row["With fixes"] = fixed
        rows.append(row)
    show_table(pd.DataFrame(rows, columns=cols))

    st.markdown("#### Hires by job type")
    rows = []
    for i, n in enumerate(res.names):
        row = {"Job type": n}
        if cur is not None:
            row["Today"] = num(cur["hires"][i])
        row["Best plan"] = num(res.hires[i])
        if imp:
            row["With fixes"] = num(imp["hires"][i])
        rows.append(row)
    show_table(pd.DataFrame(rows))


def tab_fixes(res, imp, jobs_t):
    section(":material/build_circle: Solutions for the bottlenecks",
            "First, what is holding revenue back now. Then what to add, what it costs and what you gain.")

    # ---- what holds the plan back now -----------------------------------------------
    bottlenecks = [l for l in res.limits if l["binding"] and abs(l["shadow"]) > 0]
    st.markdown("#### What holds the best plan back")
    if not bottlenecks:
        st.success("No single limit is holding revenue back right now.", icon=":material/check_circle:")
    else:
        with st.container(border=True):
            for l in bottlenecks:
                lo = "any lower value" if l["lower"] is None else amount(l["lower"], l["unit"])
                hi = "no upper limit" if l["upper"] is None else amount(l["upper"], l["unit"])
                st.markdown(f"**{l['name']}** is fully used. Adding {amount(l['step'], l['unit'])} would add about "
                            f"**{peso(l['shadow'] * l['step'])}** in monthly fees, while the limit stays between "
                            f"{lo} and {hi}.")

    # ---- the fixes ---------------------------------------------------------------------
    st.markdown("#### What to add")
    if imp is None:
        st.info("Turn on **Find the best plan after fixing the bottlenecks** in the form above to see which limits to "
                "raise, what it costs and what you gain.", icon=":material/info:")
        return

    st.caption("The planner raises a limit only where the extra fees beat the extra cost, up to the most you said you "
               "could add, then re-solves for the highest net profit.")
    if not imp["fixes"]:
        st.info(imp["insights"][0], icon=":material/info:")
    else:
        hero("Best plan with the bottlenecks fixed", f"{peso(imp['gain_month'])} more profit a month",
             f"{peso(imp['gain_year'])} a year &nbsp;·&nbsp; net profit {peso(imp['net_profit'])} after "
             f"{peso(imp['expansion_cost'])} of extra capacity cost")
        for f in imp["fixes"]:
            with st.container(border=True):
                a, b, c, d = st.columns([3, 1.4, 1.4, 1.6])
                a.markdown(f"**{f['name']}**")
                a.caption(FIX_ADVICE[f["key"]])
                b.metric("Add each month", amount(f["add"], f["unit"]))
                c.metric("Extra cost each month", peso(f["cost_total"]))
                d.metric("Profit gained if done alone", peso(f["gain_alone"]),
                         help="Profit gained if this were the only fix. The fixes work together, so these do not "
                              "add up to the total.")

    # ---- the plan after the fix ----------------------------------------------------------
    st.markdown("#### Plan with the bottlenecks fixed")
    fees = {j[0]: j[1] for j in jobs_t}
    rows = [{"Job type": n, "Best plan": num(a), "With fixes": num(b), "Change": signed_num(b - a),
             "Fees with fixes": peso(b * fees[n])} for n, a, b in zip(res.names, res.hires, imp["hires"])]
    show_table(pd.DataFrame(rows))
    if imp["whole_hires"] is not None and any(abs(h - round(h)) > 1e-6 for h in imp["hires"]):
        st.caption("Counting whole hires only: " + ", ".join(f"{h} {n.lower()}" for n, h in
                                                              zip(res.names, imp["whole_hires"]))
                   + f" (net profit {peso(imp['whole_net'])}).")
    names = {"hours": "Recruiter hours", "pool": "Qualified candidates", "budget": "Sourcing budget"}
    units = {"hours": "hours", "pool": "candidates", "budget": "PHP"}
    lim_rows = [{"Limit": names[k], "Now": amount(v["old"], units[k]), "Needed": amount(v["new"], units[k]),
                 "Increase": amount(v["new"] - v["old"], units[k])}
                for k, v in imp["new_limits"].items() if v["new"] - v["old"] > 1e-6]
    if lim_rows:
        st.markdown("#### New limits to aim for")
        show_table(pd.DataFrame(lim_rows))

    if imp["still"]:
        st.markdown("#### What still holds the improved plan back")
        with st.container(border=True):
            st.markdown(bullets([f"**{x['name']}**: {x['note']}" for x in imp["still"]]))
            if any(x["kind"] == "cap" for x in imp["still"]):
                st.caption("A maximum-hires cap is a policy or client limit, not something the model can buy past. "
                           "Raising it is a conversation with the client or your team.")


def tab_limits(res):
    section(":material/speed: Which limits are holding you back",
            "A bottleneck is a limit the plan uses completely.")
    rows = []
    for l in res.limits:
        if l["kind"] == "<=":
            usage = 0 if l["limit"] == 0 else l["used"] / l["limit"]
            limit_txt = "≤ " + amount(l["limit"], l["unit"])
        else:
            usage = 1.0 if l["used"] == 0 else l["limit"] / l["used"]
            limit_txt = "≥ " + amount(l["limit"], l["unit"])
        rows.append({"Limit": l["name"], "Plan uses": amount(l["used"], l["unit"]), "Limit set at": limit_txt,
                     "Usage": min(100.0, max(0.0, usage * 100)),
                     "Status": "🟠 Bottleneck" if l["binding"] else "🟢 Room to spare"})
    show_table(pd.DataFrame(rows),
               column_config={"Usage": st.column_config.ProgressColumn("Usage", min_value=0, max_value=100,
                                                                       format="%d%%")})

    section(":material/query_stats: What one more unit is worth",
            "How monthly fees change if a limit moves, and how far it can move before the best plan changes.")
    rows = []
    for l in res.limits:
        lo = "any lower value" if l["lower"] is None else amount(l["lower"], l["unit"])
        hi = "no upper limit" if l["upper"] is None else amount(l["upper"], l["unit"])
        rows.append({"Limit": l["name"], "If it goes up by": amount(l["step"], l["unit"]),
                     "Fees change by": signed_peso(l["shadow"] * l["step"]),
                     "Holds while the limit is between": f"{lo} and {hi}"})
    show_table(pd.DataFrame(rows))

    section(":material/payments: How far each fee can change",
            "The best plan stays the same while a fee stays inside its range. Each fee is changed on its own.")
    rows = [{"Job type": f["name"], "Current fee": peso(f["fee"]),
             "Lowest fee that keeps the plan": peso(f["lower"]),
             "Highest fee that keeps the plan": "no upper limit" if f["upper"] is None else peso(f["upper"])}
            for f in res.fee_ranges]
    show_table(pd.DataFrame(rows))


def tab_charts(res, region, jobs_t):
    fees = {j[0]: j[1] for j in jobs_t}
    if region is not None:
        section(":material/show_chart: The feasible region",
                "Every plan inside the shaded area respects all your limits. The best plan sits on a corner.")
        fig = region_figure(res, region)
        st.pyplot(fig)
        plt.close(fig)
        corner = pd.DataFrame([{f"{res.names[0]} (x)": v[0], f"{res.names[1]} (y)": v[1],
                                "Monthly fees": peso(v[2]),
                                "Result": "Best" if abs(v[2] - res.revenue) < 1e-6 else "Feasible"}
                               for v in region["vertices"]])
        with st.expander("Corner points compared", icon=":material/table_chart:"):
            show_table(corner)
    else:
        section(":material/bar_chart: Fees by job type",
                "The feasible-region chart needs exactly two job types, so it is hidden for this plan.")
        fee_df = pd.DataFrame({"Fees (₱)": [h * fees[n] for n, h in zip(res.names, res.hires)]}, index=res.names)
        st.bar_chart(fee_df)


# --------------------------------------------------------------------------- #
#  Page                                                                       #
# --------------------------------------------------------------------------- #
def render():
    jobs_t, hours, pool, budget, rate, fix = render_inputs()
    res, region, imp = run_placement(jobs_t, hours, pool, budget, rate, fix)

    st.divider()
    section(":material/analytics: 2. Your results")
    if not res.ok:
        st.error(res.error, icon=":material/error:")
        return

    t_best, t_profit, t_fix, t_limits, t_charts = st.tabs([
        ":material/emoji_events: Best plan",
        ":material/trending_up: Profit gained",
        ":material/build_circle: Bottleneck fixes",
        ":material/speed: Limits and sensitivity",
        ":material/show_chart: Charts",
    ])
    with t_best:
        tab_best_plan(res, imp, jobs_t)
    with t_profit:
        tab_profit(res, imp, jobs_t)
    with t_fix:
        tab_fixes(res, imp, jobs_t)
    with t_limits:
        tab_limits(res)
    with t_charts:
        tab_charts(res, region, jobs_t)
