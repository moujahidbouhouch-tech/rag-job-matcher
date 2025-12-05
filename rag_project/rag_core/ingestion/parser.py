from pathlib import Path
from typing import Optional

from rag_project.config import (
    PARSER_TEXT_SUFFIXES,
    PARSER_PDF_SUFFIX,
    PARSER_PDF_DEPENDENCY_MESSAGE,
)
from rag_project.logger import get_logger


logger = get_logger(__name__)


def parse_job(title: str, body: str, metadata: Optional[dict] = None) -> str:
    """Simple job text parser; can be extended with HTML stripping/cleanup."""
    parts = [title.strip()] if title else []
    parts.append(body.strip())
    if metadata and metadata.get("location"):
        parts.append(f"Location: {metadata['location']}")
    return "\n\n".join(filter(None, parts))


def parse_file(file_path: Path) -> str:
    """Minimal file loader with basic branching on suffix (txt/md/html/pdf)."""
    suffix = file_path.suffix.lower()
    if suffix in PARSER_TEXT_SUFFIXES:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    if suffix == PARSER_PDF_SUFFIX:
        try:
            import pymupdf4llm  # type: ignore
        except ImportError:
            logger.error("PDF parse requested but pymupdf4llm is missing")
            raise RuntimeError(PARSER_PDF_DEPENDENCY_MESSAGE)
        return pymupdf4llm.to_markdown(str(file_path))
    # Fallback: read as text
    logger.warning("Parsing file with unsupported suffix=%s; falling back to text read", suffix)
    return file_path.read_text(encoding="utf-8", errors="ignore")
