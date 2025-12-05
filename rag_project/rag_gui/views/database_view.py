from typing import Dict
from PyQt5 import QtCore, QtGui, QtWidgets

from rag_project.rag_gui.config import (
    DOC_TYPE_OPTIONS,
    FONT_FAMILY,
    FONT_SIZE_LABEL,
    FONT_SIZE_TITLE,
    INPUT_HEIGHT,
    BUTTON_MIN_WIDTH,
    PADDING_LARGE,
    PADDING_SMALL,
    GUI_DBVIEW_TITLE,
    GUI_REFRESH_LABEL,
    GUI_DB_STATUS_CHECKING,
    GUI_DB_ERROR_PREFIX,
)
from rag_project.rag_gui.widgets import StatsCard, StatusIndicator
from rag_project.rag_gui.workers.database_worker import DatabaseOverviewWorker
from rag_project.logger import get_logger


logger = get_logger(__name__)


class DatabaseView(QtWidgets.QWidget):
    """Show database connectivity and basic statistics."""

    def __init__(self, conn_settings: Dict[str, str], parent=None):
        super().__init__(parent)
        self._conn_settings = conn_settings
        self.doc_type_stats: Dict[str, QtWidgets.QLabel] = {}
        self._worker = None
        
        self._build_ui()
        
        # Initial load (Silent mode: don't popup if it fails immediately)
        self.refresh_statistics(silent=True)

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(PADDING_LARGE, PADDING_LARGE, PADDING_LARGE, PADDING_LARGE)
        layout.setSpacing(PADDING_SMALL)

        # --- Header ---
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel(GUI_DBVIEW_TITLE)
        title.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_TITLE, QtGui.QFont.DemiBold))
        
        self.db_indicator = StatusIndicator()
        self.db_status_label = QtWidgets.QLabel("Ready")
        self.db_status_label.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_LABEL))
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.db_indicator)
        header.addWidget(self.db_status_label)
        layout.addLayout(header)

        # --- Refresh Button ---
        self.refresh_btn = QtWidgets.QPushButton(GUI_REFRESH_LABEL)
        self.refresh_btn.setFixedHeight(INPUT_HEIGHT)
        self.refresh_btn.setFixedWidth(BUTTON_MIN_WIDTH)
        # Manual click is NOT silent
        self.refresh_btn.clicked.connect(lambda: self.refresh_statistics(silent=False))
        layout.addWidget(self.refresh_btn, alignment=QtCore.Qt.AlignLeft)

        # --- Stats Cards ---
        cards_layout = QtWidgets.QGridLayout()
        self.db_size_card = StatsCard("DB Used", "-")
        self.fs_card = StatsCard("Disk Free/Total", "-")
        cards_layout.addWidget(self.db_size_card, 0, 0)
        cards_layout.addWidget(self.fs_card, 0, 1)
        layout.addLayout(cards_layout)

        # --- Detail Group ---
        self.doc_stats_group = QtWidgets.QGroupBox("Document Statistics")
        doc_layout = QtWidgets.QFormLayout()
        
        for dt in DOC_TYPE_OPTIONS:
            label = QtWidgets.QLabel(dt.replace("_", " ").title())
            value = QtWidgets.QLabel("Waiting for data...")
            self.doc_type_stats[dt] = value
            doc_layout.addRow(label, value)
            
        self.doc_stats_group.setLayout(doc_layout)
        layout.addWidget(self.doc_stats_group)
        layout.addStretch()

    def refresh_statistics(self, silent=False):
        """Start background worker."""
        logger.info("DatabaseView refresh requested silent=%s", silent)
        self.db_status_label.setText(GUI_DB_STATUS_CHECKING)
        self.db_indicator.set_status(True) # Yellow/Active
        self.refresh_btn.setEnabled(False)
        
        # Pass the silent flag to the worker or handle it in the callback
        self._silent_error = silent 

        self._worker = DatabaseOverviewWorker(self._conn_settings)
        self._worker.finished.connect(self.on_stats_loaded)
        self._worker.error.connect(self.on_worker_error)
        self._worker.start()

    def on_stats_loaded(self, results: dict):
        """Update UI with results from worker."""
        logger.info("DatabaseView stats loaded")
        self.refresh_btn.setEnabled(True)
        self.db_indicator.set_status(True) # Green/Success
        self.db_status_label.setText("DB Connected")

        # 1. Update Cards
        self.db_size_card.update_value(self._pretty_size(results['db_size']))
        
        free_fmt = self._pretty_size(results['disk_free'])
        total_fmt = self._pretty_size(results['disk_total'])
        self.fs_card.update_value(f"{free_fmt} free / {total_fmt}")

        # 2. Update Document Type Details
        doc_counts = results.get('doc_counts', {})
        chunk_counts = results.get('chunk_counts', {})
        
        for dt, label_widget in self.doc_type_stats.items():
            d_count = doc_counts.get(dt, 0)
            c_count = chunk_counts.get(dt, 0)
            label_widget.setText(f"{d_count} docs / {c_count} chunks")

    def on_worker_error(self, error_msg: str):
        logger.error("DatabaseView worker error: %s", error_msg)
        self.refresh_btn.setEnabled(True)
        self.db_indicator.set_status(False) # Red/Error
        self.db_status_label.setText("Connection Error")
        
        # 1. Reset Top Cards to N/A
        self.db_size_card.update_value("N/A")
        self.fs_card.update_value("N/A")

        # 2. Reset Document Type details to N/A
        for label_widget in self.doc_type_stats.values():
            label_widget.setText("N/A")

        # 3. Show error message only if NOT silent
        if not getattr(self, '_silent_error', False):
            QtWidgets.QMessageBox.warning(self, "Database Error", f"{GUI_DB_ERROR_PREFIX}{error_msg}")

    @staticmethod
    def _pretty_size(num_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if num_bytes < 1024.0:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024.0
        return f"{num_bytes:.1f} PB"
