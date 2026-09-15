import pytest
from moto import mock_aws

from config import constants
from data_generator.uploader import upload_batch


@pytest.fixture(autouse=True)
def _minio_credentials(monkeypatch):
    # MINIO_ENDPOINT is deliberately left unset here: with no override,
    # boto3 falls back to the standard AWS endpoint resolution, which is
    # exactly what moto's mock_aws intercepts.
    monkeypatch.setenv(constants.MINIO_ACCESS_KEY_ENV, "test-access-key")
    monkeypatch.setenv(constants.MINIO_SECRET_KEY_ENV, "test-secret-key")


@mock_aws
def test_upload_batch_writes_single_csv_object():
    import boto3

    records = [{"order_id": "1", "customer_name": "Test Customer"}]

    key = upload_batch(records)

    assert key.startswith(constants.RAW_PREFIX)
    client = boto3.client("s3", region_name="us-east-1")
    body = client.get_object(Bucket=constants.RAW_BUCKET, Key=key)["Body"].read()
    assert b"order_id" in body
    assert b"Test Customer" in body


def test_upload_batch_raises_on_empty_records():
    with pytest.raises(ValueError):
        upload_batch([])
