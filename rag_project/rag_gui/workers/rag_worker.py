import psycopg
import time  # <--- Added for simulation
from PyQt5 import QtCore
from pgvector.psycopg import register_vector
from rag_project.rag_gui.config import (
    GUI_JOBLOADER_DB_TIMEOUT,
    GUI_JOBLOADER_QUERY,
    GUI_JOB_FALLBACK_LABELS,
    GUI_CHAT_SIMULATED_DELAY,
    GUI_CHAT_FAKE_ANSWER,
    GUI_CHAT_FAKE_SOURCES,
)
from rag_project.logger import get_logger


logger = get_logger(__name__)


# ... (Keep JobLoaderWorker exactly as it was) ...
class JobLoaderWorker(QtCore.QThread):
    # ... (No changes here, keep existing code) ...
    finished = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str)

    def __init__(self, connection_settings: dict):
        super().__init__()
        self.conn_settings = connection_settings

    def run(self):
        try:
            logger.info("JobLoaderWorker connecting to DB")
            jobs = []
            with psycopg.connect(
                connect_timeout=GUI_JOBLOADER_DB_TIMEOUT, **self.conn_settings
            ) as conn:
                register_vector(conn)
                with conn.cursor() as cur:
                    cur.execute(GUI_JOBLOADER_QUERY)
                    rows = cur.fetchall()

                    for r in rows:
                        jobs.append(
                            {
                                "id": str(r[0]),
                                "title": r[1] or GUI_JOB_FALLBACK_LABELS["title"],
                                "company": r[2] or GUI_JOB_FALLBACK_LABELS["company"],
                                "location": r[3] or GUI_JOB_FALLBACK_LABELS["location"],
                                "date": r[4].strftime("%Y-%m-%d") if r[4] else "",
                            }
                        )

            self.finished.emit(jobs)
            logger.info("JobLoaderWorker fetched %d jobs", len(jobs))

        except Exception as e:
            logger.error("JobLoaderWorker failed: %s", e, exc_info=True)
            self.error.emit(str(e))


# --- WORKER 2: Handles the Chat (MOCK VERSION) ---
class RAGQueryWorker(QtCore.QThread):
    """Sends the user question + selected IDs to the LLM and returns the answer."""

    answer_ready = QtCore.pyqtSignal(str)
    sources_ready = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str)

    def __init__(self, app, question: str, selected_job_ids: list):
        super().__init__()
        self._app = app
        self._question = question
        self._selected_ids = selected_job_ids

    def run(self):
        try:
            logger.info(
                "RAGQueryWorker starting question len=%d selected_ids=%d",
                len(self._question),
                len(self._selected_ids),
            )
            # 1. Simulate "Thinking" delay
            time.sleep(GUI_CHAT_SIMULATED_DELAY)

            # 2. Simulate Response
            # In the future, this will be: response = self._app.query(...)

            fake_answer = GUI_CHAT_FAKE_ANSWER.format(question=self._question)

            # 3. Simulate Sources
            fake_sources = GUI_CHAT_FAKE_SOURCES

            # 4. Emit Results
            self.answer_ready.emit(fake_answer)
            self.sources_ready.emit(fake_sources)

        except Exception as e:
            logger.error("RAGQueryWorker failed: %s", e, exc_info=True)
            self.error.emit(str(e))
