import streamlit as st

from assistant.session_manager import (
    reset_session,
)

def render_command_bar():

    col1, col2, col3, col4 = st.columns(
        [3, 1, 1, 1]
    )

    with col1:
        st.markdown(
            "### Chat with XAIDA"
        )

    with col2:
        st.button(
            "About",
            use_container_width=True,
        )

    with col3:
        st.button(
            "Settings",
            use_container_width=True,
        )

    with col4:
        if st.button(
            "New Analysis",
            use_container_width=True,
        ):
            reset_session()

            st.rerun()