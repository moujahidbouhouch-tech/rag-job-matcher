import os
from typing import Dict, List
from PyQt5 import QtCore, QtWidgets, QtGui

import psycopg
import requests
from pgvector.psycopg import register_vector

from rag_project.rag_gui.config import (
    PADDING_LARGE,
    PADDING_SMALL,
    FONT_FAMILY,
    FONT_SIZE_TITLE,
    BUTTON_MIN_WIDTH,
    JOB_SELECTOR_WIDTH,
    CONTEXT_PANEL_WIDTH,
    CHAT_INPUT_HEIGHT,
    GUI_RAG_HEADER_TEXT,
    GUI_RAG_JOBLIST_LABEL,
    GUI_LOADING_JOBS_TEXT,
    GUI_NO_JOBS_TEXT,
    GUI_JOB_LOAD_ERROR_PREFIX,
    GUI_NO_CONTEXT_TEXT,
    GUI_CONTEXT_TOGGLE_LABEL,
    GUI_CHAT_PLACEHOLDER,
    GUI_SEND_BUTTON_LABEL,
    GUI_RAG_SELECTION_WARNINGS,
    GUI_RAG_EMPTY_QUESTION_MESSAGE,
    JOB_MATCHING_NO_JOB_SELECTED,
    JOB_MATCHING_LOAD_FAILED,
    JOB_MATCHING_ANALYZING,
    JOB_MATCHING_RESULT_HEADER,
    JOB_MATCHING_MATCH_RATE,
    JOB_MATCHING_MATCHED_COUNT,
    JOB_MATCHING_MATCHED_HEADER,
    JOB_MATCHING_MISSING_HEADER,
    JOB_MATCHING_REQUIREMENTS_HEADER,
    JOB_MATCHING_REQUIREMENT_ITEM,
    GUI_DB_CHECK_TIMEOUT,
    GUI_JOBLOADER_DB_TIMEOUT,
)
from rag_project.config import (
    SQL_FETCH_FULL_DOCUMENT,
    OLLAMA_DEFAULT_HOST,
    OLLAMA_HEALTHCHECK_PATH,
    OLLAMA_HEALTH_TIMEOUT_SECONDS,
)
from rag_project.rag_gui.workers import JobMatchingWorker
from rag_project.rag_gui.styles.theme import DarkTheme, LightTheme
from rag_project.rag_gui.workers.rag_worker import JobLoaderWorker
from rag_project.rag_gui.widgets.rag.job_card import JobCard
from rag_project.rag_gui.widgets.rag.chat_area import ChatArea
from rag_project.rag_gui.widgets.rag.context_card import ContextCard
from rag_project.rag_gui.widgets import StatusIndicator
from rag_project.rag_core.retrieval.router_service import RouteDecision
from rag_project.rag_gui.workers import RetrievalWorker, RouterWorker
from rag_project.logger import get_logger


logger = get_logger(__name__)


