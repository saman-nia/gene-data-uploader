from pathlib import Path

import pytest

from gene_data_uploader.services.csv_utils import analyze_csv, read_csv_rows


def test_analyze_csv_detects_semicolon_delimiter(tmp_path: Path):
    sample_path = tmp_path / "sample.csv"
    sample_path.write_text(
        "id;name;description\n"
        "1;TP53;\"Tumor protein; with semicolon\"\n"
        "2;BRCA1;DNA repair\n",
        encoding="utf-8",
    )

    summary = analyze_csv(sample_path)

    assert summary.delimiter == ";"
    assert summary.columns == ["id", "name", "description"]
    assert summary.column_count == 3
    assert summary.row_count == 2


def test_read_csv_rows_supports_offset_and_limit(tmp_path: Path):
    sample_path = tmp_path / "sample.csv"
    sample_path.write_text(
        "id;name\n"
        "1;A\n"
        "2;B\n"
        "3;C\n",
        encoding="utf-8",
    )

    rows = read_csv_rows(sample_path, delimiter=";", offset=1, limit=1)

    assert rows == [{"id": "2", "name": "B"}]


def test_analyze_csv_rejects_inconsistent_row_shape(tmp_path: Path):
    sample_path = tmp_path / "invalid.csv"
    sample_path.write_text(
        "id;name\n"
        "1;A\n"
        "2\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Inconsistent column count"):
        analyze_csv(sample_path)
