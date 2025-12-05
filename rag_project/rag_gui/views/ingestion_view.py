import os
from typing import Callable, Optional
from PyQt5 import QtCore, QtGui, QtWidgets

from rag_project.rag_gui.config import (
    BUTTON_MIN_HEIGHT,
    BUTTON_MIN_WIDTH,
    DOC_TYPE_OPTIONS,
    FONT_FAMILY,
    FONT_SIZE_BODY,
    FONT_SIZE_LABEL,
    FONT_SIZE_LOG_HEADER,
    FONT_SIZE_TITLE,
    INPUT_HEIGHT,
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
    COLOR_LIGHT_DANGER,
    GUI_INGEST_TITLE,
    GUI_DB_STATUS_INITIAL,
    GUI_GROUP_SELECT_DOCS,
    GUI_NO_FILES_PLACEHOLDER,
    GUI_FILELIST_MIN_HEIGHT,
    GUI_FILE_BUTTON_LABELS,
    GUI_DOC_TYPE_PLACEHOLDER,
    GUI_DOC_TYPE_EXTRA_WIDTH,
    GUI_INGEST_BUTTON_LABELS,
    GUI_BUTTON_HEIGHT_OFFSET,
    GUI_STOP_BUTTON_STYLE,
    GUI_PROGRESS_LABEL,
    GUI_PROGRESS_HEIGHT_OFFSET,
    GUI_DETAIL_STATUS_DEFAULT,
    GUI_DETAIL_STATUS_COLOR_DEFAULT,
    GUI_DETAIL_PROGRESS_HEIGHT_OFFSET,
    GUI_LOG_HEADER_TEXT,
    GUI_CLEAR_BUTTON_SIZE,
    GUI_FILE_DIALOG_FILTERS,
    GUI_DOC_TYPE_WARNING_TEXT,
    GUI_START_LOG_TEMPLATE,
    GUI_STOP_STATUS_TEXT,
    GUI_ABORT_MESSAGE,
    GUI_LOG_CLEAR_BEHAVIOR,
)
from rag_project.rag_gui.widgets import StatusIndicator
from rag_project.rag_gui.workers.ingestion_worker import IngestionWorker
from rag_project.logger import get_logger


logger = get_logger(__name__)


