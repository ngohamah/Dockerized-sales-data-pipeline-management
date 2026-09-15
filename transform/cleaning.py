"""Pure functions for cleaning/validating raw sales records before they are
loaded into Postgres. No I/O and no logging here on purpose, so the Airflow
DAG (which does the logging) and the unit tests can both drive this module
without any external service.
"""
from __future__ import annotations

REQUIRED_FIELDS = (
    "order_id",
    "customer_name",
    "product_category",
    "quantity",
    "unit_price",
    "total_amount",
    "order_date",
    "region",
)


def _is_complete(record: dict) -> bool:
    return all(field in record and record[field] not in (None, "") for field in REQUIRED_FIELDS)


def _has_valid_amounts(record: dict) -> bool:
    try:
        return float(record["quantity"]) > 0 and float(record["unit_price"]) >= 0
    except (TypeError, ValueError):
        return False


def _is_valid_record(record: dict) -> bool:
    return _is_complete(record) and _has_valid_amounts(record)


def _coerce_types(record: dict) -> dict:
    return {
        **record,
        "quantity": int(float(record["quantity"])),
        "unit_price": round(float(record["unit_price"]), 2),
        "total_amount": round(float(record["total_amount"]), 2),
    }


def _dedupe(records: list[dict]) -> list[dict]:
    seen: set[str] = set()
    deduped = []
    for record in records:
        order_id = record["order_id"]
        if order_id in seen:
            continue
        seen.add(order_id)
        deduped.append(record)
    return deduped


def clean_records(raw_records: list[dict]) -> tuple[list[dict], int]:
    """Validates, coerces, and de-duplicates raw records.

    Returns `(cleaned_records, dropped_count)` so the caller can log how many
    rows were dropped (invalid or duplicate) for observability.
    """
    valid = [_coerce_types(r) for r in raw_records if _is_valid_record(r)]
    deduped = _dedupe(valid)
    dropped = len(raw_records) - len(deduped)
    return deduped, dropped
