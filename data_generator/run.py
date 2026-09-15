"""Entry point: generate a batch of synthetic sales records and upload them
to MinIO once. This is the data-generator container's CMD.
"""
from __future__ import annotations

import sys

from config import constants
from config.logging_setup import get_logger
from data_generator.generator import generate_records
from data_generator.uploader import upload_batch

logger = get_logger(__name__, constants.DATA_GENERATOR_LOG_FILE)


def main(count: int = constants.DEFAULT_RECORD_COUNT) -> int:
    try:
        records = generate_records(count)
        logger.info("Generated %d synthetic records", len(records))
        key = upload_batch(records)
        logger.info("Batch upload complete: %s", key)
        return 0
    except Exception:
        logger.error("Data generator run failed", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
