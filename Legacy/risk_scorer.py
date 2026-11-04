import pandas as pd
import streamlit as st

scores = (
    results.get(
        "scores"
    )
)

if scores is not None:

    st.write(
        "**Risk Score Distribution**"
    )

    st.bar_chart(
        pd.DataFrame(
            {
                "Risk Score": scores
            }
        )
    )

    flagged = (
    results.get(
        "flagged_transactions"
    )
)

if flagged is not None:

    st.write(
        "**Flagged Transactions**"
    )

    st.dataframe(
        flagged,
        width="stretch",
    )