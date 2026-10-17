from io import BytesIO

import pandas as pd

from csv_utils import (
    build_column_profile,
    clean_dataframe,
    dataframe_to_csv_bytes,
    get_overview,
    read_uploaded_csv,
)


class FakeUpload:
    def __init__(self, data: bytes):
        self.data = data

    def getvalue(self):
        return self.data


def test_read_uploaded_csv():
    df = read_uploaded_csv(FakeUpload(b"name,score\nA,10\nB,20\n"))
    assert df.shape == (2, 2)
    assert list(df.columns) == ["name", "score"]


def test_overview_counts_missing_and_duplicates():
    df = pd.DataFrame({"x": [1, 1, None], "y": ["a", "a", "b"]})
    overview = get_overview(df)
    assert overview["rows"] == 3
    assert overview["columns"] == 2
    assert overview["missing_cells"] == 1
    assert overview["duplicate_rows"] == 1


def test_profile_reports_missing_values():
    df = pd.DataFrame({"score": [10, None, 30]})
    profile = build_column_profile(df)
    assert profile.loc[0, "Missing"] == 1
    assert profile.loc[0, "Unique values"] == 2


def test_cleaning_returns_copy_and_removes_duplicates_and_fills_missing():
    original = pd.DataFrame({
        "score": [10.0, 10.0, None],
        "name": [" A ", " A ", None],
    })
    cleaned = clean_dataframe(
        original,
        drop_duplicates=True,
        fill_missing=True,
        fill_strategy="Median for numeric / mode for text",
        trim_text=True,
    )
    assert len(cleaned) == 2
    assert cleaned["score"].isna().sum() == 0
    assert cleaned["name"].isna().sum() == 0
    assert original["name"].iloc[0] == " A "  # original is unchanged


def test_csv_export_has_no_index():
    df = pd.DataFrame({"a": [1], "b": ["x"]})
    csv_text = dataframe_to_csv_bytes(df).decode("utf-8")
    assert csv_text.strip() == "a,b\n1,x"
