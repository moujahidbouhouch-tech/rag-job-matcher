from PyQt5 import QtCore, QtWidgets, QtGui

from rag_project.rag_gui.config import (
    PADDING_MEDIUM,
    GUI_JOB_CARD_CHECKBOX_STYLE,
    GUI_JOB_TITLE_FALLBACK,
    GUI_JOB_COMPANY_FALLBACK,
    GUI_JOB_LOCATION_FALLBACK,
)

class JobCard(QtWidgets.QFrame):
    """A card widget representing a Job Posting with a checkbox."""
    
    selection_changed = QtCore.pyqtSignal(str, bool)

    def __init__(self, job_data: dict, parent=None):
        super().__init__(parent)
        self.job_data = job_data
        self.job_id = job_data.get("id")
        self.setObjectName("JobCard")
        self._build_ui()

    def _build_ui(self):
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(PADDING_MEDIUM, PADDING_MEDIUM, PADDING_MEDIUM, PADDING_MEDIUM)
        layout.setSpacing(PADDING_MEDIUM)

        # 1. Checkbox (Top aligned for long text)
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setObjectName("JobCardCheckbox")
        if GUI_JOB_CARD_CHECKBOX_STYLE:
            self.checkbox.setStyleSheet(GUI_JOB_CARD_CHECKBOX_STYLE)
        self.checkbox.stateChanged.connect(self._on_toggle)
        layout.addWidget(self.checkbox, alignment=QtCore.Qt.AlignTop)

        # 2. Info Area
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(2)
        
        # FIX: Enable Word Wrap so long titles don't trigger scrollbars
        title = QtWidgets.QLabel(self.job_data.get("title", GUI_JOB_TITLE_FALLBACK))
        title.setObjectName("JobTitle")
        title.setWordWrap(True)  # <--- Added
        
        company = QtWidgets.QLabel(self.job_data.get("company", GUI_JOB_COMPANY_FALLBACK))
        company.setObjectName("JobCompany")
        company.setWordWrap(True) # <--- Added
        
        loc = self.job_data.get("location", GUI_JOB_LOCATION_FALLBACK)
        date = self.job_data.get("date", "")
        meta_text = f"{loc} • {date}" if loc else date
        meta = QtWidgets.QLabel(meta_text)
        meta.setObjectName("JobMeta")
        meta.setWordWrap(True)    # <--- Added

        info_layout.addWidget(title)
        info_layout.addWidget(company)
        info_layout.addWidget(meta)
        
        # Give the text area the ability to expand vertically
        layout.addLayout(info_layout, stretch=1)

    def _on_toggle(self, state):
        is_checked = (state == QtCore.Qt.Checked)
        self.setProperty("selected", is_checked)
        self.style().unpolish(self)
        self.style().polish(self)
        self.selection_changed.emit(self.job_id, is_checked)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()
