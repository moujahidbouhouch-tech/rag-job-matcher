import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable, List

from rag_project.config.__init__ import LOG_DIRECTORY, LOG_FILE_NAME, LOG_FORMAT, DEFAULT_LOG_LEVEL


_LOG_DIR = Path(__file__).resolve().parents[1] / LOG_DIRECTORY
_LOG_DIR.mkdir(exist_ok=True)
_LOG_FILE = _LOG_DIR / LOG_FILE_NAME
_LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "2000000"))  # ~2MB per file
_LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # ~10MB total


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger with console and file handlers configured once."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level_name = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)
    fmt = logging.Formatter(LOG_FORMAT)

    # File handler only (keep GUI stdout clean)
    try:
        file_handler = RotatingFileHandler(
            _LOG_FILE, maxBytes=_LOG_MAX_BYTES, backupCount=_LOG_BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    except Exception:
        # If file handler fails (e.g., permissions), fall back to console.
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        logger.addHandler(console)

    logger.propagate = False
    return logger


def iter_logs_newest_first(limit: int | None = None) -> List[str]:
    """
    Utility to read combined logs (current + rotated) with newest entries first.

    This keeps append-order logging while still supporting newest-first display in UIs/CLI.
    """
    files: list[Path] = []
    backups: list[tuple[int, Path]] = []
    for f in _LOG_DIR.glob(f"{_LOG_FILE.name}.*"):
        try:
            num = int(f.suffix.lstrip("."))
            backups.append((num, f))
        except ValueError:
            continue
    # Oldest first: highest number down to 1
    for _, f in sorted(backups, reverse=True):
        files.append(f)
    files.append(_LOG_FILE)

    lines: list[str] = []
    for f in files:
        try:
            lines.extend(f.read_text(encoding="utf-8").splitlines())
        except FileNotFoundError:
            continue
    newest_first = list(reversed(lines))
    return newest_first[:limit] if limit is not None else newest_first