class IngestionView(QtWidgets.QWidget):
    """Ingestion view: drop/browse, doc type picker, progress, logs."""

    def __init__(self, app, conn_checker: Callable[[], bool], parent=None):
        super().__init__(parent)
        self._app = app
        self._conn_checker = conn_checker
        self._current_files: list[str] = []
        self._worker: Optional[IngestionWorker] = None
        
        self._build_ui()
        self.refresh_db_status()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(PADDING_LARGE, PADDING_LARGE, PADDING_LARGE, PADDING_LARGE)
        layout.setSpacing(PADDING_MEDIUM)

        # --- 1. Header ---
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel(GUI_INGEST_TITLE)
        title.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_TITLE, QtGui.QFont.DemiBold))
        self.db_indicator = StatusIndicator()
        self.db_status_label = QtWidgets.QLabel(GUI_DB_STATUS_INITIAL)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.db_indicator)
        header.addWidget(self.db_status_label)
        layout.addLayout(header)

        # --- 2. File Selection Area (Grouped) ---
        file_group = QtWidgets.QGroupBox(GUI_GROUP_SELECT_DOCS)
        file_layout = QtWidgets.QHBoxLayout(file_group)
        file_layout.setContentsMargins(PADDING_MEDIUM, PADDING_MEDIUM, PADDING_MEDIUM, PADDING_MEDIUM)
        
        self.selected_display = QtWidgets.QPlainTextEdit()
        self.selected_display.setReadOnly(True)
        self.selected_display.setPlaceholderText(GUI_NO_FILES_PLACEHOLDER)
        self.selected_display.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.selected_display.setMinimumHeight(GUI_FILELIST_MIN_HEIGHT)

        file_layout.addWidget(self.selected_display, stretch=1)

        btn_col = QtWidgets.QVBoxLayout()
        btn_col.setSpacing(PADDING_SMALL)
        self.browse_btn = QtWidgets.QPushButton(GUI_FILE_BUTTON_LABELS["browse"])
        self.browse_btn.clicked.connect(self.browse_files)
        self.remove_btn = QtWidgets.QPushButton(GUI_FILE_BUTTON_LABELS["clear"])
        self.remove_btn.clicked.connect(self.remove_files)
        
        self.browse_btn.setFixedWidth(BUTTON_MIN_WIDTH)
        self.browse_btn.setFixedHeight(INPUT_HEIGHT)
        self.remove_btn.setFixedWidth(BUTTON_MIN_WIDTH)
        self.remove_btn.setFixedHeight(INPUT_HEIGHT)

        btn_col.addWidget(self.browse_btn)
        btn_col.addWidget(self.remove_btn)
        btn_col.addStretch()
        file_layout.addLayout(btn_col)

        layout.addWidget(file_group)

        # --- 3. Configuration & Actions ---
        action_layout = QtWidgets.QHBoxLayout()
        action_layout.setSpacing(PADDING_LARGE)

        type_layout = QtWidgets.QVBoxLayout()
        type_layout.setSpacing(2)
        type_label = QtWidgets.QLabel("2. Document Type")
        type_label.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_LABEL, QtGui.QFont.DemiBold))
        
        self.doc_type_combo = QtWidgets.QComboBox()
        self.doc_type_combo.addItem(GUI_DOC_TYPE_PLACEHOLDER, None)
        self.doc_type_combo.addItems(DOC_TYPE_OPTIONS)
        self.doc_type_combo.setFixedHeight(INPUT_HEIGHT)
        self.doc_type_combo.setMinimumWidth(BUTTON_MIN_WIDTH + GUI_DOC_TYPE_EXTRA_WIDTH)
        self.doc_type_combo.currentIndexChanged.connect(self.validate_state)

        type_layout.addWidget(type_label)
        type_layout.addWidget(self.doc_type_combo)
        action_layout.addLayout(type_layout)

        action_layout.addStretch()

        ctrl_layout = QtWidgets.QVBoxLayout()
        ctrl_layout.setSpacing(PADDING_SMALL)
        
        self.ingest_btn = QtWidgets.QPushButton(GUI_INGEST_BUTTON_LABELS["start"])
        self.ingest_btn.setFixedHeight(INPUT_HEIGHT + GUI_BUTTON_HEIGHT_OFFSET)
        self.ingest_btn.setFixedWidth(BUTTON_MIN_WIDTH)
        self.ingest_btn.clicked.connect(self.start_ingestion)
        self.ingest_btn.setEnabled(False) 
        
        self.stop_btn = QtWidgets.QPushButton(GUI_INGEST_BUTTON_LABELS["stop"])
        self.stop_btn.setFixedHeight(INPUT_HEIGHT + GUI_BUTTON_HEIGHT_OFFSET)
        self.stop_btn.setFixedWidth(BUTTON_MIN_WIDTH)
        # Apply explicit Red style for Danger feeling
        self.stop_btn.setStyleSheet(GUI_STOP_BUTTON_STYLE.format(color=COLOR_LIGHT_DANGER))
        self.stop_btn.clicked.connect(self.stop_ingestion)
        self.stop_btn.setVisible(False)

        ctrl_layout.addWidget(self.ingest_btn)
        ctrl_layout.addWidget(self.stop_btn)
        action_layout.addLayout(ctrl_layout)

        layout.addLayout(action_layout)

        # --- 4. Progress ---
        progress_col = QtWidgets.QVBoxLayout()
        progress_col.setSpacing(2)
        
        self.progress_label = QtWidgets.QLabel(GUI_PROGRESS_LABEL)
        self.progress_label.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_LABEL))
        
        self.overall_progress = QtWidgets.QProgressBar()
        self.overall_progress.setFixedHeight(INPUT_HEIGHT - GUI_PROGRESS_HEIGHT_OFFSET)
        
        self.detail_label = QtWidgets.QLabel(GUI_DETAIL_STATUS_DEFAULT)
        self.detail_label.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_LABEL))
        # Initial gray state
        self.detail_label.setStyleSheet(GUI_DETAIL_STATUS_COLOR_DEFAULT)
        
        self.detail_progress = QtWidgets.QProgressBar()
        self.detail_progress.setFixedHeight(INPUT_HEIGHT - GUI_DETAIL_PROGRESS_HEIGHT_OFFSET)
        
        progress_col.addWidget(self.progress_label)
        progress_col.addWidget(self.overall_progress)
        progress_col.addWidget(self.detail_label)
        progress_col.addWidget(self.detail_progress)
        layout.addLayout(progress_col)

        # --- 5. Logs ---
        log_section = QtWidgets.QVBoxLayout()
        log_header_layout = QtWidgets.QHBoxLayout()
        log_header = QtWidgets.QLabel(GUI_LOG_HEADER_TEXT)
        log_header.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_LOG_HEADER, QtGui.QFont.DemiBold))
        
        clear_logs_btn = QtWidgets.QPushButton("Clear")
        clear_logs_btn.setFixedSize(*GUI_CLEAR_BUTTON_SIZE)
        clear_logs_btn.clicked.connect(self.clear_logs)
        
        log_header_layout.addWidget(log_header)
        log_header_layout.addStretch()
        log_header_layout.addWidget(clear_logs_btn)
        
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_BODY))
        
        log_section.addLayout(log_header_layout)
        log_section.addWidget(self.log_text, stretch=1)
        layout.addLayout(log_section)

    def refresh_db_status(self):
        ok = self._conn_checker()
        self.db_indicator.set_status(ok)
        self.db_status_label.setText("DB connected" if ok else "DB unavailable")

    def validate_state(self):
        has_files = len(self._current_files) > 0
        has_type = self.doc_type_combo.currentIndex() > 0 
        self.ingest_btn.setEnabled(has_files and has_type)

    def browse_files(self):
        logger.info("IngestionView browse_files invoked")
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Select Documents", "", 
            GUI_FILE_DIALOG_FILTERS
        )
        if paths:
            self._current_files = paths
            self.selected_display.setPlainText("\n".join(paths))
            self.log_text.append(f"Selected {len(paths)} file(s)")
            self.validate_state()
            logger.info("IngestionView selected %d files", len(paths))

    def remove_files(self):
        logger.info("IngestionView remove_files invoked")
        self._current_files = []
        self.selected_display.clear()
        self.validate_state()

    def start_ingestion(self):
        logger.info("IngestionView start_ingestion clicked files=%d", len(self._current_files))
        if self.doc_type_combo.currentIndex() <= 0:
            QtWidgets.QMessageBox.warning(self, GUI_DOC_TYPE_WARNING_TEXT["title"], GUI_DOC_TYPE_WARNING_TEXT["message"])
            return

        doc_type = self.doc_type_combo.currentText()
        
        self.ingest_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.browse_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)
        self.doc_type_combo.setEnabled(False)
        self.overall_progress.setValue(0)
        self.detail_progress.setValue(0)
        
        # Reset color to default (remove gray/red)
        self.detail_label.setStyleSheet("") 
        
        self.add_log(GUI_START_LOG_TEMPLATE.format(doc_type=doc_type))

        self._worker = IngestionWorker(self._app, self._current_files, doc_type)
        self._worker.progress_updated.connect(self.update_progress)
        self._worker.progress_detail.connect(self.update_detail_progress)
        self._worker.detail_status.connect(self.update_detail_status)
        self._worker.log_message.connect(self.add_log)
        self._worker.ingestion_complete.connect(self.on_ingestion_complete)
        self._worker.error_occurred.connect(self.on_ingestion_error)
        self._worker.process_aborted.connect(self.on_process_aborted)
        self._worker.finished.connect(self.on_worker_finished)
        self._worker.start()

    def stop_ingestion(self):
        if self._worker:
            logger.warning("IngestionView stop_ingestion requested")
            self.detail_label.setText(GUI_STOP_STATUS_TEXT["stopping"])
            # Immediate Visual Feedback: Red Text
            self.detail_label.setStyleSheet(f"color: {COLOR_LIGHT_DANGER}; font-weight: bold;")
            self.stop_btn.setText(GUI_STOP_STATUS_TEXT["stopping"])
            self.stop_btn.setEnabled(False)
            self._worker.stop()

    def reset_ui_state(self):
        """Reset buttons and styles after process ends."""
        self.ingest_btn.setVisible(True)
        self.ingest_btn.setEnabled(True)
        self.stop_btn.setVisible(False)
        self.stop_btn.setEnabled(True)
        self.stop_btn.setText(GUI_INGEST_BUTTON_LABELS["stop"]) # Reset text
        
        self.browse_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)
        self.doc_type_combo.setEnabled(True)
        
        # Reset status label style to default (removes red/gray)
        self.detail_label.setStyleSheet("")

    def update_progress(self, current: int, total: int):
        self.overall_progress.setValue(current)

    def update_detail_progress(self, pct: int):
        self.detail_progress.setValue(pct)

    def update_detail_status(self, status: str):
        self.detail_label.setText(status)

    def add_log(self, message: str, error: bool = False):
        if error:
            self.log_text.append(f"<span style='color:{COLOR_LIGHT_DANGER}'>{message}</span>")
        else:
            self.log_text.append(message)
        
        cursor = self.log_text.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.log_text.setTextCursor(cursor)

    def on_ingestion_complete(self, doc_id: str, chunk_count: int):
        pass 

    def on_ingestion_error(self, error_msg: str):
        self.add_log(f"Error: {error_msg}", error=True)

    def on_process_aborted(self):
        self.add_log(GUI_ABORT_MESSAGE, error=True)
        self.detail_label.setText(GUI_STOP_STATUS_TEXT["stopped"])
        # Ensure red color persists until reset
        self.detail_label.setStyleSheet(f"color: {COLOR_LIGHT_DANGER}; font-weight: bold;")

    def on_worker_finished(self):
        self.reset_ui_state()

    def clear_logs(self):
        self.log_text.clear()
