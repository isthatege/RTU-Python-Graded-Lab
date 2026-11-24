"""Row validation helpers for the Flight Schedule Parser and Query Tool."""

from datetime import datetime
import math
import re

DATETIME_FORMAT = "%Y-%m-%d %H:%M"

_FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}", re.ASCII)
_AIRPORT_RE = re.compile(r"[A-Z]{3}", re.ASCII)
_DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}", re.ASCII)


def load_airports(path: str) -> set[str]:
    """Read airport list file, one code per line. Strip whitespace, skip blanks and # comments."""
    airports: set[str] = set()
    with open(path, mode="r", encoding="utf-8-sig") as fh:
        for raw_line in fh:
            code = raw_line.strip()
            if code and not code.startswith("#"):
                airports.add(code)
    return airports


def parse_datetime(value: object) -> datetime | None:
    """Parse an exact zero-padded 24-hour 'YYYY-MM-DD HH:MM' timestamp."""
    if not isinstance(value, str) or not _DATETIME_RE.fullmatch(value):
        return None
    try:
        dt = datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        return None
    formatted = f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}"
    return dt if formatted == value else None


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Validate one CSV row (fields from csv.reader, not stripped). Return None if valid, else first error code."""
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    values = [field.strip() for field in fields]
    if any(value == "" for value in values):
        return "MISSING_FIELD"

    flight_id, origin, destination, departure, arrival, price_text = values

    if not _FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"
    if not _AIRPORT_RE.fullmatch(origin) or origin not in airports:
        return "INVALID_ORIGIN"
    if not _AIRPORT_RE.fullmatch(destination) or destination not in airports:
        return "INVALID_DESTINATION"
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    dep_dt = parse_datetime(departure)
    if dep_dt is None:
        return "INVALID_DEPARTURE"

    arr_dt = parse_datetime(arrival)
    if arr_dt is None:
        return "INVALID_ARRIVAL"

    if arr_dt <= dep_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    try:
        price = float(price_text)
    except (TypeError, ValueError, OverflowError):
        return "INVALID_PRICE"

    if not math.isfinite(price):
        return "INVALID_PRICE"
    if price <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Convert valid row to flight record dict."""
    flight_id, origin, destination, departure, arrival, price_text = (
        field.strip() for field in fields
    )
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        "price": float(price_text),
    }