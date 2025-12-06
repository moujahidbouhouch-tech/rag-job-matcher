from PyQt5 import QtCore, QtWidgets, QtGui

from rag_project.rag_gui.config import (
    PADDING_SMALL,
    BORDER_RADIUS,
    FONT_FAMILY,
    PADDING_MEDIUM,
    GUI_CONTEXT_SCORE_FORMAT,
    GUI_CONTEXT_TITLE_FALLBACK,
)


class ContextCard(QtWidgets.QFrame):
    """Widget displaying a single source chunk used by the LLM."""

    def __init__(self, source_data: dict, index: int, parent=None):
        super().__init__(parent)
        self.source = source_data
        self.index = index  # e.g. 1 for "[1]"

        self.setObjectName("ContextCard")
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(
            PADDING_MEDIUM, PADDING_MEDIUM, PADDING_MEDIUM, PADDING_MEDIUM
        )
        layout.setSpacing(PADDING_SMALL)

        meta = self.source.get("metadata", {}) or {}
        # --- 1. Header Row (Source Name + Score) ---
        header_layout = QtWidgets.QHBoxLayout()

        # Citation Number + Filename
        filename = (
            self.source.get("title")
            or meta.get("title")
            or meta.get("source")
            or GUI_CONTEXT_TITLE_FALLBACK
        )

        title_lbl = QtWidgets.QLabel(f"[{self.index}] {filename}")
        font = QtGui.QFont(FONT_FAMILY)
        font.setBold(True)
        title_lbl.setFont(font)
        title_lbl.setObjectName("ContextTitle")

        # Score (if available)
        score = self.source.get("score")
        score_text = GUI_CONTEXT_SCORE_FORMAT.format(score=score) if score else ""
        score_lbl = QtWidgets.QLabel(score_text)
        score_lbl.setObjectName("ContextScore")

        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(score_lbl)

        layout.addLayout(header_layout)

        # --- 1b. Meta line (doc type or source info) ---
        doc_type = self.source.get("doc_type") or meta.get("doc_type")
        if doc_type:
            meta_lbl = QtWidgets.QLabel(f"Type: {doc_type}")
            meta_font = QtGui.QFont(FONT_FAMILY)
            meta_font.setPointSize(meta_font.pointSize() - 1)
            meta_lbl.setFont(meta_font)
            meta_lbl.setStyleSheet("color: rgba(0,0,0,0.6);")
            layout.addWidget(meta_lbl)

        # --- 2. Content Snippet ---
        content = self.source.get("content", "").strip()
        snippet = content[:1200] + ("..." if len(content) > 1200 else "")

        content_view = QtWidgets.QTextBrowser()
        content_view.setPlainText(snippet)
        content_view.setOpenExternalLinks(False)
        content_view.setReadOnly(True)
        content_view.setFrameShape(QtWidgets.QFrame.NoFrame)
        content_view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        content_view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        content_view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        content_view.setWordWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)
        content_view.setMinimumHeight(120)
        content_view.setMaximumHeight(1200)
        layout.addWidget(content_view)
