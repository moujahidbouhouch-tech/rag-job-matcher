from typing import Dict, List
from PyQt5 import QtCore, QtGui, QtWidgets

from rag_project.rag_gui.config import (
    BUTTON_MIN_HEIGHT,
    BUTTON_MIN_WIDTH,
    DELETE_TABLE_HEADERS,
    DOC_TYPE_OPTIONS,
    FONT_FAMILY,
    FONT_SIZE_LABEL,
    FONT_SIZE_TITLE,
    INPUT_HEIGHT,
    PADDING_LARGE,
    PADDING_SMALL,
    TABLE_ROW_HEIGHT,
    TABLE_COLUMN_ID_WIDTH,
    GUI_DELETE_TITLE,
    GUI_REFRESH_LABEL,
    GUI_DELETE_LOAD_LABEL,
    GUI_DELETE_BUTTON_LABEL,
    GUI_DELETE_FILTER_OPTIONS,
    GUI_DELETE_SELECTION_WARNING,
    GUI_DELETE_CONFIRM_TEXT,
    GUI_DELETE_FAIL_TITLE,
    GUI_DELETE_TABLE_HEADERS,
)
from rag_project.rag_gui.widgets import StatsCard, StatusIndicator
from rag_project.rag_gui.workers.database_worker import DataLoaderWorker, DeleteWorker
from rag_project.logger import get_logger


logger = get_logger(__name__)


