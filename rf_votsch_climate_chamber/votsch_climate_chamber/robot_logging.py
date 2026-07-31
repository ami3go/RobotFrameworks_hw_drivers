"""Bridge standard Python logging records into Robot Framework's log.

The driver deliberately depends only on Python's logging module.  This handler
is attached by the adapter so driver messages appear in ``log.html`` without
coupling the driver to Robot Framework.
"""

from __future__ import annotations

import logging

from robot.api import logger as robot_logger


class RobotLogHandler(logging.Handler):
    """Forward driver log records to the matching Robot log level."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            if record.levelno >= logging.ERROR:
                robot_logger.error(message)
            elif record.levelno >= logging.WARNING:
                robot_logger.warn(message)
            elif record.levelno >= logging.INFO:
                robot_logger.info(message)
            else:
                robot_logger.debug(message)
        except Exception:
            # Logging must never break instrument control or test teardown.
            self.handleError(record)


def create_robot_logger(name: str = "votsch_climate_chamber.driver") -> logging.Logger:
    """Return a non-propagating logger configured for Robot output."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if not any(isinstance(handler, RobotLogHandler) for handler in logger.handlers):
        handler = RobotLogHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(handler)
    return logger
