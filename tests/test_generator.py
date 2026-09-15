from data_generator.generator import generate_record, generate_records

REQUIRED_KEYS = {
    "order_id",
    "customer_name",
    "product_category",
    "quantity",
    "unit_price",
    "total_amount",
    "order_date",
    "region",
}


def test_generate_record_has_required_fields():
    record = generate_record()
    assert REQUIRED_KEYS.issubset(record.keys())


def test_generate_record_total_matches_quantity_times_price():
    record = generate_record()
    assert record["total_amount"] == round(record["quantity"] * record["unit_price"], 2)


def test_generate_records_returns_requested_count():
    records = generate_records(25)
    assert len(records) == 25
    assert all(REQUIRED_KEYS.issubset(r.keys()) for r in records)


def test_generate_records_zero_returns_empty_list():
    assert generate_records(0) == []


def test_generate_records_order_ids_are_unique():
    records = generate_records(50)
    order_ids = [r["order_id"] for r in records]
    assert len(order_ids) == len(set(order_ids))
