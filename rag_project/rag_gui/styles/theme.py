from rag_project.rag_gui.config.theme import (
    COLOR_DARK_ACCENT,
    COLOR_DARK_BG,
    COLOR_DARK_BORDER,
    COLOR_DARK_BORDER_STRONG,
    COLOR_DARK_DANGER,
    COLOR_DARK_DANGER_DISABLED,
    COLOR_DARK_DANGER_HOVER,
    COLOR_DARK_MUTED,
    COLOR_DARK_SUCCESS,
    COLOR_DARK_SUCCESS_DISABLED,
    COLOR_DARK_SUCCESS_HOVER,
    COLOR_DARK_TEXT,
    COLOR_DARK_WIDGET,
    COLOR_LIGHT_ACCENT,
    COLOR_LIGHT_BG,
    COLOR_LIGHT_BORDER,
    COLOR_LIGHT_BORDER_STRONG,
    COLOR_LIGHT_DANGER,
    COLOR_LIGHT_DANGER_DISABLED,
    COLOR_LIGHT_DANGER_HOVER,
    COLOR_LIGHT_MUTED,
    COLOR_LIGHT_SUCCESS,
    COLOR_LIGHT_SUCCESS_DISABLED,
    COLOR_LIGHT_SUCCESS_HOVER,
    COLOR_LIGHT_TEXT,
    COLOR_LIGHT_WIDGET,
    COLOR_CARD_TEXT_DARK,
    COLOR_CARD_TEXT_LIGHT,
    FONT_WEIGHT_SEMIBOLD,
    COLOR_CHAT_USER_TEXT,
    COLOR_CHAT_ASSISTANT_BORDER_DARK,
    COLOR_CHAT_ASSISTANT_BORDER_LIGHT,
)

from rag_project.rag_gui.config.layout import (
    BORDER_RADIUS,
    BORDER_RADIUS_LARGE,
    BORDER_RADIUS_SMALL,
    BUTTON_MIN_HEIGHT,
    BUTTON_MIN_WIDTH,
    GROUP_TITLE_PADDING_X,
    GROUP_TITLE_PADDING_Y,
    GROUPBOX_TITLE_MARGIN_TOP,
    PADDING_MEDIUM,
    PADDING_SMALL,
    PROGRESSBAR_HEIGHT,
    SCROLLBAR_RADIUS,
    SCROLLBAR_WIDTH,
    MENU_BUTTON_PADDING_X,
    MENU_BUTTON_PADDING_Y,
    COMBOBOX_PADDING,
    INPUT_PADDING_X,
    INPUT_PADDING_Y,
    HEADER_SECTION_PADDING,
)


