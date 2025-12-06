from PyQt5 import QtCore, QtGui, QtWidgets  # type: ignore

from rag_project.rag_gui.config import GUI_STATUS_INDICATOR_SIZE, GUI_STATUS_COLORS


class StatusIndicator(QtWidgets.QWidget):
    """Minimal circular status indicator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status = False
        size = GUI_STATUS_INDICATOR_SIZE or 12
        self.setFixedSize(size, size)

    def set_status(self, connected: bool):
        self._status = connected
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = (
            QtGui.QColor(GUI_STATUS_COLORS["ok"])
            if self._status
            else QtGui.QColor(GUI_STATUS_COLORS["error"])
        )
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtCore.Qt.NoPen)
        size = self.width()
        painter.drawEllipse(0, 0, size, size)
