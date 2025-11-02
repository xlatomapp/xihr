"""Structured logging configuration helpers."""

from __future__ import annotations

import logging
from typing import Mapping


def configure_logging(level: int = logging.INFO, extra: Mapping[str, str] | None = None) -> None:
    """Configure standard library logging with structured context."""

    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if extra:
        logger = logging.getLogger()
        for key, value in extra.items():
            logger = logging.LoggerAdapter(logger, {key: value})


__all__ = ["configure_logging"]
