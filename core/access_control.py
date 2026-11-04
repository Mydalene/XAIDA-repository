import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

from core.user_auth import (
    AuthenticationStorageError,
    allowed_email_set,
    authenticate_account,
    create_account,
    password_error,
    valid_email,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def authentication_required():
    setting = os.getenv("XAIDA_REQUIRE_AUTH", "true").strip().casefold()
    if setting not in {"true", "false"}:
        raise ValueError("XAIDA_REQUIRE_AUTH must be set to 'true' or 'false'.")
    return setting == "true"


def allowed_emails():
    return allowed_email_set()


def is_authorized_email(email, authorized_emails):
    return bool(email) and email.strip().casefold() in authorized_emails


def oidc_configuration_present():
    try:
        return bool(st.secrets.get("auth"))
    except StreamlitSecretNotFoundError:
        return False


def oidc_user_logged_in():
    return bool(getattr(st.user, "is_logged_in", False))


def authenticated_user_email():
    if oidc_user_logged_in():
        return st.user.get("email", "")
    return st.session_state.get("xaida_local_user_email", "")


def _render_authentication_page():
    with st.container(
        horizontal=True,
        horizontal_alignment="center",
        wrap=True,
    ):
        with st.container(
            width=480,
            border=True,
            key="xaida_authentication_card",
        ):
            st.subheader("XAIDA")
            st.caption("Sign in to your auditor workspace")

            if oidc_configuration_present():
                if st.button(
                    "Continue with organization SSO",
                    icon=":material/lock:",
                    key="xaida_oidc_login",
                ):
                    st.login()
                    st.stop()
                st.caption("Or sign in with your email")

            sign_in_tab, sign_up_tab = st.tabs(
                ["Sign in", "Create account"]
            )

            with sign_in_tab:
                with st.form("xaida_local_sign_in"):
                    email = st.text_input(
                        "Email address",
                        key="xaida_login_email",
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        key="xaida_login_password",
                    )
                    submitted = st.form_submit_button(
                        "Sign in",
                        type="primary",
                    )
                if submitted:
                    try:
                        signed_in = authenticate_account(email, password)
                    except AuthenticationStorageError as error:
                        st.error(str(error))
                    else:
                        if signed_in:
                            st.session_state["xaida_local_user_email"] = (
                                email.strip().casefold()
                            )
                            st.rerun()
                        st.error(
                            "Email or password is incorrect, or this email "
                            "is not approved."
                        )

            with sign_up_tab:
                st.caption(
                    "Use an email address approved by your administrator."
                )
                with st.form("xaida_local_sign_up"):
                    email = st.text_input(
                        "Email address",
                        key="xaida_signup_email",
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        key="xaida_signup_password",
                    )
                    password_confirmation = st.text_input(
                        "Confirm password",
                        type="password",
                        key="xaida_signup_password_confirmation",
                    )
                    submitted = st.form_submit_button(
                        "Create account",
                        type="primary",
                    )
                if submitted:
                    if not valid_email(email):
                        st.error("Enter a valid email address.")
                    elif error := password_error(password):
                        st.error(error)
                    elif password != password_confirmation:
                        st.error("The passwords do not match.")
                    else:
                        try:
                            created = create_account(email, password)
                        except ValueError as error:
                            st.error(str(error))
                        except AuthenticationStorageError as error:
                            st.error(str(error))
                        else:
                            if not created:
                                st.error(
                                    "An account already exists for this "
                                    "email address."
                                )
                            else:
                                st.session_state[
                                    "xaida_local_user_email"
                                ] = email.strip().casefold()
                                st.rerun()


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

    if oidc_user_logged_in():
        email = st.user.get("email", "")
        if is_authorized_email(email, authorized_users):
            return
        st.error("Your account is not authorized to access XAIDA.")
        st.stop()

    email = st.session_state.get("xaida_local_user_email", "")
    if email:
        if is_authorized_email(email, authorized_users):
            return
        st.session_state.pop("xaida_local_user_email", None)
        st.error("Your account is not authorized to access XAIDA.")
        st.stop()

    _render_authentication_page()
    st.stop()
