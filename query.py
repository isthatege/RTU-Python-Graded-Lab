"""Row validation: airport list loading, single-row checks, record building."""

import math

from validator import parse_datetime

_RECORD_KEYS = frozenset(
    {
        "flight_id",
        "origin",
        "destination",
        "departure_datetime",
        "arrival_datetime",
        "price",
    }
)
_STRING_KEYS = frozenset({"flight_id", "origin", "destination"})
_DATETIME_KEYS = frozenset({"departure_datetime", "arrival_datetime"})
_NUMBER_KEYS = frozenset({"price", "min_price"})
_ALLOWED_KEYS = _STRING_KEYS | _DATETIME_KEYS | _NUMBER_KEYS | {"sort_by", "order", "limit"}


def _is_valid_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def _is_valid_query(query: object) -> bool:
    if not isinstance(query, dict):
        return False

    for key, value in query.items():
        if key not in _ALLOWED_KEYS:
            return False
        if key in _STRING_KEYS:
            if not isinstance(value, str):
                return False
        elif key in _DATETIME_KEYS:
            if parse_datetime(value) is None:
                return False
        elif key in _NUMBER_KEYS:
            if not _is_valid_number(value):
                return False
        elif key == "sort_by":
            if not isinstance(value, str) or value not in _RECORD_KEYS:
                return False
        elif key == "order":
            if not isinstance(value, str) or value not in ("asc", "desc"):
                return False
        elif key == "limit":
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                return False

    if "order" in query and "sort_by" not in query:
        return False

    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object."""
    if not _is_valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches: list[dict] = []
    for record in db:
        if "flight_id" in query and record["flight_id"] != query["flight_id"]:
            continue
        if "origin" in query and record["origin"] != query["origin"]:
            continue
        if "destination" in query and record["destination"] != query["destination"]:
            continue
        if (
            "departure_datetime" in query
            and record["departure_datetime"] < query["departure_datetime"]
        ):
            continue
        if (
            "arrival_datetime" in query
            and record["arrival_datetime"] > query["arrival_datetime"]
        ):
            continue
        if "price" in query and record["price"] > query["price"]:
            continue
        if "min_price" in query and record["price"] < query["min_price"]:
            continue
        matches.append(dict(record))

    if "sort_by" in query:
        sort_key = query["sort_by"]
        reverse = query.get("order", "asc") == "desc"
        matches = sorted(matches, key=lambda r: r[sort_key], reverse=reverse)

    if "limit" in query:
        matches = matches[: query["limit"]]

    return {"query": query, "matches": matches}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept single query or list; always return list of entries."""
    if isinstance(queries, dict):
        return [run_query(db, queries)]
    if isinstance(queries, list) and all(isinstance(q, dict) for q in queries):
        return [run_query(db, q) for q in queries]
    raise ValueError("Query JSON must be a query object or a list of query objects.")