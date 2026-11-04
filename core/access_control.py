import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def authentication_required():
    setting = os.getenv("XAIDA_REQUIRE_AUTH", "true").strip().casefold()
    if setting not in {"true", "false"}:
        raise ValueError("XAIDA_REQUIRE_AUTH must be set to 'true' or 'false'.")
    return setting == "true"


def allowed_emails():
    return {
        email.strip().casefold()
        for email in os.getenv("XAIDA_ALLOWED_EMAILS", "").split(",")
        if email.strip()
    }


def is_authorized_email(email, authorized_emails):
    return bool(email) and email.strip().casefold() in authorized_emails


def oidc_configuration_present():
    try:
        return bool(st.secrets.get("auth"))
    except StreamlitSecretNotFoundError:
        return False


def enforce_access_control():
    if not authentication_required():
        return

    authorized_users = allowed_emails()
    if not authorized_users:
        st.error(
            "Access control is enabled, but XAIDA_ALLOWED_EMAILS is empty. "
            "Contact your deployment administrator."
        )
        st.stop()

    if not oidc_configuration_present():
        st.error(
            "Access control is enabled, but the Streamlit OIDC provider is "
            "not configured. Contact your deployment administrator."
        )
        st.stop()

    if not st.user.is_logged_in:
        st.title("Sign in to XAIDA")
        st.login()
        st.stop()

    email = st.user.get("email", "")
    if not is_authorized_email(email, authorized_users):
        st.error("Your account is not authorized to access XAIDA.")
        st.stop()
