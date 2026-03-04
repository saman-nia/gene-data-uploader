import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CsvSummary:
    delimiter: str
    columns: list[str]
    column_count: int
    row_count: int


def detect_delimiter(path: Path) -> str:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(8192)

    candidates = [",", ";", "\t", "|"]

    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=candidates)
        return dialect.delimiter
    except csv.Error:
        first_line = sample.splitlines()[0] if sample else ""
        best_delimiter = max(candidates, key=lambda delimiter: first_line.count(delimiter))
        if first_line.count(best_delimiter) > 0:
            return best_delimiter
        return ","


def analyze_csv(path: Path) -> CsvSummary:
    delimiter = detect_delimiter(path)

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter, quotechar='"')
        try:
            columns = next(reader)
        except StopIteration as exc:
            raise ValueError("CSV file is empty") from exc

        if not columns or all(column.strip() == "" for column in columns):
            raise ValueError("CSV file has no header columns")

        normalized_columns = [column.strip() for column in columns]
        expected_columns = len(normalized_columns)
        row_count = 0

        for row_index, row in enumerate(reader, start=2):
            # Treat fully empty lines as ignorable.
            if not row or all(cell == "" for cell in row):
                continue

            if len(row) != expected_columns:
                raise ValueError(
                    f"Inconsistent column count at row {row_index}: expected {expected_columns}, got {len(row)}"
                )
            row_count += 1

    return CsvSummary(
        delimiter=delimiter,
        columns=normalized_columns,
        column_count=len(normalized_columns),
        row_count=row_count,
    )


def read_csv_rows(path: Path, delimiter: str, offset: int = 0, limit: int | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter, quotechar='"')

        skipped = 0
        while skipped < offset:
            if next(reader, None) is None:
                return []
            skipped += 1

        for row_index, row in enumerate(reader, start=2 + offset):
            if None in row and row[None]:
                raise ValueError(f"Inconsistent column count at row {row_index}")

            if all(value in ("", None) for value in row.values()):
                continue

            if any(value is None for value in row.values()):
                raise ValueError(f"Missing value mapping at row {row_index}")

            if limit is not None and len(rows) >= limit:
                break

            normalized_row: dict[str, str] = {}
            for key, value in row.items():
                if key is None:
                    continue
                normalized_row[key] = value

            rows.append(normalized_row)

    return rows
