import streamlit as st


def render_workflow_actions():

    st.subheader(
        "Workflow Actions"
    )

    c1, c2 = st.columns(2)

    with c1:
        st.button(
            "Upload Dataset",
            use_container_width=True,
        )

    with c2:
        st.button(
            "Use Sample Dataset",
            use_container_width=True,
        )
