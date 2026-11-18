"""Profile block in the left sidebar: a profile you can edit (name, headline, bio, education, skills).

The saved profile lives in data/profile.json. If that file is missing, the built-in example below is used.
Who may edit: everyone, unless `profile_editors = ["you@example.com"]` is set in the secrets file, in which case
only those signed-in emails can edit.
"""
from __future__ import annotations

import base64
import io
import json
import re
from copy import deepcopy
from pathlib import Path

import pandas as pd
import streamlit as st

from . import auth
from .helpers import esc, section

PROFILE_PATH = Path(__file__).resolve().parent.parent / "data" / "profile.json"
LEVELS = ["", "Beginner", "Intermediate", "Advanced", "Expert"]

PHOTO_SIZE = 360                      # photos are cropped to a square and shrunk to this many pixels
_PHOTO_RE = re.compile(r"^data:image/(jpeg|png);base64,[A-Za-z0-9+/=]+$")

DEFAULT_PROFILE = {
    "name": "June Dela Cruz",
    "photo": "",                      # empty = show initials; otherwise a small data:image/jpeg;base64,... string
    "headline": "Mathematician and prescriptive analytics specialist",
    "bio": (
        "June Dela Cruz is a mathematics graduate who turns hiring and staffing questions into models a manager can "
        "act on. He specializes in prescriptive analytics: linear programming to decide how many placements of each "
        "job type to make each month, sensitivity analysis to show which limits (recruiter hours, candidate supply, "
        "sourcing budget) hold revenue back and what relaxing them is worth, and queueing models that size interview "
        "teams so candidates do not wait.\n\n"
        "He builds these tools in Excel Solver and Python, checks them against hand calculations, and explains the "
        "results in plain language to non-technical teams."
    ),
    "education": [
        {"school": "Southern Luzon State University", "degree": "BS Mathematics", "years": ""},
    ],
    "skills": [
        {"skill": "Linear programming", "level": "Advanced"},
        {"skill": "Sensitivity analysis", "level": "Advanced"},
        {"skill": "Queueing theory (M/M/s)", "level": "Advanced"},
        {"skill": "Mathematical modeling", "level": "Advanced"},
        {"skill": "Statistics and data analysis", "level": "Advanced"},
        {"skill": "Excel Solver", "level": "Advanced"},
        {"skill": "Python (SciPy, pandas)", "level": "Intermediate"},
        {"skill": "Streamlit dashboards", "level": "Intermediate"},
        {"skill": "Data visualization", "level": "Intermediate"},
        {"skill": "Explaining results to non-technical teams", "level": "Intermediate"},
    ],
}


# --------------------------------------------------------------------------- #
#  Loading and saving                                                         #
# --------------------------------------------------------------------------- #
def _clean_rows(rows, keys) -> list:
    """Keep only rows that have their first field filled in, with every value as plain text."""
    out = []
    for r in rows or []:
        row = {k: ("" if r.get(k) is None or (isinstance(r.get(k), float) and r.get(k) != r.get(k)) else str(r.get(k)).strip())
               for k in keys}
        if row[keys[0]]:
            out.append(row)
    return out


def prepare_photo(file_bytes: bytes) -> str:
    """Turn an uploaded picture into a small square JPEG, returned as a data URI that is stored in profile.json."""
    from PIL import Image, ImageOps

    img = ImageOps.exif_transpose(Image.open(io.BytesIO(file_bytes))).convert("RGB")
    side = min(img.size)
    left, top = (img.width - side) // 2, (img.height - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize((PHOTO_SIZE, PHOTO_SIZE))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _normalize(d: dict) -> dict:
    photo = str(d.get("photo") or "")
    return {
        "name": str(d.get("name") or "").strip(),
        "photo": photo if _PHOTO_RE.match(photo) else "",
        "headline": str(d.get("headline") or "").strip(),
        "bio": str(d.get("bio") or "").strip(),
        "education": _clean_rows(d.get("education"), ["school", "degree", "years"]),
        "skills": _clean_rows(d.get("skills"), ["skill", "level"]),
    }


def load_profile() -> dict:
    try:
        return _normalize(json.loads(PROFILE_PATH.read_text(encoding="utf-8")))
    except Exception:
        return deepcopy(DEFAULT_PROFILE)


def save_profile_file(profile: dict) -> bool:
    try:
        PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROFILE_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False


def get_profile() -> dict:
    if "tf_profile" not in st.session_state:
        st.session_state["tf_profile"] = load_profile()
    return st.session_state["tf_profile"]


def can_edit() -> bool:
    try:
        editors = st.secrets.get("profile_editors")
    except Exception:
        editors = None
    if not editors:
        return True
    user = auth.current_user()
    return bool(user and user.get("email") and user["email"].lower() in [str(e).lower() for e in editors])


# --------------------------------------------------------------------------- #
#  Showing the profile                                                        #
# --------------------------------------------------------------------------- #
def _initials(name: str) -> str:
    parts = name.split()
    return "?" if not parts else "".join(w[0] for w in parts[:2]).upper()      # "June Dela Cruz" -> "JD"


