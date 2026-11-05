from io import BytesIO

import pandas as pd
import pyarrow as pa

from ui.evidence import table_download


def test_dataframe_for_streamlit_formats_mixed_object_columns():
    dataframe = pd.DataFrame(
        {
            "Mixed": pd.Series(
                [b"source", pd.Timestamp("2026-11-05 13:53:00")],
                dtype=object,
            ),
            "Text": ["first", "second"],
        }
    )

    display_dataframe = table_download.dataframe_for_streamlit(dataframe)

    assert display_dataframe["Mixed"].tolist() == [
        "source",
        "2026-11-05 13:53:00",
    ]
    assert dataframe["Mixed"].tolist() == [
        b"source",
        pd.Timestamp("2026-11-05 13:53:00"),
    ]
    pa.Table.from_pandas(display_dataframe, preserve_index=False)


def test_table_download_escapes_spreadsheet_formulas_and_preserves_numbers(
    monkeypatch,
):
    download = {}
    monkeypatch.setattr(
        table_download.st,
        "download_button",
        lambda **kwargs: download.update(kwargs),
    )
    dataframe = pd.DataFrame(
        {
            "Description": ["=1+1", "  @SUM(A1:A2)", "ordinary text"],
            "Amount": [-12, 4, 8],
        }
    )

    table_download.render_table_download(
        dataframe,
        "Test Table",
        "test_table",
    )

    downloaded = pd.read_csv(
        BytesIO(download["data"]),
        encoding="utf-8-sig",
    )
    assert downloaded["Description"].tolist() == [
        "'=1+1",
        "'  @SUM(A1:A2)",
        "ordinary text",
    ]
    assert downloaded["Amount"].tolist() == [-12, 4, 8]
