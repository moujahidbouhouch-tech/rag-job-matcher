from PyQt5.QtCore import QThread, pyqtSignal  # type: ignore
from rag_project.logger import get_logger


logger = get_logger(__name__)


class RetrievalWorker(QThread):
    """Background worker to run QueryService.answer without blocking the UI."""

    answer_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, query_service, question: str, doc_types=None):
        super().__init__()
        self.query_service = query_service
        self.question = question
        self.doc_types = doc_types

    def run(self):
        try:
            logger.info("RetrievalWorker starting question len=%d doc_types=%s", len(self.question), self.doc_types)
            result = self.query_service.answer(self.question, doc_types=self.doc_types)
            self.answer_ready.emit(result)
        except Exception as exc:  # noqa: BLE001
            logger.error("RetrievalWorker failed: %s", exc, exc_info=True)
            self.error_occurred.emit(str(exc))
