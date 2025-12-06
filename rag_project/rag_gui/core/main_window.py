from pathlib import Path
from typing import Dict

import psycopg
from PyQt5 import QtCore, QtGui, QtWidgets  # type: ignore
from pgvector.psycopg import register_vector

from rag_project.logger import get_logger
from rag_project.rag_core.app_facade import RAGApp
from rag_project.rag_gui.config import (
    DEFAULT_THEME,
    SIDEBAR_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    PADDING_LARGE,
    PADDING_SMALL,
    GUI_WINDOW_TITLE,
    GUI_THEME_DARK,
    GUI_THEME_LIGHT,
    GUI_SIDEBAR_LABELS,
    GUI_DB_CHECK_TIMEOUT,
)
from rag_project.rag_gui.styles import DarkTheme, LightTheme

# Added RAGView to imports
from rag_project.rag_gui.views import DatabaseView, DeleteView, IngestionView, RAGView
from rag_project.rag_gui.widgets import StatusIndicator

logger = get_logger(__name__)


class ManualIngestionGUI(QtWidgets.QMainWindow):
    """Main window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(GUI_WINDOW_TITLE)
        # More horizontal, less vertical
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self._theme = DEFAULT_THEME
        self._app = self._load_app()
        self._conn_settings = self._make_conn_settings()
        self._build_ui()
        if self._theme == GUI_THEME_DARK:
            self.set_dark_theme()
        else:
            self.set_light_theme()

    def set_dark_theme(self):
        self.setStyleSheet(DarkTheme.get_complete_stylesheet())
        if hasattr(self, "ingestion_btn"):
            self.ingestion_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)
            self.rag_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)
            self.database_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)
            self.delete_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)
            self.theme_toggle_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)
        if hasattr(self, "rag_view"):
            self.rag_view.set_theme("dark")

    def set_light_theme(self):
        self.setStyleSheet(LightTheme.get_complete_stylesheet())
        if hasattr(self, "ingestion_btn"):
            self.ingestion_btn.setStyleSheet(LightTheme.MENU_BUTTON_STYLE)
            self.rag_btn.setStyleSheet(LightTheme.MENU_BUTTON_STYLE)
            self.database_btn.setStyleSheet(LightTheme.MENU_BUTTON_STYLE)
            self.delete_btn.setStyleSheet(LightTheme.MENU_BUTTON_STYLE)
            self.theme_toggle_btn.setStyleSheet(LightTheme.MENU_BUTTON_STYLE)
        if hasattr(self, "rag_view"):
            self.rag_view.set_theme("light")

    def _load_app(self) -> RAGApp:
        try:
            return RAGApp()
        except Exception as exc:  # noqa: BLE001
            QtWidgets.QMessageBox.critical(self, "RAG initialization failed", str(exc))
            raise

    def _make_conn_settings(self) -> Dict[str, str]:
        settings = self._app.settings
        return {
            "host": settings.db_host,
            "port": settings.db_port,
            "dbname": settings.db_name,
            "user": settings.db_user,
            "password": settings.db_password,
        }

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QHBoxLayout(central)
        layout.setContentsMargins(
            PADDING_LARGE, PADDING_LARGE, PADDING_LARGE, PADDING_LARGE
        )
        layout.setSpacing(PADDING_LARGE)

        # Sidebar
        sidebar = QtWidgets.QVBoxLayout()
        sidebar.setSpacing(PADDING_LARGE)
        sidebar.setContentsMargins(0, PADDING_LARGE + PADDING_SMALL, 0, 0)
        sidebar.setAlignment(QtCore.Qt.AlignTop)

        # --- Create Buttons ---

        # 1. Ingestion (Index 0 - Default)
        self.ingestion_btn = QtWidgets.QPushButton(GUI_SIDEBAR_LABELS["ingestion"])
        self.ingestion_btn.setCheckable(True)
        self.ingestion_btn.setChecked(True)  # Default Active
        self.ingestion_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)

        # 2. Chat RAG (Index 1)
        self.rag_btn = QtWidgets.QPushButton(GUI_SIDEBAR_LABELS["rag"])
        self.rag_btn.setCheckable(True)
        self.rag_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)

        # 3. Database (Index 2)
        self.database_btn = QtWidgets.QPushButton(GUI_SIDEBAR_LABELS["database"])
        self.database_btn.setCheckable(True)
        self.database_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)

        # 4. Delete (Index 3)
        self.delete_btn = QtWidgets.QPushButton(GUI_SIDEBAR_LABELS["delete"])
        self.delete_btn.setCheckable(True)
        self.delete_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)

        # Theme Toggle
        self.theme_toggle_btn = QtWidgets.QPushButton(GUI_SIDEBAR_LABELS["toggle"])
        self.theme_toggle_btn.setStyleSheet(DarkTheme.MENU_BUTTON_STYLE)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)

        # --- Wire Buttons to Indices ---
        self.ingestion_btn.clicked.connect(lambda: self.switch_view(0))
        self.rag_btn.clicked.connect(lambda: self.switch_view(1))
        self.database_btn.clicked.connect(lambda: self.switch_view(2))
        self.delete_btn.clicked.connect(lambda: self.switch_view(3))

        # --- Add to Sidebar Layout (Visual Order) ---
        sidebar.addWidget(self.ingestion_btn)
        sidebar.addWidget(self.rag_btn)
        sidebar.addWidget(self.database_btn)
        sidebar.addWidget(self.delete_btn)
        sidebar.addWidget(self.theme_toggle_btn)
        sidebar.addStretch()

        # --- Content Stack ---
        self.content_stack = QtWidgets.QStackedWidget()

        # Initialize Views
        self.ingestion_view = IngestionView(self._app, self.check_database_connection)
        self.rag_view = RAGView(self._app, self._conn_settings)
        self.database_view = DatabaseView(self._conn_settings)
        self.delete_view = DeleteView(self._app.repo, self._conn_settings)

        # Add to stack (Order must match switch_view index)
        self.content_stack.addWidget(self.ingestion_view)  # Index 0
        self.content_stack.addWidget(self.rag_view)  # Index 1
        self.content_stack.addWidget(self.database_view)  # Index 2
        self.content_stack.addWidget(self.delete_view)  # Index 3

        sidebar_container = QtWidgets.QWidget()
        sidebar_container.setLayout(sidebar)
        sidebar_container.setFixedWidth(SIDEBAR_WIDTH)
        layout.addWidget(sidebar_container, stretch=0)
        layout.addWidget(self.content_stack, stretch=1)

    def switch_view(self, index: int):
        self.content_stack.setCurrentIndex(index)
        # Update Sidebar Styling
        self.ingestion_btn.setChecked(index == 0)
        self.rag_btn.setChecked(index == 1)
        self.database_btn.setChecked(index == 2)
        self.delete_btn.setChecked(index == 3)
        # Refresh statuses when switching
        self.update_all_db_status()

    def check_database_connection(self) -> bool:
        try:
            with psycopg.connect(
                connect_timeout=GUI_DB_CHECK_TIMEOUT, **self._conn_settings
            ) as conn:
                register_vector(conn)
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("DB not reachable: %s", exc)
            return False

    def update_all_db_status(self):
        """Update the active view."""
        idx = self.content_stack.currentIndex()

        if idx == 0:
            self.ingestion_view.refresh_db_status()
        elif idx == 1:
            self.rag_view.refresh_data()
        elif idx == 2:
            self.database_view.refresh_statistics()
        elif idx == 3:
            self.delete_view.refresh_statistics()

    def toggle_theme(self):
        if self._theme == GUI_THEME_DARK:
            self._theme = GUI_THEME_LIGHT
            self.set_light_theme()
        else:
            self._theme = GUI_THEME_DARK
            self.set_dark_theme()
