import os
import re
from pathlib import Path
from PyQt5 import QtCore  # type: ignore
from rag_project.rag_core.app_facade import RAGApp
from rag_project.rag_gui.config import (
    GUI_INGEST_STAGE_WEIGHTS,
    GUI_STAGE_PARSE_MATCH,
    GUI_STAGE_CHUNK_MATCH,
    GUI_CHUNK_COUNT_REGEX,
    GUI_STAGE_EMBED_DONE_MATCH,
    GUI_STAGE_WRITE_MATCH,
    GUI_INGEST_DONE_TEXT,
    GUI_ABORT_LOG_TEXT,
)
from rag_project.logger import get_logger


logger = get_logger(__name__)

class UserAbortException(Exception):
    """Custom exception to break out of blocking operations immediately."""
    pass

class IngestionWorker(QtCore.QThread):
    progress_updated = QtCore.pyqtSignal(int, int)
    progress_detail = QtCore.pyqtSignal(int)
    log_message = QtCore.pyqtSignal(str)
    detail_status = QtCore.pyqtSignal(str)
    ingestion_complete = QtCore.pyqtSignal(str, int)
    error_occurred = QtCore.pyqtSignal(str)
    process_aborted = QtCore.pyqtSignal()

    def __init__(self, app: RAGApp, file_paths: list[str], doc_type: str):
        super().__init__()
        self._app = app
        self._file_paths = file_paths
        self._doc_type = doc_type
        self._chunk_count = 0
        self._is_running = True

    def stop(self):
        """Signal the thread to stop."""
        self._is_running = False
        self.requestInterruption()

    def run(self):
        try:
            total_files = len(self._file_paths)
            if total_files == 0:
                raise ValueError("No files selected")
            logger.info("IngestionWorker starting %d files doc_type=%s", total_files, self._doc_type)
            
            stage_weights = GUI_INGEST_STAGE_WEIGHTS
            
            self.log_message.emit("Loading application components...")
            self.detail_status.emit("Initializing")
            self.progress_updated.emit(0, 100)
            
            for idx, file_path in enumerate(self._file_paths, start=1):
                # 1. Check for stop BEFORE file start
                if not self._is_running:
                    raise UserAbortException()

                self._chunk_count = 0
                self.detail_status.emit(f"Processing {os.path.basename(file_path)}...")
                logger.debug("IngestionWorker processing file=%s", file_path)
                
                file_base_progress = int((idx - 1) / total_files * 100)
                self.progress_updated.emit(file_base_progress, 100)

                stage_done = {"parse": False, "chunk": False, "embed": False, "write": False}

                def progress_cb(stage: str, info: dict):
                    # 2. Check for stop INSIDE the heavy lifting
                    if not self._is_running:
                        raise UserAbortException()

                    msg = info.get("message")
                    if msg:
                        self.log_message.emit(f"[{os.path.basename(file_path)}] {msg}")
                        
                        # --- String Matching Logic (Same as before) ---
                        if GUI_STAGE_PARSE_MATCH in msg:
                            stage_done["parse"] = True
                            self.detail_status.emit("Chunking")
                        elif GUI_STAGE_CHUNK_MATCH in msg:
                            stage_done["chunk"] = True
                            m = re.search(GUI_CHUNK_COUNT_REGEX, msg)
                            if m: self._chunk_count = int(m.group(1))
                            self.detail_status.emit("Embedding")
                        elif GUI_STAGE_EMBED_DONE_MATCH in msg:
                            stage_done["embed"] = True
                            self.detail_status.emit("Writing")
                        elif "Embedding" in msg:
                            self.detail_status.emit("Embedding")
                        elif GUI_STAGE_WRITE_MATCH in msg:
                            stage_done["write"] = True
                        elif "Ingestion completed" in msg:
                            for k in stage_done: stage_done[k] = True

                    # --- Math Logic ---
                    completed_weight = sum(w for s, w in stage_weights.items() if stage_done[s])
                    detail_pct_raw = info.get("detail_pct", 0)
                    current_stage_key = next((k for k, v in stage_done.items() if not v), None)
                    if current_stage_key:
                        completed_weight += stage_weights[current_stage_key] * (detail_pct_raw / 100.0)

                    span_per_file = 100 / total_files
                    overall = file_base_progress + (span_per_file * completed_weight)
                    
                    self.progress_updated.emit(int(min(100, overall)), 100)
                    self.progress_detail.emit(int(detail_pct_raw))

                # 3. Run Ingestion (Protected Block)
                try:
                    metadata = {"doc_type": self._doc_type}
                    doc_id = self._app.ingestion.ingest_file(
                        file_path, 
                        metadata=metadata, 
                        progress_cb=progress_cb
                    )
                    
                    self.log_message.emit(f"Completed {os.path.basename(file_path)} → ID: {doc_id}")
                    self.ingestion_complete.emit(str(doc_id), self._chunk_count)
                    logger.info("IngestionWorker completed file=%s doc_id=%s chunks=%d", file_path, doc_id, self._chunk_count)
                    
                except UserAbortException:
                    # Catch the specific stop signal from the callback
                    raise UserAbortException() 
                except Exception as e:
                    # If stopped, ignore other errors (like DB connection closed)
                    if not self._is_running:
                        raise UserAbortException()
                    self.log_message.emit(f"Error processing file: {str(e)}")
                    # We continue to next file unless it's a critical crash, 
                    # but usually we might want to stop here too. 
                    # For now, let's log and continue.

            self.detail_status.emit(GUI_INGEST_DONE_TEXT)
            self.progress_updated.emit(100, 100)

        except UserAbortException:
            self.log_message.emit(GUI_ABORT_LOG_TEXT)
            self.process_aborted.emit()
            logger.warning("IngestionWorker aborted by user")
            
        except Exception as exc:
            logger.error("IngestionWorker failed: %s", exc, exc_info=True)
            self.error_occurred.emit(str(exc))
