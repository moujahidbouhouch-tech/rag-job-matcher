from PyQt5 import QtCore, QtWidgets, QtGui

from rag_project.rag_gui.config import (
    PADDING_LARGE,
    PADDING_SMALL,
    INPUT_HEIGHT,
    BUTTON_MIN_WIDTH,
    CHAT_INPUT_HEIGHT,
    PADDING_MEDIUM,
    GUI_CHAT_PLACEHOLDER,
    GUI_SEND_BUTTON_LABEL,
)
from rag_project.rag_gui.widgets.rag.chat_bubble import ChatBubble
from rag_project.config import (
    ROUTER_HISTORY_MAX_MESSAGES,
    ROUTER_HISTORY_PER_MESSAGE_TRUNCATE,
)


class ChatArea(QtWidgets.QWidget):
    """Container for Chat History + Input + Send Logic."""

    # Signal to tell the parent (RAGView) to open the context panel with specific sources
    context_requested = QtCore.pyqtSignal(list)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
        self._history: list[dict] = []
        self._history_max_messages = ROUTER_HISTORY_MAX_MESSAGES
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Scroll Area (History)
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.history_container = QtWidgets.QWidget()
        self.history_layout = QtWidgets.QVBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(
            PADDING_LARGE, PADDING_LARGE, PADDING_LARGE, PADDING_LARGE
        )
        self.history_layout.setSpacing(PADDING_MEDIUM)
        self.history_layout.addStretch()  # Pushes messages to bottom

        self.scroll_area.setWidget(self.history_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # 2. Input Area Container
        input_container = QtWidgets.QFrame()
        input_container.setObjectName("ContentPanel")  # Use the panel border style
        # Add a top border manually if theme doesn't handle it perfectly, or rely on container
        input_layout = QtWidgets.QHBoxLayout(input_container)
        input_layout.setContentsMargins(
            PADDING_MEDIUM, PADDING_MEDIUM, PADDING_MEDIUM, PADDING_MEDIUM
        )

        self.input_box = QtWidgets.QTextEdit()
        self.input_box.setPlaceholderText(GUI_CHAT_PLACEHOLDER)
        self.input_box.setFixedHeight(CHAT_INPUT_HEIGHT)
        self.input_box.setObjectName("ChatInput")
        self.input_box.installEventFilter(self)  # Catch Enter key

        self.send_btn = QtWidgets.QPushButton(GUI_SEND_BUTTON_LABEL)
        self.send_btn.setFixedHeight(CHAT_INPUT_HEIGHT)
        self.send_btn.setFixedWidth(BUTTON_MIN_WIDTH)
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.input_box)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_container)

    def eventFilter(self, obj, event):
        """Handle Enter key to send, Shift+Enter for newline."""
        if obj is self.input_box and event.type() == QtCore.QEvent.KeyPress:
            if (
                event.key() == QtCore.Qt.Key_Return
                and not event.modifiers() & QtCore.Qt.ShiftModifier
            ):
                self.send_message()
                return True
        return super().eventFilter(obj, event)

    def add_message(self, text: str, is_user: bool, store: bool = True, citations=None):
        bubble = ChatBubble(text, is_user, citations=citations)
        if not is_user:
            # Connect the AI bubble's citation click
            bubble.citation_clicked.connect(self._on_citation_clicked)

        self.history_layout.addWidget(bubble)

        # Scroll to bottom
        QtCore.QTimer.singleShot(10, self._scroll_to_bottom)
        if store:
            role = "user" if is_user else "assistant"
            self._history.append(
                {"role": role, "content": text[:ROUTER_HISTORY_PER_MESSAGE_TRUNCATE]}
            )
            # keep bounded history
            if len(self._history) > self._history_max_messages:
                self._history = self._history[-self._history_max_messages :]
        return bubble

    def _scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def send_message(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            return

        # 1. UI Update
        self.add_message(text, True)  # Add user bubble
        thinking_bubble = self.add_message("Thinking...", False, store=False)
        self.input_box.clear()
        self.set_input_enabled(False)

        # Delegate to parent routing (RAGView)
        parent_view = self.parent()
        if parent_view and hasattr(parent_view, "start_routing"):
            parent_view.start_routing(text, thinking_bubble)
        else:
            self.add_message("Routing not available.", False)
            self.set_input_enabled(True)

    def get_history_tail(self) -> list[dict]:
        """Return a copy of recent chat messages (bounded)."""
        return list(self._history)

    def set_input_enabled(self, enabled: bool):
        self.input_box.setDisabled(not enabled)
        self.send_btn.setDisabled(not enabled)
        if enabled:
            self.input_box.setFocus()

    def _on_citation_clicked(self, link_id: str):
        """Handle click on a citation marker like [1]."""
        bubble = self.sender()
        if bubble and hasattr(bubble, "citation_map"):
            cited = bubble.citation_map.get(str(link_id))
            if cited:
                self.context_requested.emit([cited])
                return
            # Fallback: emit all citations from this bubble
            if bubble.citation_map:
                self.context_requested.emit(list(bubble.citation_map.values()))