class DeleteView(QtWidgets.QWidget):
    """List and delete documents by type with async loading."""

    def __init__(self, repo, conn_settings: Dict[str, str], parent=None):
        super().__init__(parent)
        self._repo = repo
        self._conn_settings = conn_settings
        self._docs: List[dict] = []

        # Keep references to workers to prevent garbage collection
        self._load_worker = None
        self._delete_worker = None

        self._build_ui()

        # Initial Load (Silent mode: don't popup if it fails immediately)
        self.refresh_statistics(silent=True)

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(
            PADDING_LARGE, PADDING_LARGE, PADDING_LARGE, PADDING_LARGE
        )
        layout.setSpacing(PADDING_SMALL)

        # --- Header ---
        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel(GUI_DELETE_TITLE)
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
        self.refresh_btn.setFixedSize(BUTTON_MIN_WIDTH, INPUT_HEIGHT)
        # Manual click is NOT silent
        self.refresh_btn.clicked.connect(lambda: self.refresh_statistics(silent=False))
        layout.addWidget(self.refresh_btn, alignment=QtCore.Qt.AlignLeft)

        # --- Stats Cards ---
        cards_layout = QtWidgets.QGridLayout()
        self.db_status_card = StatsCard("Documents", "-")
        self.storage_card = StatsCard("Chunks", "-")
        self.used_card = StatsCard("Embeddings", "-")

        cards_layout.addWidget(self.db_status_card, 0, 0)
        cards_layout.addWidget(self.storage_card, 0, 1)
        cards_layout.addWidget(self.used_card, 0, 2)
        layout.addLayout(cards_layout)

        # --- Filters & Action ---
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.setSpacing(PADDING_SMALL)

        self.browse_type_combo = QtWidgets.QComboBox()
        self.browse_type_combo.addItems(GUI_DELETE_FILTER_OPTIONS + DOC_TYPE_OPTIONS)
        # Filter change acts like a manual refresh (show errors if it fails)
        self.browse_type_combo.currentTextChanged.connect(
            lambda: self.refresh_statistics(silent=False)
        )

        self.delete_btn = QtWidgets.QPushButton(GUI_DELETE_BUTTON_LABEL)
        self.delete_btn.setFixedSize(BUTTON_MIN_WIDTH, INPUT_HEIGHT)
        self.delete_btn.clicked.connect(self.confirm_and_delete)

        filter_label = QtWidgets.QLabel("Filter")
        filter_label.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_LABEL))

        filter_layout.addWidget(filter_label, alignment=QtCore.Qt.AlignVCenter)
        filter_layout.addWidget(
            self.browse_type_combo, stretch=1, alignment=QtCore.Qt.AlignVCenter
        )
        filter_layout.addStretch()
        filter_layout.addWidget(self.delete_btn, alignment=QtCore.Qt.AlignVCenter)
        layout.addLayout(filter_layout)

        layout.addSpacing(PADDING_SMALL)

        # --- Table ---
        self.doc_table = QtWidgets.QTableWidget()
        self.doc_table.setColumnCount(len(GUI_DELETE_TABLE_HEADERS))
        self.doc_table.setHorizontalHeaderLabels(GUI_DELETE_TABLE_HEADERS)
        self.doc_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.doc_table.verticalHeader().setDefaultSectionSize(TABLE_ROW_HEIGHT)

        # Header Resizing
        h_header = self.doc_table.horizontalHeader()
        h_header.setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )  # Checkbox
        h_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)  # ID
        h_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)  # Type
        h_header.setSectionResizeMode(
            3, QtWidgets.QHeaderView.ResizeToContents
        )  # Created
        h_header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)  # Label
        self.doc_table.setColumnWidth(1, TABLE_COLUMN_ID_WIDTH)

        self.doc_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.doc_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.doc_table.setAlternatingRowColors(False)  # Clean look

        layout.addWidget(self.doc_table, stretch=1)

    # --- Logic ---

    def set_loading(self, is_loading: bool, message: str = ""):
        """Toggle UI state during async operations."""
        self.refresh_btn.setEnabled(not is_loading)
        self.delete_btn.setEnabled(not is_loading)
        self.browse_type_combo.setEnabled(not is_loading)
        self.doc_table.setEnabled(not is_loading)

        if is_loading:
            self.db_status_label.setText(message)
            self.db_indicator.set_status(True)
        else:
            self.db_status_label.setText("Ready")

    def refresh_statistics(self, silent=False):
        """Start the background worker to load stats and docs."""
        logger.info("DeleteView refresh requested silent=%s", silent)
        filter_val = self.browse_type_combo.currentText()
        self.set_loading(True, "Loading data...")

        # Store silent flag for error handler
        self._silent_error = silent

        # Initialize Worker
        self._load_worker = DataLoaderWorker(self._conn_settings, filter_val)
        self._load_worker.finished.connect(self.on_data_loaded)
        self._load_worker.error.connect(self.on_worker_error)
        self._load_worker.start()

    def on_data_loaded(self, stats: dict, docs: list):
        """Callback when data is fetched successfully."""
        logger.info("DeleteView data loaded docs=%d", len(docs))
        self.set_loading(False)
        self.db_indicator.set_status(True)
        self.db_status_label.setText("Connected")

        # Update Cards
        self.db_status_card.update_value(stats.get("docs", "0"))
        self.storage_card.update_value(stats.get("chunks", "0"))
        self.used_card.update_value(stats.get("embeds", "0"))

        # Update Table
        self._docs = docs
        self._populate_table(docs)

    def on_worker_error(self, error_msg: str):
        """Callback for any worker failure."""
        logger.error("DeleteView worker error: %s", error_msg)
        self.set_loading(False)
        self.db_indicator.set_status(False)
        self.db_status_label.setText("Connection Error")

        # 1. Reset Stats to N/A
        self.db_status_card.update_value("N/A")
        self.storage_card.update_value("N/A")
        self.used_card.update_value("N/A")

        # 2. Only show popup if user manually requested action
        if not getattr(self, "_silent_error", False):
            QtWidgets.QMessageBox.critical(
                self, "Database Error", f"An error occurred:\n{error_msg}"
            )

    def _populate_table(self, docs: List[dict]):
        """Fill table, handling the empty state correctly."""
        self.doc_table.setRowCount(len(docs))

        for row, doc in enumerate(docs):
            # Checkbox
            checkbox_item = QtWidgets.QTableWidgetItem()
            checkbox_item.setFlags(
                QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
            )
            checkbox_item.setCheckState(QtCore.Qt.Unchecked)
            self.doc_table.setItem(row, 0, checkbox_item)

            # Data items (Read only)
            id_item = QtWidgets.QTableWidgetItem(doc["id"])
            id_item.setFlags(id_item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.doc_table.setItem(row, 1, id_item)

            type_item = QtWidgets.QTableWidgetItem(doc["doc_type"])
            type_item.setFlags(type_item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.doc_table.setItem(row, 2, type_item)

            date_item = QtWidgets.QTableWidgetItem(str(doc["created_at"]))
            date_item.setFlags(date_item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.doc_table.setItem(row, 3, date_item)

            label_item = QtWidgets.QTableWidgetItem(doc["label"])
            label_item.setFlags(label_item.flags() ^ QtCore.Qt.ItemIsEditable)
            self.doc_table.setItem(row, 4, label_item)

    def confirm_and_delete(self):
        """Validate selection and show confirmation dialog."""
        doc_ids = []
        for row in range(self.doc_table.rowCount()):
            item = self.doc_table.item(row, 0)
            if item and item.checkState() == QtCore.Qt.Checked:
                doc_id = self.doc_table.item(row, 1).text()
                doc_ids.append(doc_id)

        if not doc_ids:
            QtWidgets.QMessageBox.information(
                self,
                GUI_DELETE_SELECTION_WARNING["title"],
                GUI_DELETE_SELECTION_WARNING["message"],
            )
            return
        logger.info("DeleteView delete requested count=%d", len(doc_ids))

        reply = QtWidgets.QMessageBox.question(
            self,
            GUI_DELETE_CONFIRM_TEXT["title"],
            GUI_DELETE_CONFIRM_TEXT["template"].format(count=len(doc_ids)),
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.start_delete_process(doc_ids)

    def start_delete_process(self, doc_ids: List[str]):
        """Start background delete worker."""
        logger.info("DeleteView starting delete worker count=%d", len(doc_ids))
        self.set_loading(True, f"Deleting {len(doc_ids)} items...")

        # Deletion is never silent, we always want feedback
        self._silent_error = False

        self._delete_worker = DeleteWorker(self._repo, doc_ids)
        self._delete_worker.finished.connect(self.on_delete_finished)
        self._delete_worker.error.connect(self.on_worker_error)
        self._delete_worker.start()

    def on_delete_finished(self, count: int):
        logger.info("DeleteView delete finished count=%d", count)
        self.set_loading(False)
        QtWidgets.QMessageBox.information(
            self, "Success", f"Successfully deleted {count} documents."
        )
        self.refresh_statistics(silent=False)