class DarkTheme:
    """Dark Theme with Enhanced Rich Text Support."""

    MAIN_WINDOW_STYLE = f"""
        QMainWindow {{ background-color: {COLOR_DARK_BG}; }}
        QWidget {{ 
            color: {COLOR_DARK_TEXT}; 
            background-color: {COLOR_DARK_BG}; 
            outline: none; 
        }}
        QGroupBox {{ 
            border: 1px solid {COLOR_DARK_BORDER_STRONG}; 
            border-radius: {BORDER_RADIUS}px; 
            margin-top: {GROUPBOX_TITLE_MARGIN_TOP}px; 
        }}
        QGroupBox::title {{ 
            subcontrol-origin: margin; 
            subcontrol-position: top left; 
            padding: {GROUP_TITLE_PADDING_Y}px {GROUP_TITLE_PADDING_X}px; 
            background-color: {COLOR_DARK_BG};
            color: {COLOR_DARK_MUTED};
        }}
        QToolTip {{
            background-color: {COLOR_DARK_WIDGET};
            color: {COLOR_DARK_TEXT};
            border: 1px solid {COLOR_DARK_BORDER};
        }}
    """

    BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {COLOR_DARK_WIDGET};
            color: {COLOR_DARK_TEXT};
            border: 1px solid {COLOR_DARK_BORDER};
            padding: {PADDING_MEDIUM}px {PADDING_SMALL * 2}px;
            border-radius: {BORDER_RADIUS}px;
            min-height: {BUTTON_MIN_HEIGHT}px;
            min-width: {BUTTON_MIN_WIDTH}px;
        }}
        QPushButton:hover {{ 
            background-color: {COLOR_DARK_ACCENT}; 
            color: {COLOR_DARK_BG}; 
            border-color: {COLOR_DARK_ACCENT}; 
        }}
        QPushButton:pressed {{ 
            background-color: {COLOR_DARK_BORDER_STRONG}; 
            color: {COLOR_DARK_BG};
        }}
        QPushButton:disabled {{ 
            color: {COLOR_DARK_MUTED}; 
            background-color: {COLOR_DARK_WIDGET}; 
            border: 1px solid {COLOR_DARK_BORDER_STRONG}; 
        }}
    """

    PRIMARY_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {COLOR_DARK_SUCCESS};
            color: {COLOR_DARK_BG};
            border: none;
            padding: {PADDING_MEDIUM}px {PADDING_SMALL * 2}px;
            border-radius: {BORDER_RADIUS}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            min-height: {BUTTON_MIN_HEIGHT}px;
            min-width: {BUTTON_MIN_WIDTH}px;
        }}
        QPushButton:hover {{ background-color: {COLOR_DARK_SUCCESS_HOVER}; }}
        QPushButton:pressed {{ background-color: {COLOR_DARK_SUCCESS_DISABLED}; }}
        QPushButton:disabled {{ 
            background-color: {COLOR_DARK_SUCCESS_DISABLED}; 
            color: {COLOR_DARK_MUTED}; 
        }}
    """

    DANGER_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {COLOR_DARK_DANGER};
            color: {COLOR_DARK_BG};
            border: none;
            padding: {PADDING_MEDIUM}px {PADDING_SMALL * 2}px;
            border-radius: {BORDER_RADIUS}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            min-height: {BUTTON_MIN_HEIGHT}px;
            min-width: {BUTTON_MIN_WIDTH}px;
        }}
        QPushButton:hover {{ background-color: {COLOR_DARK_DANGER_HOVER}; }}
        QPushButton:pressed {{ background-color: {COLOR_DARK_DANGER_DISABLED}; }}
        QPushButton:disabled {{ 
            background-color: {COLOR_DARK_DANGER_DISABLED}; 
            color: {COLOR_DARK_MUTED}; 
        }}
    """

    MENU_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {COLOR_DARK_BG};
            color: {COLOR_DARK_MUTED};
            border: 1px solid {COLOR_DARK_BORDER_STRONG};
            padding: {MENU_BUTTON_PADDING_Y}px {MENU_BUTTON_PADDING_X}px;
            border-radius: {BORDER_RADIUS_LARGE}px;
            text-align: left;
            min-height: {BUTTON_MIN_HEIGHT}px;
        }}
        QPushButton:checked {{ 
            background-color: {COLOR_DARK_WIDGET}; 
            border-color: {COLOR_DARK_ACCENT}; 
            color: {COLOR_DARK_TEXT};
        }}
        QPushButton:hover {{ 
            background-color: {COLOR_DARK_ACCENT}; 
            color: {COLOR_DARK_BG}; 
            border-color: {COLOR_DARK_ACCENT}; 
        }}
    """

    COMBOBOX_STYLE = f"""
        QComboBox {{
            background-color: {COLOR_DARK_BG};
            color: {COLOR_DARK_TEXT};
            border: 1px solid {COLOR_DARK_BORDER};
            padding: {COMBOBOX_PADDING}px;
            padding-left: {COMBOBOX_PADDING * 2}px;
            border-radius: {BORDER_RADIUS}px;
        }}
        QComboBox::drop-down {{ 
            border: none; 
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border: none;
            color: {COLOR_DARK_MUTED}; 
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLOR_DARK_BG};
            color: {COLOR_DARK_TEXT};
            selection-background-color: {COLOR_DARK_WIDGET};
            border: 1px solid {COLOR_DARK_BORDER};
            outline: none;
        }}
    """

    PROGRESSBAR_STYLE = f"""
        QProgressBar {{
            background-color: {COLOR_DARK_BG};
            color: {COLOR_DARK_MUTED};
            border: 1px solid {COLOR_DARK_BORDER_STRONG};
            border-radius: {BORDER_RADIUS}px;
            text-align: center;
            min-height: {PROGRESSBAR_HEIGHT}px;
        }}
        QProgressBar::chunk {{
            background-color: {COLOR_DARK_SUCCESS};
            border-radius: {BORDER_RADIUS_SMALL}px;
        }}
    """

    INPUT_STYLE = f"""
        QTextEdit, QPlainTextEdit, QLineEdit {{
            background-color: {COLOR_DARK_BG};
            color: {COLOR_DARK_TEXT};
            border: 1px solid {COLOR_DARK_BORDER_STRONG};
            border-radius: {BORDER_RADIUS}px;
            padding: {INPUT_PADDING_Y}px {INPUT_PADDING_X}px;
        }}
        QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {{
            border: 1px solid {COLOR_DARK_ACCENT};
        }}
    """

    TABLEWIDGET_STYLE = f"""
        QTableWidget {{
            background-color: {COLOR_DARK_BG};
            color: {COLOR_DARK_TEXT};
            gridline-color: {COLOR_DARK_BORDER_STRONG};
            border: 1px solid {COLOR_DARK_BORDER_STRONG};
            border-radius: {BORDER_RADIUS}px;
            selection-background-color: {COLOR_DARK_WIDGET};
            selection-color: {COLOR_DARK_ACCENT};
        }}
        QTableWidget::item {{
            padding: 4px;
        }}
    """

    HEADERVIEW_STYLE = f"""
        QHeaderView {{ background-color: {COLOR_DARK_BG}; border: none; }}
        QHeaderView::section {{
            background-color: {COLOR_DARK_BG};
            color: {COLOR_DARK_MUTED};
            padding: {HEADER_SECTION_PADDING}px;
            border: none;
            border-bottom: 1px solid {COLOR_DARK_BORDER_STRONG};
            border-right: 1px solid {COLOR_DARK_BORDER_STRONG};
        }}
    """

    SCROLLBAR_STYLE = f"""
        QScrollBar:vertical {{
            background: {COLOR_DARK_BG};
            width: {SCROLLBAR_WIDTH}px;
            margin: 0px;
        }}
        QScrollBar:horizontal {{
            background: {COLOR_DARK_BG};
            height: {SCROLLBAR_WIDTH}px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {COLOR_DARK_BORDER_STRONG};
            min-height: 20px;
            border-radius: {SCROLLBAR_RADIUS}px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background: {COLOR_DARK_BORDER_STRONG};
            min-width: 20px;
            border-radius: {SCROLLBAR_RADIUS}px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{ 
            background: {COLOR_DARK_BORDER}; 
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            height: 0px;
            width: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
    """

    CHECKBOX_STYLE = f"""
        QCheckBox {{ color: {COLOR_DARK_TEXT}; spacing: {PADDING_SMALL}px; }}
        QCheckBox::indicator {{
            width: 16px; 
            height: 16px;
            border-radius: {BORDER_RADIUS_SMALL}px;
            border: 1px solid {COLOR_DARK_BORDER};
            background-color: {COLOR_DARK_BG};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLOR_DARK_ACCENT};
            border-color: {COLOR_DARK_ACCENT};
        }}
    """

    JOB_CARD_STYLE = f"""
        QFrame#JobCard {{
            background-color: {COLOR_DARK_WIDGET};
            border: 1px solid {COLOR_DARK_BORDER};
            border-radius: {BORDER_RADIUS}px;
        }}
        QFrame#JobCard:hover {{
            border: 1px solid {COLOR_DARK_ACCENT};
        }}
        QFrame#JobCard[selected="true"] {{
            background-color: {COLOR_DARK_WIDGET};
            border: 1px solid {COLOR_DARK_ACCENT};
            border-left: 4px solid {COLOR_DARK_ACCENT};
        }}
        QLabel#JobTitle {{ font-weight: {FONT_WEIGHT_SEMIBOLD}; font-size: 13px; color: {COLOR_DARK_TEXT}; background-color: {COLOR_DARK_WIDGET}; }}
        QLabel#JobCompany {{ font-size: 11px; color: {COLOR_DARK_MUTED}; background-color: {COLOR_DARK_WIDGET}; }}
        QLabel#JobMeta {{ font-size: 10px; color: {COLOR_DARK_MUTED}; background-color: {COLOR_DARK_WIDGET}; }}
        QCheckBox#JobCardCheckbox::indicator {{
            width: 16px; 
            height: 16px;
            border-radius: {BORDER_RADIUS_SMALL}px;
            border: 1px solid {COLOR_DARK_BORDER};
            background-color: {COLOR_DARK_BG};
        }}
        QCheckBox#JobCardCheckbox::indicator:checked {{
            background-color: {COLOR_DARK_ACCENT};
            border-color: {COLOR_DARK_ACCENT};
        }}
    """

    PANEL_STYLE = f"""
        QFrame#ContentPanel {{
            background-color: {COLOR_DARK_WIDGET};
            border: 1px solid {COLOR_DARK_BORDER_STRONG};
            border-radius: {BORDER_RADIUS}px;
        }}
    """

    # =========================================================================
    # ENHANCED: Chat Styles with Rich Text Elements
    # =========================================================================
    CHAT_STYLES = f"""
        /* Base chat bubbles */
        QFrame#UserBubble {{
            background-color: {COLOR_DARK_ACCENT};
            border-radius: {BORDER_RADIUS}px;
            border-bottom-right-radius: 2px;
        }}
        
        QLabel#UserBubbleLabel {{ 
            color: {COLOR_CHAT_USER_TEXT}; 
            background-color: {COLOR_DARK_ACCENT};
            line-height: 1.6;
        }}
        
        QFrame#AssistantBubble {{
            background-color: {COLOR_DARK_WIDGET};
            border: 1px solid {COLOR_CHAT_ASSISTANT_BORDER_DARK};
            border-radius: {BORDER_RADIUS}px;
            border-bottom-left-radius: 2px;
        }}
        
        QLabel#AssistantBubbleLabel {{ 
            color: {COLOR_DARK_TEXT}; 
            background-color: {COLOR_DARK_WIDGET};
            line-height: 1.6;
        }}
        
        /* Rich text elements inside bubbles */
        QLabel#AssistantBubbleLabel h1,
        QLabel#AssistantBubbleLabel h2,
        QLabel#AssistantBubbleLabel h3 {{
            color: #e8e8e8;
            font-weight: 600;
            margin-top: 14px;
            margin-bottom: 6px;
            line-height: 1.3;
        }}
        
        QLabel#AssistantBubbleLabel h1 {{ font-size: 18px; }}
        QLabel#AssistantBubbleLabel h2 {{ font-size: 16px; }}
        QLabel#AssistantBubbleLabel h3 {{ font-size: 14px; }}
        
        QLabel#AssistantBubbleLabel strong {{
            font-weight: 700;
            color: #ffffff;
        }}
        
        QLabel#AssistantBubbleLabel em {{
            font-style: italic;
            color: #d5d5d5;
        }}
        
        QLabel#AssistantBubbleLabel ul,
        QLabel#AssistantBubbleLabel ol {{
            margin: 8px 0;
            padding-left: 20px;
        }}
        
        QLabel#AssistantBubbleLabel li {{
            margin: 4px 0;
            line-height: 1.5;
        }}
        
        QLabel#AssistantBubbleLabel code {{
            background-color: rgba(0, 0, 0, 0.3);
            color: #ff9e64;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        QLabel#AssistantBubbleLabel pre {{
            background-color: rgba(0, 0, 0, 0.4);
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
            overflow-x: auto;
        }}
        
        QLabel#AssistantBubbleLabel pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        QLabel#AssistantBubbleLabel a {{
            color: {COLOR_DARK_ACCENT};
            text-decoration: none;
        }}
        
        QLabel#AssistantBubbleLabel a:hover {{
            text-decoration: underline;
        }}
        
        QLabel#AssistantBubbleLabel blockquote {{
            border-left: 3px solid #606060;
            padding-left: 12px;
            margin: 8px 0;
            font-style: italic;
            color: #b5b5b5;
        }}
        
        QLabel#AssistantBubbleLabel hr {{
            border: none;
            border-top: 1px solid #555;
            margin: 14px 0;
        }}
        
        /* Input area */
        QTextEdit#ChatInput {{ 
            background-color: {COLOR_DARK_WIDGET}; 
            border: 1px solid {COLOR_DARK_BORDER_STRONG}; 
            border-radius: {BORDER_RADIUS}px; 
        }}
        QTextEdit#ChatInput:focus {{ border: 1px solid {COLOR_DARK_ACCENT}; }}

        /* Context cards */
        QFrame#ContextCard {{
            border: 1px solid {COLOR_DARK_BORDER_STRONG};
            border-left: 4px solid {COLOR_DARK_ACCENT};
            border-radius: {BORDER_RADIUS}px;
            background-color: {COLOR_DARK_WIDGET};
            padding: {PADDING_SMALL}px;
        }}
        QLabel#ContextTitle {{ color: {COLOR_DARK_ACCENT}; font-weight: {FONT_WEIGHT_SEMIBOLD}; }}
        QLabel#ContextScore {{ color: {COLOR_DARK_MUTED}; font-size: 10px; background-color: {COLOR_DARK_WIDGET}; }}
        QFrame#ContextCard QLabel {{ background-color: {COLOR_DARK_WIDGET}; }}
        QLabel#ContextHeaderTitle {{ background-color: {COLOR_DARK_WIDGET}; color: {COLOR_DARK_TEXT}; }}
    """

    @classmethod
    def get_complete_stylesheet(cls) -> str:
        parts = [
            cls.MAIN_WINDOW_STYLE,
            cls.BUTTON_STYLE,
            cls.MENU_BUTTON_STYLE,
            cls.COMBOBOX_STYLE,
            cls.PROGRESSBAR_STYLE,
            cls.INPUT_STYLE,
            cls.TABLEWIDGET_STYLE,
            cls.HEADERVIEW_STYLE,
            cls.SCROLLBAR_STYLE,
            cls.CHECKBOX_STYLE,
            cls.JOB_CARD_STYLE,
            cls.PANEL_STYLE,
            cls.CHAT_STYLES,
            f"StatsCard {{ background-color: {COLOR_DARK_WIDGET}; color: {COLOR_CARD_TEXT_DARK}; border-radius: {BORDER_RADIUS}px; }}",
            f"StatsCard QLabel {{ color: {COLOR_CARD_TEXT_DARK}; background-color: {COLOR_DARK_WIDGET}; border: none; }}",
        ]
        return "\n".join(parts)


