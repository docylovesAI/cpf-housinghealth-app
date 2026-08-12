"""
Simple password gate for the app, as recommended in the assignment brief.

This is intentionally basic -- a single shared password checked against a
secret, not a full user-account system. It's meant to keep the app from
being wide open to the public internet, not to provide strong security.
"""

import streamlit as st


def check_password() -> bool:
    """
    Show a password prompt and halt the page (via st.stop()) until the
    correct password is entered. Once entered correctly, the result is
    stored in st.session_state, which Streamlit shares across all pages
    in the same browser session -- so the user only has to log in once,
    not on every page.

    Call this as the very first thing after st.set_page_config() on every
    page, so a user can't bypass the gate by navigating directly to a
    page's URL.
    """

    def _password_entered():
        if st.session_state.get("password_input") == st.secrets.get("APP_PASSWORD", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]  # don't keep the raw password around
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", type="password", on_change=_password_entered, key="password_input"
    )
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Incorrect password.")

    st.stop()
    return False
