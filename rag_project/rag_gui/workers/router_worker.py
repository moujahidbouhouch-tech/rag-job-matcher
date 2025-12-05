from PyQt5.QtCore import QThread, pyqtSignal  # type: ignore
from rag_project.logger import get_logger


logger = get_logger(__name__)


class RouterWorker(QThread):
    """Background worker to classify user intent via RouterService."""

    decision_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, router_service, user_text: str, context: dict | None = None):
        super().__init__()
        self.router_service = router_service
        self.user_text = user_text
        self.context = context or {}

    def run(self):
        try:
            logger.info("RouterWorker starting for text len=%d", len(self.user_text))
            decision = self.router_service.route(self.user_text, self.context)
            self.decision_ready.emit(decision)
        except Exception as exc:  # noqa: BLE001
            logger.error("RouterWorker failed: %s", exc, exc_info=True)
            self.error_occurred.emit(str(exc))