class RAGView(QtWidgets.QWidget):
    """Main RAG Interface: Job Selection + Chat + Context."""

    def __init__(self, app, conn_settings: Dict[str, str], parent=None):
        super().__init__(parent)
        self._app = app
        self._conn_settings = conn_settings

        self._jobs: List[dict] = []
        self._selected_job_ids: set = set()
        self._worker = None
        self._job_worker = None
        self._retrieval_worker = None
        self._router_worker = None
        self._theme = "dark"

        self._build_ui()
        self.refresh_status()
        # We trigger loading via refresh_data() when view is switched

    def _build_ui(self):
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(
            PADDING_LARGE, PADDING_LARGE, PADDING_LARGE, PADDING_LARGE
        )
        outer.setSpacing(PADDING_SMALL)

        status_header = QtWidgets.QHBoxLayout()
        status_header.addStretch()
        self.db_indicator = StatusIndicator()
        self.db_status_label = QtWidgets.QLabel("DB: checking...")
        self.model_indicator = StatusIndicator()
        self.model_status_label = QtWidgets.QLabel("Models: checking...")
        status_header.addWidget(self.db_indicator)
        status_header.addWidget(self.db_status_label)
        status_header.addSpacing(PADDING_SMALL)
        status_header.addWidget(self.model_indicator)
        status_header.addWidget(self.model_status_label)
        outer.addLayout(status_header)

        # Main Layout
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(PADDING_LARGE)

        # ==========================
        # COL 1: Job Selector
        # ==========================
        self.left_col = QtWidgets.QWidget()
        self.left_col.setFixedWidth(JOB_SELECTOR_WIDTH)

        left_layout = QtWidgets.QVBoxLayout(self.left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(PADDING_SMALL)

        # Header
        title = QtWidgets.QLabel(GUI_RAG_JOBLIST_LABEL)
        title.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_TITLE, QtGui.QFont.DemiBold))
        left_layout.addWidget(title)

        # Loading Indicator (Hidden by default)
        self.loading_label = QtWidgets.QLabel(GUI_LOADING_JOBS_TEXT)
        self.loading_label.setAlignment(QtCore.Qt.AlignCenter)
        self.loading_label.setVisible(False)
        left_layout.addWidget(self.loading_label)

        # Scroll Area for Cards
        self.job_scroll = QtWidgets.QScrollArea()
        self.job_scroll.setWidgetResizable(True)
        self.job_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.job_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.job_container = QtWidgets.QWidget()
        self.job_card_layout = QtWidgets.QVBoxLayout(self.job_container)
        self.job_card_layout.setContentsMargins(0, 0, 0, 0)
        self.job_card_layout.setSpacing(PADDING_SMALL)
        self.job_card_layout.addStretch()  # Push items up

        self.job_scroll.setWidget(self.job_container)
        left_layout.addWidget(self.job_scroll)

        # ==========================
        # COL 2: Chat Area
        # ==========================
        # We pass 'self' as parent so ChatArea can find us
        self.center_col = ChatArea(self._app, parent=self)
        self.center_col.setObjectName("ContentPanel")  # Target the Theme Style

        # Connect Signal: When ChatArea gets citations, open right panel
        self.center_col.context_requested.connect(self.update_context_panel)

        # ==========================
        # COL 3: Context Panel
        # ==========================
        self.right_col = QtWidgets.QFrame()
        self.right_col.setObjectName("ContentPanel")  # Target the Theme Style
        self.right_col.setFixedWidth(CONTEXT_PANEL_WIDTH)
        self.right_col.setVisible(False)  # Start hidden

        # Right Column Layout
        self.right_layout_container = QtWidgets.QVBoxLayout(self.right_col)

        # Header Row (Title + Close Button)
        header_row = QtWidgets.QHBoxLayout()
        r_title = QtWidgets.QLabel(GUI_RAG_HEADER_TEXT)
        r_title.setObjectName("ContextHeaderTitle")
        r_title.setFont(QtGui.QFont(FONT_FAMILY, FONT_SIZE_TITLE, QtGui.QFont.DemiBold))

        close_btn = QtWidgets.QPushButton("✖")
        close_btn.setFixedSize(30, 30)
        close_btn.setFlat(True)
        close_btn.clicked.connect(self.toggle_context_panel)

        header_row.addWidget(r_title)
        header_row.addStretch()
        header_row.addWidget(close_btn)

        self.right_layout_container.addLayout(header_row)

        # Placeholder for source cards (Will be populated dynamically)
        self.sources_scroll = QtWidgets.QScrollArea()
        self.sources_scroll.setWidgetResizable(True)
        self.sources_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.sources_container = QtWidgets.QWidget()
        self.sources_layout = QtWidgets.QVBoxLayout(self.sources_container)
        self.sources_layout.addStretch()
        self.sources_scroll.setWidget(self.sources_container)

        self.right_layout_container.addWidget(self.sources_scroll)

        # Add columns to main
        self.main_layout.addWidget(self.left_col)
        self.main_layout.addWidget(self.center_col, stretch=1)
        self.main_layout.addWidget(self.right_col)
        outer.addLayout(self.main_layout)

    # --- Logic ---

    def get_selected_job_ids(self) -> List[str]:
        """Public method for ChatArea to access selected IDs safely."""
        return list(self._selected_job_ids)

    def refresh_data(self):
        """Called by Main Window. Starts background loader."""
        # Only load if empty to prevent flickering, or force refresh if needed
        if not self._jobs:
            self.load_jobs()
        self.refresh_status()

    # --- Routing & dispatch ---
    def route_input(self, user_text: str) -> RouteDecision:
        """Use RouterService to classify user intent."""
        context = {"selected_jobs": list(self._selected_job_ids)}
        logger.info(
            "RAGView route_input text len=%d selected_jobs=%d",
            len(user_text),
            len(self._selected_job_ids),
        )
        return self._app.router.route(user_text, context)

    def start_routing(self, user_text: str, thinking_bubble=None):
        """Start router in a background thread to avoid blocking UI."""
        history = (
            self.center_col.get_history_tail()
            if hasattr(self.center_col, "get_history_tail")
            else []
        )
        context = {"selected_jobs": list(self._selected_job_ids), "history": history}
        logger.info(
            "RAGView start_routing text len=%d history_len=%d",
            len(user_text),
            len(history),
        )
        self._router_worker = RouterWorker(self._app.router, user_text, context)
        self._router_worker.decision_ready.connect(
            lambda decision: self.dispatch_action(decision, user_text, thinking_bubble)
        )
        self._router_worker.error_occurred.connect(
            lambda msg: self._on_route_error(msg, thinking_bubble)
        )
        self._router_worker.start()

    def dispatch_action(
        self, decision: RouteDecision, user_text: str, thinking_bubble=None
    ):
        """Execute action based on router decision."""
        if decision.needs_clarification:
            self.center_col.add_message(
                decision.clarification_prompt or "What would you like me to do?",
                False,
            )
            self.center_col.set_input_enabled(True)
            return

        handlers = {
            "job_match": self._handle_job_match,
            "retrieve": self._handle_retrieve,
            "help": self._handle_help,
            "unknown": self._handle_unknown,
        }
        handler = handlers.get(decision.action, self._handle_unknown)
        handler(user_text, decision, thinking_bubble)

    def _handle_job_match(
        self, user_text: str, _decision: RouteDecision, thinking_bubble=None
    ):
        # We don't update the bubble here; job matching already posts progress messages
        self.run_job_matching(user_text)

    def _handle_retrieve(
        self, _user_text: str, _decision: RouteDecision, thinking_bubble=None
    ):
        question = _user_text
        # run retrieval in background to avoid freezing UI
        self._retrieval_worker = RetrievalWorker(self._app.query, question)
        self._retrieval_worker.answer_ready.connect(
            lambda answer: self._on_retrieval_done(answer, thinking_bubble)
        )
        self._retrieval_worker.error_occurred.connect(
            lambda msg: self._on_retrieval_error(msg, thinking_bubble)
        )
        self._retrieval_worker.start()

    def _handle_help(
        self, _user_text: str, _decision: RouteDecision, thinking_bubble=None
    ):
        help_text = (
            "I can help you with:\n"
            "- Job Matching: select a job and ask to compare.\n"
            "- Retrieval (coming soon): ask questions about indexed docs.\n"
            "- Help: ask what I can do."
        )
        self.center_col.add_message(help_text, False)
        self.center_col.set_input_enabled(True)

    def _handle_unknown(
        self, _user_text: str, _decision: RouteDecision, thinking_bubble=None
    ):
        self.center_col.add_message(
            "I'm not sure what to do. Try:\n"
            '• "Compare me to this job"\n'
            '• "What skills are required?"\n'
            '• "Help"',
            False,
        )
        self.center_col.set_input_enabled(True)

    def _on_retrieval_done(self, answer, thinking_bubble=None):
        logger.info("RAGView retrieval completed")
        if thinking_bubble is not None:
            thinking_bubble.lbl.setText(
                f"<div style='white-space: pre-wrap; word-break: break-word;'>{answer.answer}</div>"
            )
        else:
            self.center_col.add_message(answer.answer, False)
        self.center_col.set_input_enabled(True)
        self._retrieval_worker = None

    def _on_retrieval_error(self, msg: str, thinking_bubble=None):
        logger.error("RAGView retrieval error: %s", msg)
        if thinking_bubble is not None:
            thinking_bubble.lbl.setText(
                f"<div style='white-space: pre-wrap; word-break: break-word;'>Retrieval failed: {msg}</div>"
            )
        else:
            self.center_col.add_message(f"Retrieval failed: {msg}", False)
        self.center_col.set_input_enabled(True)
        self._retrieval_worker = None

    def _on_route_error(self, msg: str, thinking_bubble=None):
        logger.error("RAGView routing error: %s", msg)
        if thinking_bubble is not None:
            thinking_bubble.lbl.setText(
                f"<div style='white-space: pre-wrap; word-break: break-word;'>Routing failed: {msg}</div>"
            )
        else:
            self.center_col.add_message(f"Routing failed: {msg}", False)
        self.center_col.set_input_enabled(True)
        self._router_worker = None

    def load_jobs(self):
        logger.info("RAGView loading jobs")
        self.loading_label.setVisible(True)
        self.job_scroll.setVisible(False)

        self._worker = JobLoaderWorker(self._conn_settings)
        self._worker.finished.connect(self.on_jobs_loaded)
        self._worker.error.connect(self.on_worker_error)
        self._worker.start()

    def on_jobs_loaded(self, jobs: list):
        logger.info("RAGView jobs loaded count=%d", len(jobs))
        self.loading_label.setVisible(False)
        self.job_scroll.setVisible(True)
        self._jobs = jobs

        # Clear existing cards (except the stretch item)
        while self.job_card_layout.count() > 1:
            item = self.job_card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not jobs:
            lbl = QtWidgets.QLabel(GUI_NO_JOBS_TEXT)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            self.job_card_layout.insertWidget(0, lbl)
            return

        # Create Cards
        for job in jobs:
            card = JobCard(job)
            card.selection_changed.connect(self.on_job_selection_change)
            self.job_card_layout.insertWidget(self.job_card_layout.count() - 1, card)

    def on_worker_error(self, err: str):
        logger.error("RAGView job load error: %s", err)
        self.loading_label.setText(f"{GUI_JOB_LOAD_ERROR_PREFIX}{err}")
        self.loading_label.setStyleSheet("color: red;")

    # --- Job Matching ---
    def run_job_matching(self, question: str):
        # Require a selected job
        if not self._selected_job_ids:
            self.center_col.add_message(JOB_MATCHING_NO_JOB_SELECTED, False)
            self.center_col.set_input_enabled(True)
            return

        job_id = next(iter(self._selected_job_ids))
        job_text = self._load_job_text(job_id)
        if not job_text:
            self.center_col.add_message(JOB_MATCHING_LOAD_FAILED, False)
            self.center_col.set_input_enabled(True)
            return

        logger.info(
            "RAGView running job matching selected_id=%s question_len=%d",
            job_id,
            len(question),
        )
        self.center_col.add_message(JOB_MATCHING_ANALYZING, False)
        self._job_worker = JobMatchingWorker(self._app.job_matching, job_text)
        self._job_worker.progress_update.connect(
            lambda msg: self.center_col.add_message(msg, False)
        )
        self._job_worker.requirements_ready.connect(self._on_requirements_ready)
        self._job_worker.evaluation_ready.connect(self._on_evaluation_ready)
        self._job_worker.analysis_complete.connect(self._on_job_match_complete)
        self._job_worker.error_occurred.connect(self._on_job_match_error)
        self._job_worker.start()

    def _load_job_text(self, job_id: str) -> str:
        try:
            with psycopg.connect(
                connect_timeout=GUI_JOBLOADER_DB_TIMEOUT, **self._conn_settings
            ) as conn:
                register_vector(conn)
                with conn.cursor() as cur:
                    cur.execute(SQL_FETCH_FULL_DOCUMENT, (job_id,))
                    rows = cur.fetchall()
                    return "\n".join([r[0] for r in rows]) if rows else ""
        except Exception as exc:  # noqa: BLE001
            self.center_col.add_message(f"{JOB_MATCHING_LOAD_FAILED} ({exc})", False)
            logger.error(
                "RAGView failed loading job text id=%s: %s", job_id, exc, exc_info=True
            )
            return ""

    def _on_job_match_complete(self, result):
        summary = [
            JOB_MATCHING_RESULT_HEADER,
            JOB_MATCHING_MATCH_RATE.format(rate=result.match_rate),
            JOB_MATCHING_MATCHED_COUNT.format(
                match=result.match_count, total=len(result.evaluations)
            ),
        ]

        logger.info(
            "RAGView job matching complete rate=%.1f%% matches=%d/%d",
            result.match_rate,
            result.match_count,
            len(result.evaluations),
        )
        self.center_col.add_message("\n".join(summary), False)
        self.center_col.set_input_enabled(True)

    def _on_job_match_error(self, msg: str):
        logger.error("RAGView job matching error: %s", msg)
        self.center_col.add_message(msg, False)
        self.center_col.set_input_enabled(True)

    def _on_evaluation_ready(self, req, evaluation):
        verdict = evaluation.verdict if hasattr(evaluation, "verdict") else "Unknown"
        reasoning = evaluation.reasoning if hasattr(evaluation, "reasoning") else ""
        citations = getattr(evaluation, "citations", []) or []
        markers = (
            " ".join([f"[{c['label']}]({c['label']})" for c in citations])
            if citations
            else ""
        )
        msg = f"{verdict} | {req.name}: {reasoning} {markers}".strip()
        sources = []
        for c in citations:
            meta = c.get("metadata") or {}
            sources.append(
                {
                    "label": c.get("label"),
                    "content": c.get("content", ""),
                    "score": c.get("score"),
                    "metadata": {
                        "doc_type": c.get("doc_type") or meta.get("doc_type"),
                        "title": c.get("title") or meta.get("title"),
                        "company": c.get("company") or meta.get("company"),
                        "chunk_id": c.get("chunk_id") or meta.get("chunk_id"),
                        "doc_id": c.get("doc_id") or meta.get("doc_id"),
                    },
                }
            )
        self.center_col.add_message(msg, False, citations=sources)

    def _on_requirements_ready(self, requirements):
        if not requirements:
            self.center_col.add_message("No requirements extracted.", False)
            return
        logger.info("RAGView requirements ready count=%d", len(requirements))
        lines = [JOB_MATCHING_REQUIREMENTS_HEADER]
        lines.extend(
            [
                JOB_MATCHING_REQUIREMENT_ITEM.format(
                    name=req.name, category=req.category, query=req.search_query
                )
                for req in requirements
            ]
        )
        self.center_col.add_message("\n".join(lines), False)

    def on_job_selection_change(self, job_id: str, is_checked: bool):
        if is_checked:
            self._selected_job_ids.add(job_id)
        else:
            self._selected_job_ids.discard(job_id)
        logger.info("RAGView selection changed count=%d", len(self._selected_job_ids))

    def update_context_panel(self, sources: list):
        """Populate the right column and show it."""
        # 1. Clear previous content
        # Clear the sources_layout
        while self.sources_layout.count() > 1:  # Keep the stretch at the bottom
            item = self.sources_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 2. Add Sources
        if not sources:
            lbl = QtWidgets.QLabel(GUI_NO_CONTEXT_TEXT)
            lbl.setStyleSheet("font-style: italic;")
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            self.sources_layout.insertWidget(0, lbl)
        else:
            # Enumerate to give them numbers [1], [2]
            for i, src in enumerate(sources, start=1):
                card = ContextCard(src, index=i)
                # Insert before the stretch item
                self.sources_layout.insertWidget(self.sources_layout.count() - 1, card)

        # 3. Animate/Show
        if not self.right_col.isVisible():
            self.right_col.setVisible(True)

    # --- Status helpers ---
    def refresh_status(self):
        """Refresh DB and model reachability indicators."""
        db_ok = self._check_db()
        self.db_indicator.set_status(db_ok)
        self.db_status_label.setText("DB: connected" if db_ok else "DB: error")

        model_ok = self._check_models()
        self.model_indicator.set_status(model_ok)
        self.model_status_label.setText(
            "Models: ready" if model_ok else "Models: error"
        )

    def _check_db(self) -> bool:
        try:
            with psycopg.connect(
                connect_timeout=GUI_DB_CHECK_TIMEOUT, **self._conn_settings
            ) as conn:
                register_vector(conn)
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True
        except Exception:
            return False

    def _check_models(self) -> bool:
        try:
            host = getattr(
                self._app.settings,
                "ollama_host",
                os.getenv("OLLAMA_HOST", OLLAMA_DEFAULT_HOST),
            )
            resp = requests.get(
                f"{host}{OLLAMA_HEALTHCHECK_PATH}",
                timeout=OLLAMA_HEALTH_TIMEOUT_SECONDS,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def toggle_context_panel(self):
        self.right_col.setVisible(not self.right_col.isVisible())

    # --- Theming ---
    def set_theme(self, theme: str):
        """Apply theme-specific styles for RagView widgets."""
        self._theme = theme
        # Chat bubbles and context cards rely on global stylesheet; no per-widget restyle needed here.
        # If we had theme-specific adjustments (e.g., icons), we could apply them here.

    def refresh_theme(self):
        """Reapply theme after main window toggles."""
        self.set_theme(self._theme)
