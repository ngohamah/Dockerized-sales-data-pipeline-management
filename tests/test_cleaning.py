from transform.cleaning import clean_records

VALID_RECORD = {
    "order_id": "abc-123",
    "customer_name": "Jane Doe",
    "product_category": "Books",
    "quantity": "2",
    "unit_price": "9.99",
    "total_amount": "19.98",
    "order_date": "2024-01-01",
    "region": "California",
}


def test_clean_records_keeps_valid_rows():
    cleaned, dropped = clean_records([VALID_RECORD])
    assert dropped == 0
    assert len(cleaned) == 1
    assert cleaned[0]["quantity"] == 2
    assert cleaned[0]["unit_price"] == 9.99


def test_clean_records_drops_rows_missing_required_fields():
    incomplete = {**VALID_RECORD, "customer_name": ""}
    cleaned, dropped = clean_records([VALID_RECORD, incomplete])
    assert dropped == 1
    assert len(cleaned) == 1


def test_clean_records_drops_rows_with_invalid_quantity():
    bad_quantity = {**VALID_RECORD, "order_id": "xyz-999", "quantity": "0"}
    cleaned, dropped = clean_records([bad_quantity])
    assert dropped == 1
    assert cleaned == []


def test_clean_records_drops_rows_with_non_numeric_price():
    bad_price = {**VALID_RECORD, "order_id": "bad-price", "unit_price": "not-a-number"}
    cleaned, dropped = clean_records([bad_price])
    assert dropped == 1
    assert cleaned == []


def test_clean_records_deduplicates_by_order_id():
    duplicate = dict(VALID_RECORD)
    cleaned, dropped = clean_records([VALID_RECORD, duplicate])
    assert len(cleaned) == 1
    assert dropped == 1


def test_clean_records_empty_input_returns_empty_output():
    cleaned, dropped = clean_records([])
    assert cleaned == []
    assert dropped == 0
