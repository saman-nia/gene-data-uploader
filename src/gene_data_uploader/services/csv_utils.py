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
