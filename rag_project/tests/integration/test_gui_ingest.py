import uuid
from pathlib import Path

import pytest

from rag_project.rag_gui.workers.ingestion_worker import IngestionWorker


class FakeIngestion:
    def __init__(self):
        self.called_with = None
    
    def ingest_file(self, file_path: str, metadata=None, progress_cb=None):
        # 1. Simulate Error for "missing file" test
        if "missing" in str(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        self.called_with = (file_path, metadata)
        
        # 2. Simulate Success Callback so "ingestion completed" log appears
        if progress_cb:
             progress_cb("done", {"message": "Ingestion completed"})
        
        return uuid.uuid4()


class FakeApp:
    def __init__(self):
        self.ingestion = FakeIngestion()


@pytest.fixture
def sample_files(tmp_path):
    paths = {}
    paths["txt"] = tmp_path / "sample.txt"
    paths["txt"].write_text("dummy content", encoding="utf-8")
    paths["json"] = tmp_path / "sample.json"
    paths["json"].write_text('{"key": "value"}', encoding="utf-8")
    paths["md"] = tmp_path / "sample.md"
    paths["md"].write_text("# Title\n\nBody text.", encoding="utf-8")
    paths["html"] = tmp_path / "sample.html"
    paths["html"].write_text("<html><body><p>Hello</p></body></html>", encoding="utf-8")
    paths["pdf"] = tmp_path / "sample.pdf"
    paths["pdf"].write_bytes(b"%PDF-1.4\n%fake\n")  # stub header
    return paths


def test_ingest_worker_emits_progress_and_finishes(sample_files):
    dummy_file = sample_files["txt"]

    app = FakeApp()
    from rag_project.config import DOC_TYPE_CV

    worker = IngestionWorker(app, [str(dummy_file)], {"doc_type": DOC_TYPE_CV})

    stages = []
    details = []
    messages = []

    worker.progress_updated.connect(lambda c, t: stages.append(c))
    worker.progress_detail.connect(lambda v: details.append(v))
    worker.log_message.connect(lambda msg: messages.append(msg))
    worker.error_occurred.connect(lambda msg: messages.append(f"error:{msg}"))
    
    worker.run()

    assert app.ingestion.called_with[0] == str(dummy_file)
    assert any("ingestion completed" in m.lower() for m in messages)

def test_ingest_worker_handles_missing_file(tmp_path):
    missing_file = tmp_path / "missing.json"
    app = FakeApp()
    from rag_project.config import DOC_TYPE_JOB_POSTING

    worker = IngestionWorker(app, [str(missing_file)], {"doc_type": DOC_TYPE_JOB_POSTING})

    errors = []
    worker.error_occurred.connect(errors.append)
    worker.run()

    assert errors, "Expected error signal for missing file"
    assert "error" in errors[-1].lower() or str(missing_file) in errors[-1]
