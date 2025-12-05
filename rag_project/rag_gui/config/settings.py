"""Behavioral settings, options, weights, and timeouts."""

from rag_project.config import SUPPORTED_DOC_TYPES

DOC_TYPE_OPTIONS = list(SUPPORTED_DOC_TYPES)

# Ingestion/progress weights
PROGRESS_STAGE_WEIGHTS = {"parse": 0.1, "chunk": 0.35, "embed": 0.4, "write": 0.15}
GUI_INGEST_STAGE_WEIGHTS = PROGRESS_STAGE_WEIGHTS

# Timeouts and delays
GUI_DB_CHECK_TIMEOUT = 5
GUI_JOBLOADER_DB_TIMEOUT = 10
GUI_CHAT_SIMULATED_DELAY = 1.5
GUI_DISK_USAGE_PATH = "/"
GUI_DB_OVERVIEW_TIMEOUT = 10

# Regex / parsing
GUI_CHUNK_COUNT_REGEX = r"Chunking complete: (\d+) chunks"

# Options
GUI_DELETE_FILTER_OPTIONS = ["Choose document type", "All Documents"]

__all__ = [
    "DOC_TYPE_OPTIONS",
    "PROGRESS_STAGE_WEIGHTS",
    "GUI_INGEST_STAGE_WEIGHTS",
    "GUI_DB_CHECK_TIMEOUT",
    "GUI_JOBLOADER_DB_TIMEOUT",
    "GUI_CHAT_SIMULATED_DELAY",
    "GUI_DISK_USAGE_PATH",
    "GUI_DB_OVERVIEW_TIMEOUT",
    "GUI_CHUNK_COUNT_REGEX",
    "GUI_DELETE_FILTER_OPTIONS",
]
