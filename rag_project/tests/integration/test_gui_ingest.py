import uuid
from pathlib import Path

import pytest

from rag_project.rag_gui.main import IngestWorker


class FakeIngestion:
    def __init__(self):
        self.called_with = None

    def ingest_file(self, file_path: str, metadata=None, progress_cb=None):
        self.called_with = (file_path, metadata)
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

    worker = IngestWorker(app, [str(dummy_file)], {"doc_type": DOC_TYPE_CV})

    stages = []
    details = []
    messages = []

    worker.progress_stage.connect(lambda v: stages.append(v))
    worker.progress_detail.connect(lambda v: details.append(v))
    worker.finished.connect(lambda msg: messages.append(msg))
    worker.error.connect(lambda msg: messages.append(f"error:{msg}"))

    worker.run()

    assert app.ingestion.called_with[0] == str(dummy_file)
    assert stages and stages[-1] == 100
    assert details and details[-1] == 100
    assert messages and "ingestions completed" in messages[-1].lower()


def test_ingest_worker_handles_missing_file(tmp_path):
    missing_file = tmp_path / "missing.json"
    app = FakeApp()
    from rag_project.config import DOC_TYPE_JOB_POSTING

    worker = IngestWorker(app, [str(missing_file)], {"doc_type": DOC_TYPE_JOB_POSTING})

    errors = []
    worker.error.connect(errors.append)
    worker.run()

    assert errors, "Expected error signal for missing file"
    # Accept any error string that includes the missing path
    assert str(missing_file) in errors[-1]
