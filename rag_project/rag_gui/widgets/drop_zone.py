from PyQt5 import QtCore, QtGui, QtWidgets  # type: ignore

from rag_project.rag_gui.config import (
    BORDER_RADIUS,
    FONT_FAMILY,
    FONT_SIZE_BODY,
    FONT_SIZE_LABEL,
    PADDING_SMALL,
    COLOR_DARK_WIDGET,
    COLOR_DARK_BORDER,
    COLOR_DARK_MUTED,
    COLOR_DARK_TEXT,
    COLOR_DARK_SUCCESS,
    GUI_DROPZONE_TEXT,
    GUI_DROPZONE_FILE_FILTER,
)
from rag_project.logger import get_logger


logger = get_logger(__name__)


class DropZone(QtWidgets.QFrame):
    """Minimalistic drag/drop zone."""

    file_dropped = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self):
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setStyleSheet(
            f"""
            DropZone {{
                background-color: {COLOR_DARK_WIDGET};
                border: 2px dashed {COLOR_DARK_BORDER};
                border-radius: {BORDER_RADIUS}px;
                min-height: 80px;
            }}
            DropZone:hover {{
                border-color: {COLOR_DARK_MUTED};
                background-color: {COLOR_DARK_BORDER};
            }}
            """
        )
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(PADDING_SMALL)

        icon_label = QtWidgets.QLabel("↑")
        icon_label.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_BODY + 9, QtGui.QFont.Light))
        icon_label.setAlignment(QtCore.Qt.AlignCenter)
        icon_label.setStyleSheet(f"color: {COLOR_DARK_MUTED}; border: none;")

        text_label = QtWidgets.QLabel(GUI_DROPZONE_TEXT)
        text_label.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_BODY - 2))
        text_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setStyleSheet(f"color: {COLOR_DARK_TEXT}; border: none;")

        formats_label = QtWidgets.QLabel("PDF · DOCX · TXT · MD")
        formats_label.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_LABEL))
        formats_label.setAlignment(QtCore.Qt.AlignCenter)
        formats_label.setStyleSheet(f"color: {COLOR_DARK_MUTED}; border: none;")

        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addWidget(formats_label)
        self.setLayout(layout)

    def dragEnterEvent(self, event):  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(
                f"""
                DropZone {{
                    background-color: {COLOR_DARK_BORDER};
                    border: 2px dashed {COLOR_DARK_SUCCESS};
                    border-radius: {BORDER_RADIUS}px;
                }}
                """
            )

    def dragLeaveEvent(self, event):  # noqa: N802
        self._reset_style()

    def dropEvent(self, event):  # noqa: N802
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            logger.info("DropZone file dropped path=%s", files[0])
            self.file_dropped.emit(files[0])
        self._reset_style()

    def mousePressEvent(self, event):  # noqa: N802
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Document",
            "",
            GUI_DROPZONE_FILE_FILTER,
        )
        if file_path:
            logger.info("DropZone file selected path=%s", file_path)
            self.file_dropped.emit(file_path)

    def _reset_style(self):
        self.setStyleSheet(
            f"""
            DropZone {{
                background-color: {COLOR_DARK_WIDGET};
                border: 2px dashed {COLOR_DARK_BORDER};
                border-radius: {BORDER_RADIUS}px;
            }}
            """
        )
