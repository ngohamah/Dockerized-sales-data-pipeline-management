"""Shared logging configuration used by every component of the pipeline.

Every script that touches a file or an external service should log through
`get_logger` so file drops/writes/skips are traceable in one place.
"""
from __future__ import annotations

import logging
from functools import cache
from logging.handlers import RotatingFileHandler
from pathlib import Path

from config import constants


@cache
def get_logger(name: str, log_file: Path) -> logging.Logger:
    """Returns a logger configured once per (name, log_file) pair.

    Cached so repeated calls (e.g. across Airflow task retries) never attach
    duplicate handlers to the same logger.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(constants.LOG_LEVEL)
    logger.propagate = False

    formatter = logging.Formatter(constants.LOG_FORMAT)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=constants.LOG_MAX_BYTES, backupCount=constants.LOG_BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
