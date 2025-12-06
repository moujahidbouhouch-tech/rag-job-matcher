import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pytest

from rag_project.rag_core.ingestion.parser import parse_file, parse_job
from rag_project.config import (
    PDF_PARSER,
    USE_PYMUPDF_FOR_PDF,
    GENERAL_FILTER_ENABLED,
    THESIS_FILTER_ENABLED,
    CHUNK_STRATEGY,
    CV_CHUNKER_MODEL_ID,
    CV_CHUNKER_MAX_OUTPUT_TOKENS,
    INGEST_DEBUG_LOG_CHUNKS,
    INGEST_DEBUG_LOG_PATH,
)


@dataclass
class ParsedDocument:
    text: str
    metadata: Dict[str, Any]


def _install_fake_pdf_module(
    monkeypatch, return_value=None, exc: Exception | None = None
):
    """Inject a fake pymupdf4llm module so parse_file can run without the real dependency."""

    class FakePdfModule:
        @staticmethod
        def to_markdown(path: str):
            if exc:
                raise exc
            return return_value or f"fake content for {path}"

    monkeypatch.setitem(sys.modules, "pymupdf4llm", FakePdfModule())


def test_parsing_service_pdf_to_text_simple(tmp_path, monkeypatch):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%stub\n")
    _install_fake_pdf_module(monkeypatch, return_value="Simple PDF text")

    text = parse_file(pdf_path)

    assert "Simple PDF text" in text


def test_parsing_service_pdf_multi_page(tmp_path, monkeypatch):
    pdf_path = tmp_path / "multi.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%stub\n")
    _install_fake_pdf_module(
        monkeypatch, return_value="Page 1 content\n\nPage 2 content"
    )

    text = parse_file(pdf_path)

    assert "Page 1 content" in text and "Page 2 content" in text


def test_parsing_service_pdf_corrupted_raises(tmp_path, monkeypatch):
    pdf_path = tmp_path / "corrupt.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%stub\n")
    _install_fake_pdf_module(monkeypatch, exc=RuntimeError("broken pdf"))

    with pytest.raises(RuntimeError):
        parse_file(pdf_path)


def test_parsing_service_markdown_to_text(tmp_path):
    md_path = tmp_path / "doc.md"
    md_path.write_text(
        "# Heading\n\n- item 1\n- item 2\n\n[link](http://example.com)",
        encoding="utf-8",
    )

    text = parse_file(md_path)

    assert "# Heading" in text
    assert "- item 1" in text
    assert "http://example.com" in text


def test_parsing_service_json_job_normalized(tmp_path):
    job = {
        "title": "Data Scientist",
        "company": "Acme",
        "description": "Analyze data and build models.",
        "location": "Berlin",
    }
    json_path = tmp_path / "job.json"
    json_path.write_text(json.dumps(job), encoding="utf-8")

    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    normalized = parse_job(
        loaded.get("title"),
        loaded.get("description"),
        metadata={"company": loaded["company"], "location": loaded["location"]},
    )

    assert "Data Scientist" in normalized
    assert "Analyze data" in normalized
    assert "Location: Berlin" in normalized


def test_parsing_service_empty_file(tmp_path):
    txt_path = tmp_path / "empty.txt"
    txt_path.write_text("   \n", encoding="utf-8")

    text = parse_file(txt_path)

    assert text.strip() == ""


def test_parsing_service_missing_fields_in_json():
    normalized = parse_job(title="", body="", metadata=None)

    assert normalized == ""


def test_parsing_service_integration_file_to_document(tmp_path, monkeypatch):
    pdf_path = tmp_path / "full.pdf"
    md_path = tmp_path / "full.md"
    json_path = tmp_path / "full.json"

    pdf_path.write_bytes(b"%PDF-1.4\n%stub\n")
    _install_fake_pdf_module(monkeypatch, return_value="PDF text block")
    md_path.write_text("## Doc Title\nContent body", encoding="utf-8")
    json_path.write_text(
        json.dumps({"title": "T", "description": "Body"}), encoding="utf-8"
    )

    pdf_doc = ParsedDocument(parse_file(pdf_path), {"type": "pdf"})
    md_doc = ParsedDocument(parse_file(md_path), {"type": "md"})
    json_doc = ParsedDocument(parse_file(json_path), {"type": "json"})

    assert "PDF text block" in pdf_doc.text and pdf_doc.metadata["type"] == "pdf"
    assert "Doc Title" in md_doc.text and md_doc.metadata["type"] == "md"
    assert "Body" in json_doc.text and json_doc.metadata["type"] == "json"


def test_parsing_config_defaults_present():
    assert PDF_PARSER == "pymupdf"
    assert USE_PYMUPDF_FOR_PDF is True
    assert GENERAL_FILTER_ENABLED is True
    assert THESIS_FILTER_ENABLED is True
    assert CHUNK_STRATEGY.get("cv") == "llm_cv_chunker"
    assert CHUNK_STRATEGY.get("default") == "structured"
    assert isinstance(CV_CHUNKER_MODEL_ID, str) and CV_CHUNKER_MODEL_ID
    assert isinstance(CV_CHUNKER_MAX_OUTPUT_TOKENS, (int, float))
    assert INGEST_DEBUG_LOG_CHUNKS in (True, False)
    assert isinstance(INGEST_DEBUG_LOG_PATH, str) and INGEST_DEBUG_LOG_PATH
