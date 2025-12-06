from PyQt5 import QtGui, QtWidgets  # type: ignore

from rag_project.rag_gui.config import (
    BORDER_RADIUS,
    FONT_FAMILY,
    FONT_SIZE_BODY,
    FONT_SIZE_LABEL,
    PADDING_LARGE,
    PADDING_SMALL,
    STATS_CARD_MIN_HEIGHT,
    GUI_STATS_CARD_HEIGHT,
)


class StatsCard(QtWidgets.QFrame):
    """Simple card to display a numeric stat."""

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        self._title = title
        self._value_text = value
        self._setup_ui()

    def _setup_ui(self):
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setStyleSheet(
            f"StatsCard {{ border: 1px solid transparent; border-radius: {BORDER_RADIUS}px; }}"
        )
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(
            PADDING_LARGE, PADDING_LARGE, PADDING_LARGE, PADDING_LARGE
        )
        layout.setSpacing(PADDING_SMALL)

        title_label = QtWidgets.QLabel(self._title)
        title_label.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_LABEL))
        title_label.setStyleSheet(
            "border: none; text-transform: uppercase; letter-spacing: 0.5px;"
        )

        self.value_label = QtWidgets.QLabel(self._value_text)
        self.value_label.setFont(
            QtGui.QFont(FONT_FAMILY, FONT_SIZE_BODY + 7, QtGui.QFont.DemiBold)
        )
        self.value_label.setStyleSheet(
            "color: inherit; border: none; background: transparent;"
        )

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
        self.setLayout(layout)
        self.setMinimumHeight(GUI_STATS_CARD_HEIGHT or STATS_CARD_MIN_HEIGHT)

    def update_value(self, value):
        self.value_label.setText(str(value))
