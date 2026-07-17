"""Structured logging setup.

Per the security design, logs never carry email content or PII — only structural
metadata and correlation info. This M0 version configures a clean, level-aware
console logger; a JSON formatter and per-scan correlation IDs arrive with the
scan pipeline in later milestones.
"""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s :: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