class LightTheme:
    """Light Theme Stylesheet Definition."""

    MAIN_WINDOW_STYLE = f"""
        QMainWindow {{ background-color: {COLOR_LIGHT_BG}; }}
        QWidget {{ 
            color: {COLOR_LIGHT_TEXT}; 
            background-color: {COLOR_LIGHT_BG}; 
            outline: none;
        }}
        QGroupBox {{ 
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG}; 
            border-radius: {BORDER_RADIUS}px; 
            margin-top: {GROUPBOX_TITLE_MARGIN_TOP}px; 
        }}
        QGroupBox::title {{ 
            subcontrol-origin: margin; 
            subcontrol-position: top left; 
            padding: {GROUP_TITLE_PADDING_Y}px {GROUP_TITLE_PADDING_X}px; 
            background-color: {COLOR_LIGHT_BG};
            color: {COLOR_LIGHT_MUTED};
        }}
        QToolTip {{
            background-color: {COLOR_LIGHT_WIDGET};
            color: {COLOR_LIGHT_TEXT};
            border: 1px solid {COLOR_LIGHT_BORDER};
        }}
    """

    BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {COLOR_LIGHT_WIDGET};
            color: {COLOR_LIGHT_TEXT};
            border: 1px solid {COLOR_LIGHT_BORDER};
            padding: {PADDING_MEDIUM}px {PADDING_SMALL * 2}px;
            border-radius: {BORDER_RADIUS}px;
            min-height: {BUTTON_MIN_HEIGHT}px;
            min-width: {BUTTON_MIN_WIDTH}px;
        }}
        QPushButton:hover {{ 
            background-color: {COLOR_LIGHT_ACCENT}; 
            color: {COLOR_LIGHT_BG}; 
            border-color: {COLOR_LIGHT_ACCENT}; 
        }}
        QPushButton:pressed {{ 
            background-color: {COLOR_LIGHT_BORDER_STRONG}; 
            color: {COLOR_LIGHT_TEXT};
        }}
        QPushButton:disabled {{ 
            color: {COLOR_LIGHT_MUTED}; 
            background-color: {COLOR_LIGHT_WIDGET}; 
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG}; 
        }}
    """

    PRIMARY_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {COLOR_LIGHT_SUCCESS};
            color: {COLOR_LIGHT_BG};
            border: none;
            padding: {PADDING_MEDIUM}px {PADDING_SMALL * 2}px;
            border-radius: {BORDER_RADIUS}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            min-height: {BUTTON_MIN_HEIGHT}px;
            min-width: {BUTTON_MIN_WIDTH}px;
        }}
        QPushButton:hover {{ background-color: {COLOR_LIGHT_SUCCESS_HOVER}; }}
        QPushButton:pressed {{ background-color: {COLOR_LIGHT_SUCCESS_DISABLED}; }}
        QPushButton:disabled {{ 
            background-color: {COLOR_LIGHT_SUCCESS_DISABLED}; 
            color: {COLOR_LIGHT_MUTED}; 
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG}; 
        }}
    """

    DANGER_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {COLOR_LIGHT_DANGER};
            color: {COLOR_LIGHT_BG};
            border: none;
            padding: {PADDING_MEDIUM}px {PADDING_SMALL * 2}px;
            border-radius: {BORDER_RADIUS}px;
            font-weight: {FONT_WEIGHT_SEMIBOLD};
            min-height: {BUTTON_MIN_HEIGHT}px;
            min-width: {BUTTON_MIN_WIDTH}px;
        }}
        QPushButton:hover {{ background-color: {COLOR_LIGHT_DANGER_HOVER}; }}
        QPushButton:pressed {{ background-color: {COLOR_LIGHT_DANGER_DISABLED}; }}
        QPushButton:disabled {{ 
            background-color: {COLOR_LIGHT_DANGER_DISABLED}; 
            color: {COLOR_LIGHT_MUTED}; 
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG}; 
        }}
    """

    MENU_BUTTON_STYLE = f"""
        QPushButton {{
            background-color: {COLOR_LIGHT_WIDGET};
            color: {COLOR_LIGHT_TEXT};
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG};
            padding: {MENU_BUTTON_PADDING_Y}px {MENU_BUTTON_PADDING_X}px;
            border-radius: {BORDER_RADIUS_LARGE}px;
            text-align: left;
            min-height: {BUTTON_MIN_HEIGHT}px;
        }}
        QPushButton:checked {{ 
            background-color: {COLOR_LIGHT_BORDER}; 
            border-color: {COLOR_LIGHT_BORDER_STRONG}; 
        }}
        QPushButton:hover {{ 
            background-color: {COLOR_LIGHT_ACCENT}; 
            color: {COLOR_LIGHT_BG}; 
            border-color: {COLOR_LIGHT_ACCENT}; 
        }}
    """

    COMBOBOX_STYLE = f"""
        QComboBox {{
            background-color: {COLOR_LIGHT_WIDGET};
            color: {COLOR_LIGHT_TEXT};
            border: 1px solid {COLOR_LIGHT_BORDER};
            padding: {COMBOBOX_PADDING}px;
            padding-left: {COMBOBOX_PADDING * 2}px;
            border-radius: {BORDER_RADIUS}px;
        }}
        QComboBox::drop-down {{ 
            border: none; 
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border: none;
            color: {COLOR_LIGHT_MUTED}; 
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLOR_LIGHT_WIDGET};
            color: {COLOR_LIGHT_TEXT};
            selection-background-color: {COLOR_LIGHT_BORDER};
            border: 1px solid {COLOR_LIGHT_BORDER};
            outline: none;
        }}
    """

    PROGRESSBAR_STYLE = f"""
        QProgressBar {{
            background-color: {COLOR_LIGHT_WIDGET};
            color: {COLOR_LIGHT_TEXT};
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG};
            border-radius: {BORDER_RADIUS}px;
            text-align: center;
            min-height: {PROGRESSBAR_HEIGHT}px;
        }}
        QProgressBar::chunk {{
            background-color: {COLOR_LIGHT_SUCCESS};
            border-radius: {BORDER_RADIUS_SMALL}px;
        }}
    """

    INPUT_STYLE = f"""
        QTextEdit, QPlainTextEdit, QLineEdit {{
            background-color: {COLOR_LIGHT_WIDGET};
            color: {COLOR_LIGHT_TEXT};
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG};
            border-radius: {BORDER_RADIUS}px;
            padding: {INPUT_PADDING_Y}px {INPUT_PADDING_X}px;
        }}
        QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {{
            border: 1px solid {COLOR_LIGHT_ACCENT};
        }}
    """

    TABLEWIDGET_STYLE = f"""
        QTableWidget {{
            background-color: {COLOR_LIGHT_WIDGET};
            color: {COLOR_LIGHT_TEXT};
            gridline-color: {COLOR_LIGHT_BORDER_STRONG};
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG};
            border-radius: {BORDER_RADIUS}px;
            selection-background-color: {COLOR_LIGHT_BORDER};
            selection-color: {COLOR_LIGHT_TEXT};
        }}
        QTableWidget::item {{
            padding: 4px;
        }}
    """

    HEADERVIEW_STYLE = f"""
        QHeaderView {{ background-color: {COLOR_LIGHT_WIDGET}; border: none; }}
        QHeaderView::section {{
            background-color: {COLOR_LIGHT_WIDGET};
            color: {COLOR_LIGHT_TEXT};
            padding: {PADDING_SMALL}px;
            border: none;
            border-bottom: 1px solid {COLOR_LIGHT_BORDER_STRONG};
            border-right: 1px solid {COLOR_LIGHT_BORDER_STRONG};
        }}
    """

    SCROLLBAR_STYLE = f"""
        QScrollBar:vertical {{
            background: {COLOR_LIGHT_WIDGET};
            width: {SCROLLBAR_WIDTH}px;
            margin: 0px;
        }}
        QScrollBar:horizontal {{
            background: {COLOR_LIGHT_WIDGET};
            height: {SCROLLBAR_WIDTH}px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {COLOR_LIGHT_BORDER_STRONG};
            min-height: 20px;
            border-radius: {SCROLLBAR_RADIUS}px;
            margin: 2px;
        }}
        QScrollBar::handle:horizontal {{
            background: {COLOR_LIGHT_BORDER_STRONG};
            min-width: 20px;
            border-radius: {SCROLLBAR_RADIUS}px;
            margin: 2px;
        }}
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{ 
            background: {COLOR_LIGHT_BORDER}; 
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            height: 0px;
            width: 0px;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}
    """

    CHECKBOX_STYLE = f"""
        QCheckBox {{ color: {COLOR_LIGHT_TEXT}; spacing: {PADDING_SMALL}px; }}
        QCheckBox::indicator {{
            width: 16px; 
            height: 16px;
            border-radius: {BORDER_RADIUS_SMALL}px;
            border: 1px solid {COLOR_LIGHT_BORDER};
            background-color: {COLOR_LIGHT_WIDGET};
        }}
        QCheckBox::indicator:checked {{
            background-color: {COLOR_LIGHT_ACCENT};
            border-color: {COLOR_LIGHT_ACCENT};
        }}
    """

    JOB_CARD_STYLE = f"""
        QFrame#JobCard {{
            background-color: {COLOR_LIGHT_WIDGET};
            border: 1px solid {COLOR_LIGHT_BORDER};
            border-radius: {BORDER_RADIUS}px;
        }}
        QFrame#JobCard:hover {{
            border: 1px solid {COLOR_LIGHT_ACCENT};
        }}
        QFrame#JobCard[selected="true"] {{
            background-color: #f0f9ff;
            border: 1px solid {COLOR_LIGHT_ACCENT};
            border-left: 4px solid {COLOR_LIGHT_ACCENT};
        }}
        QLabel#JobTitle {{ font-weight: {FONT_WEIGHT_SEMIBOLD}; font-size: 13px; color: {COLOR_LIGHT_TEXT}; background-color: {COLOR_LIGHT_WIDGET}; }}
        QLabel#JobCompany {{ font-size: 11px; color: {COLOR_LIGHT_MUTED}; background-color: {COLOR_LIGHT_WIDGET}; }}
        QLabel#JobMeta {{ font-size: 10px; color: {COLOR_LIGHT_MUTED}; background-color: {COLOR_LIGHT_WIDGET}; }}
        QCheckBox#JobCardCheckbox::indicator {{
            width: 16px; 
            height: 16px;
            border-radius: {BORDER_RADIUS_SMALL}px;
            border: 1px solid {COLOR_LIGHT_BORDER};
            background-color: {COLOR_LIGHT_WIDGET};
        }}
        QCheckBox#JobCardCheckbox::indicator:checked {{
            background-color: {COLOR_LIGHT_ACCENT};
            border-color: {COLOR_LIGHT_ACCENT};
        }}
    """

    PANEL_STYLE = f"""
        QFrame#ContentPanel {{
            background-color: {COLOR_LIGHT_WIDGET};
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG};
            border-radius: {BORDER_RADIUS}px;
        }}
    """

    # =========================================================================
    # ENHANCED: Chat Styles with Rich Text Elements (Light Theme)
    # =========================================================================
    CHAT_STYLES = f"""
        /* Base chat bubbles */
        QFrame#UserBubble {{
            background-color: {COLOR_LIGHT_ACCENT};
            border-radius: {BORDER_RADIUS}px;
            border-bottom-right-radius: 2px;
        }}
        
        QLabel#UserBubbleLabel {{ 
            color: {COLOR_LIGHT_BG}; 
            background-color: {COLOR_LIGHT_ACCENT};
            line-height: 1.6;
        }}
        
        QFrame#AssistantBubble {{
            background-color: {COLOR_LIGHT_WIDGET};
            border: 1px solid {COLOR_CHAT_ASSISTANT_BORDER_LIGHT};
            border-radius: {BORDER_RADIUS}px;
            border-bottom-left-radius: 2px;
        }}
        
        QLabel#AssistantBubbleLabel {{ 
            color: {COLOR_LIGHT_TEXT}; 
            background-color: {COLOR_LIGHT_WIDGET};
            line-height: 1.6;
        }}
        
        /* Rich text elements inside bubbles */
        QLabel#AssistantBubbleLabel h1,
        QLabel#AssistantBubbleLabel h2,
        QLabel#AssistantBubbleLabel h3 {{
            color: #1a1a1a;
            font-weight: 600;
            margin-top: 14px;
            margin-bottom: 6px;
            line-height: 1.3;
        }}
        
        QLabel#AssistantBubbleLabel h1 {{ font-size: 18px; }}
        QLabel#AssistantBubbleLabel h2 {{ font-size: 16px; }}
        QLabel#AssistantBubbleLabel h3 {{ font-size: 14px; }}
        
        QLabel#AssistantBubbleLabel strong {{
            font-weight: 700;
            color: #000000;
        }}
        
        QLabel#AssistantBubbleLabel em {{
            font-style: italic;
            color: #404040;
        }}
        
        QLabel#AssistantBubbleLabel ul,
        QLabel#AssistantBubbleLabel ol {{
            margin: 8px 0;
            padding-left: 20px;
        }}
        
        QLabel#AssistantBubbleLabel li {{
            margin: 4px 0;
            line-height: 1.5;
        }}
        
        QLabel#AssistantBubbleLabel code {{
            background-color: rgba(0, 0, 0, 0.06);
            color: #c7254e;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        QLabel#AssistantBubbleLabel pre {{
            background-color: rgba(0, 0, 0, 0.04);
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
            overflow-x: auto;
            border: 1px solid {COLOR_LIGHT_BORDER};
        }}
        
        QLabel#AssistantBubbleLabel pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        QLabel#AssistantBubbleLabel a {{
            color: {COLOR_LIGHT_ACCENT};
            text-decoration: none;
        }}
        
        QLabel#AssistantBubbleLabel a:hover {{
            text-decoration: underline;
        }}
        
        QLabel#AssistantBubbleLabel blockquote {{
            border-left: 3px solid #d0d0d0;
            padding-left: 12px;
            margin: 8px 0;
            font-style: italic;
            color: #707070;
        }}
        
        QLabel#AssistantBubbleLabel hr {{
            border: none;
            border-top: 1px solid #d0d0d0;
            margin: 14px 0;
        }}
        
        /* Input area */
        QTextEdit#ChatInput {{ 
            background-color: {COLOR_LIGHT_WIDGET}; 
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG}; 
            border-radius: {BORDER_RADIUS}px; 
        }}
        QTextEdit#ChatInput:focus {{ border: 1px solid {COLOR_LIGHT_ACCENT}; }}

        /* Context cards */
        QFrame#ContextCard {{
            border: 1px solid {COLOR_LIGHT_BORDER_STRONG};
            border-left: 4px solid {COLOR_LIGHT_ACCENT};
            border-radius: {BORDER_RADIUS}px;
            background-color: {COLOR_LIGHT_WIDGET};
            padding: {PADDING_SMALL}px;
        }}
        QLabel#ContextTitle {{ color: {COLOR_LIGHT_ACCENT}; font-weight: {FONT_WEIGHT_SEMIBOLD}; }}
        QLabel#ContextScore {{ color: {COLOR_LIGHT_MUTED}; font-size: 10px; background-color: {COLOR_LIGHT_WIDGET}; }}
        QFrame#ContextCard QLabel {{ background-color: {COLOR_LIGHT_WIDGET}; }}
        QLabel#ContextHeaderTitle {{ background-color: {COLOR_LIGHT_WIDGET}; color: {COLOR_LIGHT_TEXT}; }}
    """

    @classmethod
    def get_complete_stylesheet(cls) -> str:
        parts = [
            cls.MAIN_WINDOW_STYLE,
            cls.BUTTON_STYLE,
            cls.MENU_BUTTON_STYLE,
            cls.COMBOBOX_STYLE,
            cls.PROGRESSBAR_STYLE,
            cls.INPUT_STYLE,
            cls.TABLEWIDGET_STYLE,
            cls.HEADERVIEW_STYLE,
            cls.SCROLLBAR_STYLE,
            cls.CHECKBOX_STYLE,
            cls.JOB_CARD_STYLE,
            cls.PANEL_STYLE,
            cls.CHAT_STYLES,
            f"StatsCard {{ background-color: {COLOR_LIGHT_WIDGET}; color: {COLOR_CARD_TEXT_LIGHT}; border-radius: {BORDER_RADIUS}px; }}",
            f"StatsCard QLabel {{ color: {COLOR_CARD_TEXT_LIGHT}; background-color: {COLOR_LIGHT_WIDGET}; border: none; }}",
        ]
        return "\n".join(parts)
