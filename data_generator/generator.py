"""Pure functions that produce synthetic sales records.

No I/O here on purpose: every function is deterministic-in-shape and testable
in isolation, independent of MinIO/upload concerns (see `uploader.py`).
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from faker import Faker

fake = Faker()

PRODUCT_CATEGORIES = ("Electronics", "Home & Garden", "Clothing", "Sports", "Books", "Toys")


def _random_order_date(max_days_ago: int = 90) -> str:
    days_ago = random.randint(0, max_days_ago)
    return (datetime.utcnow() - timedelta(days=days_ago)).date().isoformat()


def generate_record() -> dict:
    """Returns one synthetic sales order as a plain dict."""
    quantity = random.randint(1, 10)
    unit_price = round(random.uniform(5.0, 500.0), 2)
    return {
        "order_id": fake.uuid4(),
        "customer_name": fake.name(),
        "product_category": random.choice(PRODUCT_CATEGORIES),
        "quantity": quantity,
        "unit_price": unit_price,
        "total_amount": round(quantity * unit_price, 2),
        "order_date": _random_order_date(),
        "region": fake.state(),
    }


def generate_records(count: int) -> list[dict]:
    """Returns `count` synthetic sales orders."""
    return [generate_record() for _ in range(count)]
