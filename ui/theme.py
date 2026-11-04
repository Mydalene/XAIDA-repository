import streamlit as st


def apply_theme():

    st.markdown(
        """
<style>

.block-container {
    padding-top: 1rem;
    max-width: 1200px;
}

.xaida-header {
    text-align: center;
    padding: 0.5rem;
    border: 1px solid #444;
    margin-bottom: 0.75rem;
}

.xaida-header h1 {
    margin-bottom: 0.1rem;
}

.xaida-header p {
    margin: 0;
}

.workspace-card {
    border: 1px solid #444;
    padding: 1rem;
    border-radius: 6px;
    margin-top: 0.5rem;
    margin-bottom: 0.75rem;
}

</style>
""",
        unsafe_allow_html=True,
    )