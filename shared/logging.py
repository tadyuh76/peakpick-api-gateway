from __future__ import annotations

import json
import logging
import sys
from typing import Any


def configure_logging(service_name: str) -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    return logging.getLogger(service_name)


def log_event(logger: logging.Logger, service_name: str, message: str, **fields: Any) -> None:
    logger.info(json.dumps({"service": service_name, "message": message, **fields}))