def show_header(p: dict) -> None:
    """Photo (or initials), name and headline. Always visible at the top of the sidebar."""
    avatar = (f'<img class="tf-avatar-img" alt="{esc(p["name"])}" src="{esc(p["photo"])}">' if p["photo"]
              else f'<div class="tf-avatar">{esc(_initials(p["name"]))}</div>')
    st.markdown(f'<div class="tf-profile-head">{avatar}<div class="tf-profile-name">{esc(p["name"] or "Your name")}</div>'
                f'<div class="tf-profile-headline">{esc(p["headline"])}</div></div>', unsafe_allow_html=True)


def show_details(p: dict) -> None:
    """Bio, education and skills, stacked so they fit the narrow sidebar."""
    st.markdown("**:material/person: About**")
    if p["bio"]:
        st.markdown(p["bio"])
    else:
        st.caption("No bio added yet.")
    st.markdown("**:material/school: Educational background**")
    if not p["education"]:
        st.caption("No education added yet.")
    for e in p["education"]:
        years = f'<div class="tf-muted">{esc(e["years"])}</div>' if e["years"] else ""
        degree = f'<div>{esc(e["degree"])}</div>' if e["degree"] else ""
        st.markdown(f'<div class="tf-edu"><b>{esc(e["school"])}</b>{degree}{years}</div>', unsafe_allow_html=True)
    st.markdown("**:material/construction: Skills**")
    if not p["skills"]:
        st.caption("No skills added yet.")
    else:
        chips = "".join(f'<span class="tf-skill">{esc(s["skill"])}'
                        + (f'<small>{esc(s["level"])}</small>' if s["level"] else "") + "</span>" for s in p["skills"])
        st.markdown(f'<div class="tf-skills">{chips}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
#  Editing the profile                                                        #
# --------------------------------------------------------------------------- #
def edit_form(p: dict) -> None:
    with st.container(border=True):
        st.markdown("**:material/edit: Edit profile**")
        st.caption("Change anything, then press **Save profile**. Add a row with the empty last line of a table; "
                   "remove one by selecting it and pressing Delete.")
        with st.form("profile_form"):
            name = st.text_input("Full name", value=p["name"])
            photo_file = st.file_uploader("Profile photo (optional)", type=["png", "jpg", "jpeg", "webp"],
                                          help="Any picture. It is cropped to a square and shrunk automatically.")
            remove_photo = st.checkbox("Remove the current photo and show initials instead",
                                       value=False, disabled=not p["photo"])
            headline = st.text_input("Headline (your role or title)", value=p["headline"])
            bio = st.text_area("Short bio", value=p["bio"], height=220,
                               help="Your expertise and skills in a few sentences. A blank line starts a new paragraph.")
            st.markdown("**Educational background**")
            edu = st.data_editor(
                pd.DataFrame(p["education"] or [{"school": "", "degree": "", "years": ""}]),
                num_rows="dynamic", hide_index=True, key="profile_edu",
                column_config={"school": st.column_config.TextColumn("School", width="large"),
                               "degree": st.column_config.TextColumn("Degree", width="medium"),
                               "years": st.column_config.TextColumn("Years (optional)", width="small")})
            st.markdown("**Skills**")
            sk = st.data_editor(
                pd.DataFrame(p["skills"] or [{"skill": "", "level": ""}]),
                num_rows="dynamic", hide_index=True, key="profile_skills",
                column_config={"skill": st.column_config.TextColumn("Skill", width="large"),
                               "level": st.column_config.SelectboxColumn("Level (optional)", options=LEVELS,
                                                                         width="medium")})
            saved = st.form_submit_button("Save profile", icon=":material/save:", type="primary")
        if saved:
            photo = p["photo"]
            photo_error = None
            if photo_file is not None:
                try:
                    photo = prepare_photo(photo_file.getvalue())
                except Exception:
                    photo_error = "That file could not be read as a picture, so the old photo was kept."
            elif remove_photo:
                photo = ""
            new = _normalize({"name": name, "photo": photo, "headline": headline, "bio": bio,
                              "education": edu.to_dict("records"), "skills": sk.to_dict("records")})
            if not new["name"]:
                st.error("Please enter a name.")
            else:
                st.session_state["tf_profile"] = new
                if photo_error:
                    st.warning(photo_error, icon=":material/warning:")
                if save_profile_file(new):
                    st.success("Profile saved.", icon=":material/check_circle:")
                else:
                    st.warning("Saved for this visit only. The server would not let the app write the file. "
                               "Download the profile below to keep it.", icon=":material/warning:")
        st.download_button("Download profile (JSON)", json.dumps(get_profile(), indent=2, ensure_ascii=False),
                           file_name="profile.json", mime="application/json", icon=":material/download:")
        if st.button("Restore example profile", icon=":material/restart_alt:",
                     help="Puts June Dela Cruz's example profile back."):
            st.session_state["tf_profile"] = deepcopy(DEFAULT_PROFILE)
            save_profile_file(st.session_state["tf_profile"])
            st.rerun()


# --------------------------------------------------------------------------- #
#  Page                                                                       #
# --------------------------------------------------------------------------- #
def render_sidebar() -> None:
    """The Profile block for the left sidebar: the person's header, then details and the editor in an expander."""
    show_header(get_profile())
    with st.expander("View or edit profile", icon=":material/badge:"):
        if can_edit():
            editing = st.toggle("Edit profile", key="profile_edit")
        else:
            editing = False
            st.caption(":material/lock: Only the app owner can edit this profile.")
        if editing:
            edit_form(get_profile())
            st.markdown("#### Preview")
        show_details(get_profile())
