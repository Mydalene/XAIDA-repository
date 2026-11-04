import pandas as pd
import streamlit as st


def render_table_download(
    dataframe,
    table_name,
    key,
):
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("Table downloads require a pandas DataFrame.")

    download_dataframe = dataframe.copy()
    text_columns = download_dataframe.select_dtypes(
        include=["object", "string"]
    ).columns
    for column in text_columns:
        download_dataframe[column] = download_dataframe[column].map(
            _escape_spreadsheet_formula
        )

    st.download_button(
        label=f"Download {table_name} CSV",
        data=download_dataframe.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{key}.csv",
        mime="text/csv",
        key=f"download_{key}",
    )


def _escape_spreadsheet_formula(value):
    if isinstance(value, str):
        normalized_value = value.lstrip(" \t\r\n")
        if normalized_value.startswith(("=", "+", "-", "@")):
            return f"'{value}"
    return value
