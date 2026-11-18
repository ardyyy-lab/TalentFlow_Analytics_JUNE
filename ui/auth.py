"""Sign-in. The mode is chosen by what you put in Streamlit's secrets (see .streamlit/secrets.toml.example):

    [auth] ...          Single sign-on (Google, Microsoft, or any OpenID Connect provider), uses st.login
    app_password = ".." One shared password
    allow_guest = true  Adds a "Continue as guest" button
    nothing set         No sign-in: the app opens straight away (good for local use)
"""
from __future__ import annotations

import hmac

import streamlit as st

MAX_PASSWORD_TRIES = 5


def _secret(key: str, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:  # no secrets file at all
        return default


def _sso_providers() -> list:
    """Names of configured single-sign-on providers. [None] means one default provider."""
    cfg = _secret("auth")
    if not cfg or not hasattr(st, "login"):
        return []
    try:
        if "client_id" in cfg:
            return [None]
        return [k for k in cfg.keys() if hasattr(cfg[k], "keys") and "client_id" in cfg[k]]
    except Exception:
        return []


def _sso_user():
    try:
        if st.user.is_logged_in:
            email = str(st.user.get("email") or "")
            return {"name": str(st.user.get("name") or email or "User"), "email": email, "method": "sso"}
    except Exception:
        pass
    return None


def current_user():
    return _sso_user() or st.session_state.get("tf_user")


def _login_page(providers: list, password, guest: bool) -> None:
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        with st.container(border=True):
            st.markdown("### :material/lock: Sign in")
            st.caption("Sign in to use TalentFlow Analytics.")
            for p in providers:
                label = "Continue with single sign-on" if p is None else f"Continue with {str(p).title()}"
                st.button(label, key=f"sso_{p}", icon=":material/login:", on_click=st.login,
                          args=() if p is None else (p,))
            if providers and password:
                st.markdown("<div class='tf-muted' style='text-align:center'>or</div>", unsafe_allow_html=True)
            if password:
                locked = st.session_state.get("tf_tries", 0) >= MAX_PASSWORD_TRIES
                with st.form("tf_password_login"):
                    name = st.text_input("Your name (optional)")
                    pw = st.text_input("Password", type="password", disabled=locked)
                    ok = st.form_submit_button("Sign in", icon=":material/key:", disabled=locked)
                if ok:
                    if hmac.compare_digest(pw.encode(), str(password).encode()):
                        st.session_state["tf_user"] = {"name": name.strip() or "Member", "email": "",
                                                       "method": "password"}
                        st.session_state["tf_tries"] = 0
                        st.rerun()
                    else:
                        st.session_state["tf_tries"] = st.session_state.get("tf_tries", 0) + 1
                        st.error("Incorrect password.")
                if locked:
                    st.warning("Too many tries. Reload the page to try again.")
            if guest:
                if providers or password:
                    st.divider()
                if st.button("Continue as guest", key="tf_guest", icon=":material/person:"):
                    st.session_state["tf_user"] = {"name": "Guest", "email": "", "method": "guest"}
                    st.rerun()


def _denied(user: dict) -> None:
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        with st.container(border=True):
            st.markdown("### :material/block: No access")
            st.error(f"{user['email'] or user['name']} is not on the list of people allowed to use this app. "
                     "Ask the owner to add you.")
            st.button("Sign out", on_click=st.logout, icon=":material/logout:")


def require_login() -> None:
    """Call near the top of the app. Shows the sign-in page and stops the script until the person is signed in."""
    providers, password = _sso_providers(), _secret("app_password")
    guest = bool(_secret("allow_guest", False))
    if not providers and not password:                       # sign-in is not set up: open app
        st.session_state.setdefault("tf_user", {"name": "", "email": "", "method": "open"})
        return
    user = current_user()
    if user:
        allowed = _secret("allowed_emails")
        if user["method"] == "sso" and allowed and user["email"].lower() not in [str(a).lower() for a in allowed]:
            _denied(user)
            st.stop()
        return
    _login_page(providers, password, guest)
    st.stop()


def _sign_out() -> None:
    st.session_state.pop("tf_user", None)
    st.session_state.pop("tf_chat", None)


def account_box() -> None:
    """Who is signed in, with a sign-out button. Put it in the sidebar."""
    user = current_user()
    if not user or user["method"] == "open":
        return
    st.markdown(f"**:material/account_circle: {user['name'] or 'Signed in'}**")
    if user["email"]:
        st.caption(user["email"])
    elif user["method"] == "guest":
        st.caption("Guest")
    if user["method"] == "sso":
        st.button("Sign out", key="tf_signout", on_click=st.logout, icon=":material/logout:")
    else:
        st.button("Sign out", key="tf_signout", on_click=_sign_out, icon=":material/logout:")
    st.divider()
