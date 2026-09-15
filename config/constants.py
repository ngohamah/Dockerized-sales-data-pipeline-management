"""Constants, paths, and env-var names used across the platform.

Nothing here changes during the project's lifecycle. Actual secret values
live in `.env` (gitignored) and are read via `os.environ` at call sites,
using the *names* defined here.
"""
from __future__ import annotations

from pathlib import Path

# --- Filesystem paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
DATA_GENERATOR_LOG_FILE = LOG_DIR / "data_generator.log"
PIPELINE_LOG_FILE = LOG_DIR / "pipeline.log"

# --- MinIO / S3 (env var names, not values) ---
MINIO_ENDPOINT_ENV = "MINIO_ENDPOINT"
MINIO_ACCESS_KEY_ENV = "MINIO_ROOT_USER"
MINIO_SECRET_KEY_ENV = "MINIO_ROOT_PASSWORD"

RAW_BUCKET = "raw-data"
RAW_PREFIX = "incoming/"
PROCESSED_PREFIX = "processed/"

# --- Postgres (env var names, not values) ---
POSTGRES_HOST_ENV = "POSTGRES_HOST"
POSTGRES_PORT_ENV = "POSTGRES_PORT"
POSTGRES_USER_ENV = "POSTGRES_USER"
POSTGRES_PASSWORD_ENV = "POSTGRES_PASSWORD"

APP_DATABASE_NAME = "app_data"
SALES_TABLE_NAME = "sales_records"

# --- Data generation ---
DEFAULT_RECORD_COUNT = 500
CSV_FILENAME_PREFIX = "sales_batch_"

# --- Logging ---
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_LEVEL = "INFO"
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3
