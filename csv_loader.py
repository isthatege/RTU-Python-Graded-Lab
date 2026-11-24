"""Reading CSV files into flight records and error messages."""

import csv
import os

from validator import to_record, validate_row


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process CSV files in order. Return (records, errors)."""
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    for path in paths:
        filename = os.path.basename(os.fspath(path))
        with open(path, mode="r", encoding="utf-8-sig", newline="") as fh:
            for line_number, raw_line in enumerate(fh, start=1):
                if line_number == 1:
                    continue

                stripped = raw_line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                line = raw_line.rstrip("\r\n")
                try:
                    fields = next(csv.reader([line]))
                except (csv.Error, StopIteration):
                    fields = []

                error_code = validate_row(fields, airports)
                if error_code is None:
                    record = to_record(fields)
                    duplicate_key = (record["flight_id"], record["departure_datetime"])
                    if duplicate_key in seen:
                        error_code = "DUPLICATE_FLIGHT"
                    else:
                        seen.add(duplicate_key)
                        records.append(record)

                if error_code is not None:
                    errors.append(f"{filename}:{line_number}: {error_code} | {line}")

    return records, errors