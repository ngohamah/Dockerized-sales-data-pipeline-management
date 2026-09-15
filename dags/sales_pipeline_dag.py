"""Airflow DAG: sense a new file in MinIO, clean it, load it into Postgres,
then archive the source file.

`config/` and `transform/` are mounted next to `dags/` inside the Airflow
container with PYTHONPATH=/opt/airflow (see docker-compose.yml), so they
import here exactly as they do in the unit tests.
"""
from __future__ import annotations

import csv
import io
import os
from datetime import datetime, timedelta

import boto3
from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import create_engine, text

from config import constants
from config.logging_setup import get_logger
from transform.cleaning import clean_records

logger = get_logger(__name__, constants.PIPELINE_LOG_FILE)

default_args = {
    "owner": "data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def _minio_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ[constants.MINIO_ENDPOINT_ENV],
        aws_access_key_id=os.environ[constants.MINIO_ACCESS_KEY_ENV],
        aws_secret_access_key=os.environ[constants.MINIO_SECRET_KEY_ENV],
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _postgres_engine():
    conn_str = (
        f"postgresql+psycopg2://{os.environ[constants.POSTGRES_USER_ENV]}:"
        f"{os.environ[constants.POSTGRES_PASSWORD_ENV]}@"
        f"{os.environ.get(constants.POSTGRES_HOST_ENV, 'postgres')}:"
        f"{os.environ.get(constants.POSTGRES_PORT_ENV, '5432')}/{constants.APP_DATABASE_NAME}"
    )
    return create_engine(conn_str)


@dag(
    dag_id="sales_pipeline",
    description="MinIO (raw CSV) -> clean -> Postgres app_data",
    schedule="*/10 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["mini-data-platform"],
)
def sales_pipeline():
    @task
    def sense_new_file() -> str:
        client = _minio_client()
        try:
            response = client.list_objects_v2(Bucket=constants.RAW_BUCKET, Prefix=constants.RAW_PREFIX)
            keys = sorted(
                obj["Key"] for obj in response.get("Contents", []) if obj["Key"] != constants.RAW_PREFIX
            )
            if not keys:
                logger.info("No new files found under s3://%s/%s", constants.RAW_BUCKET, constants.RAW_PREFIX)
                raise AirflowSkipException("No new files to process")
            key = keys[0]
            logger.info("Detected new file: %s", key)
            return key
        except (BotoCoreError, ClientError) as exc:
            logger.error("Failed to list MinIO objects: %s", exc, exc_info=True)
            raise
        finally:
            client.close()

    @task
    def transform_file(key: str) -> dict:
        client = _minio_client()
        try:
            obj = client.get_object(Bucket=constants.RAW_BUCKET, Key=key)
            raw_bytes = obj["Body"].read()
            raw_records = list(csv.DictReader(io.StringIO(raw_bytes.decode("utf-8"))))
            cleaned, dropped = clean_records(raw_records)
            if dropped:
                logger.warning("Dropped %d invalid/duplicate rows from %s", dropped, key)
            logger.info("Cleaned %d/%d rows from %s", len(cleaned), len(raw_records), key)
            return {"key": key, "records": cleaned}
        except (BotoCoreError, ClientError) as exc:
            logger.error("Failed to download/transform %s: %s", key, exc, exc_info=True)
            raise
        finally:
            client.close()

    @task
    def load_to_postgres(payload: dict) -> str:
        records, key = payload["records"], payload["key"]
        if not records:
            logger.warning("No valid records to load from %s", key)
            return key

        engine = _postgres_engine()
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        f"""
                        CREATE TABLE IF NOT EXISTS {constants.SALES_TABLE_NAME} (
                            order_id TEXT PRIMARY KEY,
                            customer_name TEXT,
                            product_category TEXT,
                            quantity INTEGER,
                            unit_price NUMERIC,
                            total_amount NUMERIC,
                            order_date DATE,
                            region TEXT
                        )
                        """
                    )
                )
                for record in records:
                    conn.execute(
                        text(
                            f"""
                            INSERT INTO {constants.SALES_TABLE_NAME}
                                (order_id, customer_name, product_category, quantity,
                                 unit_price, total_amount, order_date, region)
                            VALUES
                                (:order_id, :customer_name, :product_category, :quantity,
                                 :unit_price, :total_amount, :order_date, :region)
                            ON CONFLICT (order_id) DO NOTHING
                            """
                        ),
                        record,
                    )
            logger.info("Loaded %d records from %s into %s", len(records), key, constants.SALES_TABLE_NAME)
            return key
        except Exception as exc:
            logger.error("Failed to load records from %s into Postgres: %s", key, exc, exc_info=True)
            raise
        finally:
            engine.dispose()

    @task
    def archive_file(key: str) -> None:
        client = _minio_client()
        try:
            filename = key.rsplit("/", 1)[-1]
            new_key = f"{constants.PROCESSED_PREFIX}{filename}"
            client.copy_object(
                Bucket=constants.RAW_BUCKET,
                CopySource={"Bucket": constants.RAW_BUCKET, "Key": key},
                Key=new_key,
            )
            client.delete_object(Bucket=constants.RAW_BUCKET, Key=key)
            logger.info("Archived %s -> %s", key, new_key)
        except (BotoCoreError, ClientError) as exc:
            logger.error("Failed to archive %s: %s", key, exc, exc_info=True)
            raise
        finally:
            client.close()

    sensed_key = sense_new_file()
    transformed = transform_file(sensed_key)
    loaded_key = load_to_postgres(transformed)
    archive_file(loaded_key)


sales_pipeline()
