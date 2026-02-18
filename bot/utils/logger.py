"""Structured logging configuration using structlog.

In ``development`` mode logs are rendered as coloured, human-readable text.
In ``production`` mode logs are emitted as JSON for log aggregators.

Usage::

    from bot.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("user_registered", user_id=42, username="john")
"""

from __future__ import annotations

import logging
import sys

import structlog

from bot.config import settings


def configure_logging() -> None:
    """Initialise structlog and stdlib logging.

    Call once at application startup (already called in ``main.py``).
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_json or settings.is_production:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Silence noisy third-party loggers
    for noisy in ("aiogram", "aiohttp", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(
            logging.DEBUG if settings.debug else logging.WARNING
        )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog logger bound to *name*.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        Configured :class:`structlog.stdlib.BoundLogger`.
    """
    return structlog.get_logger(name)  # type: ignore[return-value]
