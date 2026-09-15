"""Batch-uploads generated records to MinIO as a single CSV.

Per project rule: any external-service call happens once per run, as a
single session that is opened, used, and explicitly closed — avoiding
repeated calls that could trip rate limits.
"""
from __future__ import annotations

import csv
import io
import os
from datetime import datetime

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

from config import constants
from config.logging_setup import get_logger

logger = get_logger(__name__, constants.DATA_GENERATOR_LOG_FILE)


def _build_client():
    """Builds one boto3 S3 client. `endpoint_url` is only overridden when
    MINIO_ENDPOINT is set (real/Docker runs); left unset it falls back to
    boto3's normal AWS resolution, which is what makes this mockable with
    moto in tests without special-casing test code.
    """
    endpoint = os.environ.get(constants.MINIO_ENDPOINT_ENV)
    kwargs = {
        "aws_access_key_id": os.environ.get(constants.MINIO_ACCESS_KEY_ENV),
        "aws_secret_access_key": os.environ.get(constants.MINIO_SECRET_KEY_ENV),
        "config": Config(signature_version="s3v4"),
        "region_name": "us-east-1",
    }
    if endpoint:
        kwargs["endpoint_url"] = endpoint
    return boto3.client("s3", **kwargs)


def _records_to_csv_bytes(records: list[dict]) -> bytes:
    if not records:
        raise ValueError("no records to serialize")
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)
    return buffer.getvalue().encode("utf-8")


def _ensure_bucket(client, bucket: str) -> None:
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError:
        client.create_bucket(Bucket=bucket)
        logger.info("Created missing bucket '%s'", bucket)


def upload_batch(records: list[dict]) -> str:
    """Uploads all records as one CSV file in a single MinIO session.

    Returns the object key written. Raises on any failure, after logging it.
    """
    filename = f"{constants.CSV_FILENAME_PREFIX}{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.csv"
    key = f"{constants.RAW_PREFIX}{filename}"

    payload = _records_to_csv_bytes(records)

    client = _build_client()
    try:
        _ensure_bucket(client, constants.RAW_BUCKET)
        client.put_object(Bucket=constants.RAW_BUCKET, Key=key, Body=payload)
        logger.info(
            "Uploaded %d records to s3://%s/%s (%d bytes)",
            len(records),
            constants.RAW_BUCKET,
            key,
            len(payload),
        )
        return key
    except (BotoCoreError, ClientError) as exc:
        logger.error("Failed to upload batch to MinIO: %s", exc, exc_info=True)
        raise
    finally:
        client.close()
