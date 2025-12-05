"""User-facing labels, placeholders, warnings, and messages."""

DEFAULT_THEME = "light"
GUI_WINDOW_TITLE = "RAG Ingestion & Retrieval"
GUI_THEME_DARK = "dark"
GUI_THEME_LIGHT = "light"
GUI_SIDEBAR_LABELS = {
    "ingestion": "Ingest & Index",
    "rag": "Ask (Retrieve)",
    "database": "DB Status",
    "delete": "Delete Data",
    "toggle": "Toggle theme",
}
GUI_INGEST_TITLE = "Ingest documents"
GUI_DB_STATUS_INITIAL = "Checking database connection..."
GUI_GROUP_SELECT_DOCS = "1. Select Documents"
GUI_NO_FILES_PLACEHOLDER = "No files selected"
GUI_FILE_BUTTON_LABELS = {"browse": "Browse files", "clear": "Clear List"}
GUI_DOC_TYPE_PLACEHOLDER = "Select type..."
GUI_INGEST_BUTTON_LABELS = {"start": "Start Ingestion", "stop": "Stop"}
GUI_PROGRESS_LABEL = "Progress"
GUI_DETAIL_STATUS_DEFAULT = "Current step: Ready"
GUI_DETAIL_STATUS_COLOR_DEFAULT = "color: gray;"
GUI_LOG_HEADER_TEXT = "Process Log"
GUI_FILE_DIALOG_FILTERS = "All Supported (*.pdf *.docx *.txt *.md);;PDF (*.pdf);;Word (*.docx);;Text (*.txt)"
GUI_DOC_TYPE_WARNING_TEXT = {"title": "Missing Info", "message": "Please select a Document Type."}
GUI_START_LOG_TEMPLATE = "Starting ingestion (DB connected)... Type: {doc_type}"
GUI_STOP_STATUS_TEXT = {"stopping": "Stopping...", "stopped": "Stopped"}
GUI_ABORT_MESSAGE = "Ingestion stopped by user."
GUI_LOG_CLEAR_BEHAVIOR = "clear_without_confirm"
GUI_STAGE_PARSE_MATCH = "Parsing input"
GUI_STAGE_CHUNK_MATCH = "Chunking complete"
GUI_CHUNK_COUNT_REGEX = r"Chunking complete: (\d+) chunks"
GUI_STAGE_EMBED_DONE_MATCH = "Embedding finished"
GUI_STAGE_WRITE_MATCH = "Writing to database"
GUI_INGEST_DONE_TEXT = "All Done"
GUI_ABORT_LOG_TEXT = "Process aborted by user."
GUI_JOB_FALLBACK_LABELS = {
    "title": "Untitled Position",
    "company": "Unknown Company",
    "location": "Remote/Unknown",
}
GUI_CHAT_FAKE_ANSWER = (
    "This is a <b>simulated response</b> because the backend is not connected yet.<br><br>"
    "I see you asked about: <i>{question}</i><br>"
    "I found relevant info in your selected documents <a href='1'>[1]</a>."
)
GUI_CHAT_FAKE_SOURCES = [
    {
        "content": "Required skills: Python, PyQt5, and PostgreSQL. Must have experience with vector databases.",
        "score": 0.92,
        "metadata": {"title": "job_description_v2.pdf"},
    },
    {
        "content": "The candidate should be comfortable working in an AsyncIO environment.",
        "score": 0.85,
        "metadata": {"title": "notes.txt"},
    },
]
GUI_RAG_HEADER_TEXT = "Chat with RAG (current DB)"
GUI_RAG_JOBLIST_LABEL = "Select job postings"
GUI_CONTEXT_TOGGLE_LABEL = "Show/Hide Context"
GUI_CHAT_PLACEHOLDER = "Ask a question about the selected job(s)..."
GUI_SEND_BUTTON_LABEL = "Send"
GUI_RAG_SELECTION_WARNINGS = {"title": "No Jobs Selected", "message": "Please select at least one job posting."}
GUI_RAG_EMPTY_QUESTION_MESSAGE = {"title": "Empty Question", "message": "Please enter a question."}
GUI_DBVIEW_TITLE = "Database Overview (current DB)"
GUI_REFRESH_LABEL = "Refresh"
GUI_DB_STATUS_CHECKING = "Checking database connection..."
GUI_DB_ERROR_PREFIX = "Error: "
GUI_DELETE_TITLE = "Delete Documents"
GUI_DELETE_LOAD_LABEL = "Load"
GUI_DELETE_BUTTON_LABEL = "Delete Selected"
GUI_DELETE_SELECTION_WARNING = {"title": "No Selection", "message": "Please select at least one document."}
GUI_DELETE_CONFIRM_TEXT = {"title": "Confirm Delete", "template": "Delete {count} document(s)?"}
GUI_DELETE_FAIL_TITLE = "Deletion Failed"
GUI_CHATAREA_PLACEHOLDER = "Type your message here..."
GUI_CONTEXT_HEADER_TEXT = "Context"
GUI_CONTEXT_EMPTY_TEXT = "No context available"
GUI_CHAT_USER_STYLE_FLAG = True
GUI_JOB_CARD_CHECKBOX_STYLE = ""
GUI_JOB_TITLE_FALLBACK = "Untitled Job"
GUI_JOB_COMPANY_FALLBACK = "Unknown Company"
GUI_JOB_LOCATION_FALLBACK = "Unknown Location"
GUI_CONTEXT_SCORE_FORMAT = "Score: {score:.2f}"
GUI_CONTEXT_TITLE_FALLBACK = "Source"
GUI_DROPZONE_TEXT = "Drag & drop files here\nor click to browse"
GUI_DROPZONE_FILE_FILTER = "All Files (*)"
GUI_DB_TABLE_HEADERS = ["Doc Type", "Count", "Chunks"]
GUI_DELETE_TABLE_HEADERS = ["", "ID", "Type", "Created", "Title/Company"]
DELETE_TABLE_HEADERS = GUI_DELETE_TABLE_HEADERS  # backward-compatible alias
GUI_LOADING_JOBS_TEXT = "Loading jobs..."
GUI_NO_JOBS_TEXT = "No job postings found."
GUI_JOB_LOAD_ERROR_PREFIX = "Error: "
GUI_NO_CONTEXT_TEXT = "No specific context found."

# Job Matching View Strings
JOB_MATCHING_NO_JOB_SELECTED = "❌ Please select a job posting first to analyze your match."
JOB_MATCHING_LOAD_FAILED = "❌ Could not load job posting text."
JOB_MATCHING_ANALYZING = "🤔 Analyzing your match against this job posting..."
JOB_MATCHING_RESULT_HEADER = "## 📊 Match Analysis Results\n"
JOB_MATCHING_MATCH_RATE = "**Overall Match Rate:** {rate:.1f}%"
JOB_MATCHING_MATCHED_COUNT = "**Matched:** {match}/{total} requirements\n"
JOB_MATCHING_MATCHED_HEADER = "### ✅ Matched Requirements\n"
JOB_MATCHING_MISSING_HEADER = "### ❌ Missing/Partial Requirements\n"
JOB_MATCHING_REQUIREMENTS_HEADER = "### 📋 Extracted Requirements\n"
JOB_MATCHING_REQUIREMENT_ITEM = "- {name} ({category}) — {query}"

__all__ = [name for name in globals() if name.isupper()]
