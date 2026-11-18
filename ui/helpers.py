"""Small shared helpers for the TalentFlow pages: number formats, wide tables, metric rows, cards."""
from __future__ import annotations

import html
import math

import pandas as pd
import streamlit as st

TEAL = "#0e7a8c"


# --------------------------------------------------------------------------- #
#  Number formats                                                             #
# --------------------------------------------------------------------------- #
def peso(x: float) -> str:
    return f"₱{x:,.0f}"


def num(x: float) -> str:
    return f"{x:,.0f}" if abs(x - round(x)) < 0.005 else f"{x:,.2f}"


def amount(v: float, unit: str) -> str:
    return peso(v) if unit == "PHP" else f"{num(v)} {unit}"


def signed_peso(v: float) -> str:
    if abs(v) < 0.5:
        return "No change"
    return ("+" if v > 0 else "−") + peso(abs(v))


def signed_num(v: float) -> str:
    return "0" if abs(v) < 0.005 else f"{v:+,.0f}" if abs(v - round(v)) < 0.005 else f"{v:+,.2f}"


def clean(v):
    """Turn an empty table cell (None or NaN) into None."""
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else v


def esc(text) -> str:
    return html.escape(str(text))


# --------------------------------------------------------------------------- #
#  Layout pieces                                                              #
# --------------------------------------------------------------------------- #
def show_table(df: pd.DataFrame, **kwargs) -> None:
    """A table that fills the full width of the page, on old and new Streamlit versions."""
    try:
        st.dataframe(df, hide_index=True, width="stretch", **kwargs)
    except Exception:  # older Streamlit does not know width="stretch"
        st.dataframe(df, hide_index=True, use_container_width=True, **kwargs)


def money_input(target, label: str, **kwargs) -> float:
    """A number box for pesos. It shows the typed amount below the box as, for example, ₱300,000."""
    value = target.number_input(label, **kwargs)
    target.caption(f"Amount: {peso(value)}")
    return value


def metric_row(items: list, per_row: int | None = None) -> None:
    """Show metric cards in rows. Each item is a dict: label, value, and optionally delta, help, delta_color."""
    per_row = per_row or len(items)
    for start in range(0, len(items), per_row):
        chunk = items[start:start + per_row]
        for col, it in zip(st.columns(per_row), chunk):
            col.metric(it["label"], it["value"], delta=it.get("delta"), help=it.get("help"),
                       delta_color=it.get("delta_color", "normal"))


def hero(label: str, headline: str, sub: str = "") -> None:
    """The big highlighted answer at the top of a results page. Pass text that is already HTML-safe."""
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="tf-hero"><div class="lab">{label}</div><div class="main">{headline}</div>'
                f"{sub_html}</div>", unsafe_allow_html=True)


def section(title: str, caption: str = "") -> None:
    st.subheader(title)
    if caption:
        st.caption(caption)


def bullets(lines: list) -> str:
    return "\n".join(f"- {t}" for t in lines)
