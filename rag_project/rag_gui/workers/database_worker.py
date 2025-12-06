import shutil
import psycopg
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from pgvector.psycopg import register_vector
from rag_project.rag_gui.config import (
    GUI_DISK_USAGE_PATH,
    GUI_DB_OVERVIEW_TIMEOUT,
    GUI_DB_SIZE_QUERY,
    GUI_DOC_COUNT_QUERY,
    GUI_CHUNK_COUNT_QUERY,
    GUI_DELETE_STATS_QUERIES,
    GUI_DOC_LIST_QUERY_BASE,
    GUI_DELETE_FILTER_OPTIONS,
    GUI_DOC_LIST_FILTER_QUERY,
)
from rag_project.logger import get_logger


logger = get_logger(__name__)


# ==========================================
# CLASS 1: Used by DatabaseView
# ==========================================
class DatabaseOverviewWorker(QThread):
    """Worker to fetch DB size, disk usage, and per-type stats."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, connection_settings: dict):
        super().__init__()
        self.conn_settings = connection_settings

    def run(self):
        try:
            logger.info("DatabaseOverviewWorker gathering disk/db stats")
            results = {}
            # 1. Disk Usage
            total, used, free = shutil.disk_usage(GUI_DISK_USAGE_PATH)
            results["disk_total"] = total
            results["disk_free"] = free

            # 2. DB Operations
            with psycopg.connect(
                connect_timeout=GUI_DB_OVERVIEW_TIMEOUT, **self.conn_settings
            ) as conn:
                register_vector(conn)
                with conn.cursor() as cur:
                    cur.execute(GUI_DB_SIZE_QUERY)
                    results["db_size"] = cur.fetchone()[0]

                    cur.execute(GUI_DOC_COUNT_QUERY)
                    results["doc_counts"] = {row[0]: row[1] for row in cur.fetchall()}

                    cur.execute(GUI_CHUNK_COUNT_QUERY)
                    results["chunk_counts"] = {row[0]: row[1] for row in cur.fetchall()}

            self.finished.emit(results)
            logger.info("DatabaseOverviewWorker completed")
        except Exception as e:
            logger.error("DatabaseOverviewWorker failed: %s", e, exc_info=True)
            self.error.emit(str(e))


# ==========================================
# CLASS 2: Used by DeleteView (Loads Data)
# ==========================================
class DataLoaderWorker(QThread):
    """Worker thread to fetch statistics and document list."""

    finished = pyqtSignal(dict, list)
    error = pyqtSignal(str)

    def __init__(self, connection_settings: dict, filter_type: str):
        super().__init__()
        self.conn_settings = connection_settings
        self.filter_type = filter_type

    def run(self):
        try:
            logger.info("DataLoaderWorker loading docs filter=%s", self.filter_type)
            stats = {}
            docs = []

            with psycopg.connect(
                connect_timeout=GUI_DB_OVERVIEW_TIMEOUT, **self.conn_settings
            ) as conn:
                register_vector(conn)
                with conn.cursor() as cur:
                    # Stats
                    cur.execute(GUI_DELETE_STATS_QUERIES["docs"])
                    stats["docs"] = str(cur.fetchone()[0])
                    cur.execute(GUI_DELETE_STATS_QUERIES["chunks"])
                    stats["chunks"] = str(cur.fetchone()[0])
                    cur.execute(GUI_DELETE_STATS_QUERIES["embeds"])
                    stats["embeds"] = str(cur.fetchone()[0])

                    # Documents List
                    query_base = GUI_DOC_LIST_QUERY_BASE

                    if self.filter_type in GUI_DELETE_FILTER_OPTIONS:
                        query = query_base + " ORDER BY d.created_at DESC"
                        cur.execute(query)
                    else:
                        query = query_base + f" {GUI_DOC_LIST_FILTER_QUERY}"
                        cur.execute(query, (self.filter_type,))

                    rows = cur.fetchall()
                    docs = [
                        {
                            "id": str(r[0]),
                            "doc_type": r[1],
                            "created_at": (
                                r[2].strftime("%Y-%m-%d %H:%M:%S") if r[2] else ""
                            ),
                            "label": r[3] or "",
                        }
                        for r in rows
                    ]

            self.finished.emit(stats, docs)
            logger.info("DataLoaderWorker loaded %d docs", len(docs))
        except Exception as e:
            logger.error("DataLoaderWorker failed: %s", e, exc_info=True)
            self.error.emit(str(e))


# ==========================================
# CLASS 3: Used by DeleteView (Deletes Data)
# ==========================================
class DeleteWorker(QThread):
    """Worker thread to delete documents."""

    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, repo, doc_ids: list):
        super().__init__()
        self.repo = repo
        self.doc_ids = doc_ids

    def run(self):
        try:
            logger.info("DeleteWorker deleting %d documents", len(self.doc_ids))
            count = 0
            for doc_id in self.doc_ids:
                self.repo.delete_document(doc_id)
                count += 1
            self.finished.emit(count)
            logger.info("DeleteWorker deleted %d documents", count)
        except Exception as e:
            logger.error("DeleteWorker failed: %s", e, exc_info=True)
            self.error.emit(str(e))
