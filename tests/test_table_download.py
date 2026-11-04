from io import BytesIO

import pandas as pd

from ui.evidence import table_download


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
