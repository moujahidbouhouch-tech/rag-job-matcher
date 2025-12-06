"""Model, embedding, ingestion, and retrieval configuration."""

from .env_config import (
    _env_first,
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASS,
    TEST_DB_NAME as ENV_TEST_DB_NAME,
)

# =============================================================================
# Model configurations
# =============================================================================


def _validate_model_selection(model_name: str, registry: dict):
    if model_name not in registry:
        available = ", ".join(registry.keys())
        raise ValueError(f"Unknown model '{model_name}'. Available: {available}")


LLM_MODEL_REGISTRY = {
    "qwen2.5:7b-instruct-q4_k_m": {
        "id": "qwen2.5:7b-instruct-q4_k_m",
        "timeout_seconds": 1200.0,
        "context_window": 128000,
        "max_output_tokens": 8192,
        "ollama_num_ctx": 128000,
    },
    "llama3.1:8b": {
        "id": "llama3.1:8b",
        "timeout_seconds": 300.0,
        "context_window": 128000,
        "max_output_tokens": 2048,
        "ollama_num_ctx": 16384,
    },
    "qwen2.5:1.5b-instruct": {
        "id": "qwen2.5:1.5b-instruct",
        "timeout_seconds": 120.0,
        "context_window": 32768,
        "max_output_tokens": 4096,
        "ollama_num_ctx": 128000,
    },
    "llama3.1:8b-instruct-q8_0": {
        "id": "llama3.1:8b-instruct-q8_0",
        "timeout_seconds": 300.0,
        "context_window": 128000,
        "max_output_tokens": 4096,
        "ollama_num_ctx": 128000,
    },
}

PRIMARY_LLM = _env_first(["PRIMARY_LLM", "OLLAMA_MODEL"], "qwen2.5:7b-instruct-q4_k_m")
FALLBACK_LLM = _env_first(["FALLBACK_LLM", "OLLAMA_FALLBACK_MODEL"], "llama3.1:8b")
CHUNK_ASSIST_MODEL = _env_first(["CHUNK_ASSIST_MODEL_ID"], "qwen2.5:1.5b-instruct")
CV_CHUNKER_MODEL = _env_first(["CV_CHUNKER_MODEL_ID"], PRIMARY_LLM)

_validate_model_selection(PRIMARY_LLM, LLM_MODEL_REGISTRY)
_validate_model_selection(FALLBACK_LLM, LLM_MODEL_REGISTRY)
_validate_model_selection(CHUNK_ASSIST_MODEL, LLM_MODEL_REGISTRY)
_validate_model_selection(CV_CHUNKER_MODEL, LLM_MODEL_REGISTRY)

EMBEDDING_MODEL_REGISTRY = {
    "BAAI/bge-m3": {
        "id": "BAAI/bge-m3",
        "dim": 1024,
        "max_sequence_length": 8192,
        "target_embedding_tokens": 512,
        "language_support": "multilingual (100+ languages)",
        "proximity_weight_default": 0.3,
    },
}

EMBEDDING_MODEL_ID = _env_first(["EMBEDDING_MODEL_ID"], "BAAI/bge-m3")
_validate_model_selection(EMBEDDING_MODEL_ID, EMBEDDING_MODEL_REGISTRY)
EMBEDDING_MODEL = EMBEDDING_MODEL_REGISTRY[EMBEDDING_MODEL_ID]

LLM_MODELS = {
    "llm_primary": LLM_MODEL_REGISTRY[PRIMARY_LLM],
    "llm_fallback": LLM_MODEL_REGISTRY[FALLBACK_LLM],
    "embedding": EMBEDDING_MODEL,
    "chunk_assist": LLM_MODEL_REGISTRY[CHUNK_ASSIST_MODEL],
    "cv_chunker": LLM_MODEL_REGISTRY[CV_CHUNKER_MODEL],
}

# Backward-compatible aliases
MODELS = LLM_MODELS

# Vector/pgvector settings
VECTOR_SETTINGS = {
    "table": "embeddings",
    "column": "embedding",
    "dimension": EMBEDDING_MODEL["dim"],
    "index": "idx_embeddings_embedding_cosine",
    "distance": "cosine",
}
VECTOR_CONFIG = VECTOR_SETTINGS

# Database defaults (test DB mirrors env_config defaults)
TEST_DB_HOST = DB_HOST
TEST_DB_PORT = DB_PORT
TEST_DB_USER = DB_USER
TEST_DB_PASSWORD = DB_PASS
TEST_DB_NAME = ENV_TEST_DB_NAME

# Vector search scoring weights
WEIGHT_SIMILARITY = 0.6
WEIGHT_MATCH_SCORE = 0.3
WEIGHT_RECENCY = 0.1
RECENCY_DECAY_DAYS = 30.0

# LLM/Ollama defaults derived from selected models
OLLAMA_DEFAULT_MODEL = PRIMARY_LLM
OLLAMA_DEFAULT_FALLBACK_MODEL = FALLBACK_LLM
OLLAMA_TIMEOUT_SECONDS = LLM_MODELS["llm_primary"]["timeout_seconds"]
OLLAMA_DEFAULT_NUM_CTX = LLM_MODELS["llm_primary"]["ollama_num_ctx"]

# Embedding settings
EMBEDDING_DIM = VECTOR_SETTINGS["dimension"]

# Chunk assist model
CHUNK_ASSIST_MODEL_ID = CHUNK_ASSIST_MODEL
CV_CHUNKER_MODEL_ID = CV_CHUNKER_MODEL
CV_CHUNKER_MAX_OUTPUT_TOKENS = LLM_MODELS["cv_chunker"]["max_output_tokens"]

# Chunking settings
CHUNKER_DEFAULT_MAX_TOKENS = EMBEDDING_MODEL["target_embedding_tokens"]
CHUNKER_DEFAULT_OVERLAP_TOKENS = int(CHUNKER_DEFAULT_MAX_TOKENS * 0.20)
CHUNK_TOKEN_TARGET = CHUNKER_DEFAULT_MAX_TOKENS
CHUNK_OVERLAP_TOKENS = CHUNKER_DEFAULT_OVERLAP_TOKENS
STRUCTURED_MIN_CHUNK_WORDS = 80
STRUCTURED_MAX_LLM_INPUT_WORDS = 1800
STRUCTURED_MAX_CHUNK_WORDS_HARD = 600
STRUCTURED_DEFAULT_PROXIMITY_WEIGHT = EMBEDDING_MODEL["proximity_weight_default"]
CHUNK_ASSIST_MAX_OUTPUT_TOKENS = LLM_MODELS["chunk_assist"]["max_output_tokens"]
STRUCTURED_MIN_CHUNK_RATIO = 0.4
STRUCTURED_MAX_CHUNK_RATIO = 1.25
CHUNK_OVERSIZE_THRESHOLD_MULTIPLIER = 1.2
CV_PROMPT_MAX_LINES = 400
CV_MIN_RESPONSE_TOKENS = 512
CV_HEADING_KEYWORDS = (
    "skills",
    "fähigkeiten",
    "kompetenzen",
    "profile",
    "profil",
    "summary",
    "berufserfahrung",
    "experience",
    "work experience",
    "projects",
    "projekte",
    "education",
    "studium",
    "ausbildung",
    "certifications",
    "zertifikat",
    "zertifikate",
    "interests",
    "interessen",
    "activities",
    "sprachen",
    "languages",
)
CV_DATE_REGEX = r"\d{2}\.\d{4}"
THESIS_SNIPPET_CHARS = 1000
METADATA_SNIPPET_CHARS = 6000

CHUNK_PROFILES = {
    "cv": {
        "target_words": 450,
        "overlap_words": 90,
        "proximity_weight": 0.0,
        "use_llm": False,
        "max_llm_input_words": STRUCTURED_MAX_LLM_INPUT_WORDS,
    },
    "job_posting": {
        "target_words": 450,
        "overlap_words": 90,
        "proximity_weight": 0.0,
        "use_llm": False,
        "max_llm_input_words": STRUCTURED_MAX_LLM_INPUT_WORDS,
    },
    "thesis": {
        "target_words": 500,
        "overlap_words": 100,
        "proximity_weight": 0.2,
        "use_llm": True,
        "max_llm_input_words": STRUCTURED_MAX_LLM_INPUT_WORDS,
    },
    "report": {
        "target_words": 500,
        "overlap_words": 100,
        "proximity_weight": 0.4,
        "use_llm": True,
        "max_llm_input_words": STRUCTURED_MAX_LLM_INPUT_WORDS,
    },
    "company": {
        "target_words": 450,
        "overlap_words": 90,
        "proximity_weight": 0.3,
        "use_llm": False,
        "max_llm_input_words": STRUCTURED_MAX_LLM_INPUT_WORDS,
    },
    "personal_project": {
        "target_words": 450,
        "overlap_words": 90,
        "proximity_weight": 0.3,
        "use_llm": False,
        "max_llm_input_words": STRUCTURED_MAX_LLM_INPUT_WORDS,
    },
    "cover_letter": {
        "target_words": 450,
        "overlap_words": 90,
        "proximity_weight": 0.3,
        "use_llm": False,
        "max_llm_input_words": STRUCTURED_MAX_LLM_INPUT_WORDS,
    },
    "default": {
        "target_words": CHUNKER_DEFAULT_MAX_TOKENS,
        "overlap_words": CHUNKER_DEFAULT_OVERLAP_TOKENS,
        "proximity_weight": 0.3,
        "use_llm": False,
        "max_llm_input_words": STRUCTURED_MAX_LLM_INPUT_WORDS,
    },
}

# Parsing / preprocessing toggles
PDF_PARSER = "pymupdf"
USE_PYMUPDF_FOR_PDF = True
GENERAL_FILTER_ENABLED = True
THESIS_FILTER_ENABLED = True
PARSER_TEXT_SUFFIXES = {".txt", ".md", ".html", ".htm"}
PARSER_PDF_SUFFIX = ".pdf"
PARSER_PDF_DEPENDENCY_MESSAGE = "PDF parsing requires pymupdf4llm to be installed"

CHUNK_OVERLAP_RATIO = 0.25

# Chunking strategy selection
CHUNK_STRATEGY = {
    "cv": "llm_cv_chunker",
    "default": "structured",
}
DEFAULT_CHUNK_STRATEGY = "structured"

# Debug logging (ingestion chunking)
INGEST_DEBUG_LOG_CHUNKS = False
INGEST_DEBUG_LOG_PATH = _env_first(
    ["INGEST_DEBUG_LOG_PATH"], "logs/ingest_chunk_debug.log"
)

# Retrieval/search defaults
DEFAULT_SEARCH_LIMIT = 5
DEFAULT_MIN_MATCH_SCORE = 0.0
DEFAULT_QUERY_TOP_K = 5
REPO_SEARCH_DEFAULT_LIMIT = DEFAULT_SEARCH_LIMIT
REPO_SEARCH_DEFAULT_MIN_MATCH = DEFAULT_MIN_MATCH_SCORE
REPO_SEARCH_DEFAULT_POSTED_AFTER = None
REPO_SEARCH_DEFAULT_DOC_TYPES = None
TEST_MIN_MATCH_THRESHOLD = 0.8
ANSWER_DEFAULT_TOP_K = 5

# Document types
SUPPORTED_DOC_TYPES = (
    "job_posting",
    "company",
    "cv",
    "cover_letter",
    "thesis",
    "personal_project",
)
(
    DOC_TYPE_JOB_POSTING,
    DOC_TYPE_COMPANY,
    DOC_TYPE_CV,
    DOC_TYPE_COVER_LETTER,
    DOC_TYPE_THESIS,
    DOC_TYPE_PERSONAL_PROJECT,
) = SUPPORTED_DOC_TYPES
DEFAULT_DOC_TYPE = DOC_TYPE_JOB_POSTING

for _dt in CHUNK_PROFILES:
    if _dt not in {"default", "report"}:
        assert _dt in SUPPORTED_DOC_TYPES, f"Chunk profile for unknown doc_type: {_dt}"

# LLM default generation settings
LLM_DEFAULT_MAX_TOKENS = LLM_MODELS["llm_primary"]["max_output_tokens"]
LLM_PROVIDER_DEFAULT_MAX_TOKENS = 256

# Health check settings
REQUIRED_LLM_MODELS = {
    LLM_MODELS["llm_primary"]["id"],
    LLM_MODELS["llm_fallback"]["id"],
}
REQUIRED_EMBEDDING_MODELS = {LLM_MODELS["embedding"]["id"]}
REQUIRED_TABLES = {
    "documents",
    "job_postings",
    "personal_documents",
    "company_info",
    "chunks",
    VECTOR_SETTINGS["table"],
}
REQUIRED_EXTENSIONS = {"vector"}
REQUIRED_INDEXES = {VECTOR_SETTINGS["index"]}
REQUIRED_FKS = {
    ("chunks", "chunks_document_id_fkey", "documents", "id", "CASCADE"),
    (
        VECTOR_SETTINGS["table"],
        f"{VECTOR_SETTINGS['table']}_chunk_id_fkey",
        "chunks",
        "id",
        "CASCADE",
    ),
}
REQUIRED_COLUMNS = {
    ("chunks", "id"),
    ("chunks", "document_id"),
    ("documents", "id"),
    ("documents", "doc_type"),
    (VECTOR_SETTINGS["table"], "chunk_id"),
    (VECTOR_SETTINGS["table"], VECTOR_SETTINGS["column"]),
}

# Chunk-assist overrides
CHUNK_ASSIST_MAX_TOKENS_OVERRIDE = 128

JOB_MATCHING_EXTRACTION_MODEL = _env_first(
    ["JOB_MATCHING_EXTRACTION_MODEL"],
    "llama3.1:8b-instruct-q8_0",
)
_validate_model_selection(JOB_MATCHING_EXTRACTION_MODEL, LLM_MODEL_REGISTRY)

JOB_MATCHING_EVALUATOR_MODEL = _env_first(
    ["JOB_MATCHING_EVALUATOR_MODEL"],
    "llama3.1:8b-instruct-q8_0",
)
_validate_model_selection(JOB_MATCHING_EVALUATOR_MODEL, LLM_MODEL_REGISTRY)
JOB_MATCHING_SEARCH_LIMIT = 5  # chunks per requirement
JOB_MATCHING_MIN_MATCH_SCORE = 0.0  # recall-first
JOB_MATCHING_EXTRACTION_MAX_TOKENS = 2000
JOB_MATCHING_EVALUATION_MAX_TOKENS = 256
JOB_MATCHING_JOB_TEXT_LIMIT = 6000  # characters for extraction prompt

# Ingestion progress stage percentages
PROGRESS_START_STAGE_PCT = 5
PROGRESS_START_DETAIL_PCT = 0
PROGRESS_CHUNK_STAGE_PCT = 35
PROGRESS_CHUNK_DETAIL_PCT = 50
PROGRESS_EMBED_STAGE_PCT = 60
PROGRESS_EMBED_DETAIL_PCT = 0
PROGRESS_EMBED_DONE_STAGE_PCT = 75
PROGRESS_EMBED_DONE_DETAIL_PCT = 100
PROGRESS_STORE_STAGE_PCT = 85
PROGRESS_STORE_DETAIL_PCT = 100
PROGRESS_DONE_STAGE_PCT = 100
PROGRESS_DONE_DETAIL_PCT = 100

__all__ = [
    "LLM_MODELS",
    "MODELS",
    "VECTOR_SETTINGS",
    "VECTOR_CONFIG",
    "TEST_DB_HOST",
    "TEST_DB_PORT",
    "TEST_DB_USER",
    "TEST_DB_PASSWORD",
    "TEST_DB_NAME",
    "TEST_DB_PORT",
    "TEST_DB_USER",
    "TEST_DB_PASSWORD",
    "WEIGHT_SIMILARITY",
    "WEIGHT_MATCH_SCORE",
    "WEIGHT_RECENCY",
    "RECENCY_DECAY_DAYS",
    "OLLAMA_DEFAULT_MODEL",
    "OLLAMA_DEFAULT_FALLBACK_MODEL",
    "OLLAMA_TIMEOUT_SECONDS",
    "OLLAMA_DEFAULT_NUM_CTX",
    "EMBEDDING_MODEL_ID",
    "EMBEDDING_DIM",
    "CHUNK_ASSIST_MODEL_ID",
    "CV_CHUNKER_MODEL_ID",
    "CV_CHUNKER_MAX_OUTPUT_TOKENS",
    "CHUNKER_DEFAULT_MAX_TOKENS",
    "CHUNKER_DEFAULT_OVERLAP_TOKENS",
    "CHUNK_TOKEN_TARGET",
    "CHUNK_OVERLAP_TOKENS",
    "STRUCTURED_MIN_CHUNK_WORDS",
    "STRUCTURED_MAX_LLM_INPUT_WORDS",
    "STRUCTURED_MAX_CHUNK_WORDS_HARD",
    "STRUCTURED_DEFAULT_PROXIMITY_WEIGHT",
    "CHUNK_ASSIST_MAX_OUTPUT_TOKENS",
    "STRUCTURED_MIN_CHUNK_RATIO",
    "STRUCTURED_MAX_CHUNK_RATIO",
    "CHUNK_OVERSIZE_THRESHOLD_MULTIPLIER",
    "CV_PROMPT_MAX_LINES",
    "CV_MIN_RESPONSE_TOKENS",
    "CV_HEADING_KEYWORDS",
    "CV_DATE_REGEX",
    "THESIS_SNIPPET_CHARS",
    "METADATA_SNIPPET_CHARS",
    "CHUNK_PROFILES",
    "PDF_PARSER",
    "USE_PYMUPDF_FOR_PDF",
    "GENERAL_FILTER_ENABLED",
    "THESIS_FILTER_ENABLED",
    "PARSER_TEXT_SUFFIXES",
    "PARSER_PDF_SUFFIX",
    "PARSER_PDF_DEPENDENCY_MESSAGE",
    "CHUNK_OVERLAP_RATIO",
    "CHUNK_STRATEGY",
    "DEFAULT_CHUNK_STRATEGY",
    "INGEST_DEBUG_LOG_CHUNKS",
    "INGEST_DEBUG_LOG_PATH",
    "DEFAULT_SEARCH_LIMIT",
    "DEFAULT_MIN_MATCH_SCORE",
    "DEFAULT_QUERY_TOP_K",
    "REPO_SEARCH_DEFAULT_LIMIT",
    "REPO_SEARCH_DEFAULT_MIN_MATCH",
    "REPO_SEARCH_DEFAULT_POSTED_AFTER",
    "REPO_SEARCH_DEFAULT_DOC_TYPES",
    "TEST_MIN_MATCH_THRESHOLD",
    "ANSWER_DEFAULT_TOP_K",
    "SUPPORTED_DOC_TYPES",
    "DOC_TYPE_JOB_POSTING",
    "DOC_TYPE_COMPANY",
    "DOC_TYPE_CV",
    "DOC_TYPE_COVER_LETTER",
    "DOC_TYPE_THESIS",
    "DOC_TYPE_PERSONAL_PROJECT",
    "DEFAULT_DOC_TYPE",
    "LLM_DEFAULT_MAX_TOKENS",
    "LLM_PROVIDER_DEFAULT_MAX_TOKENS",
    "REQUIRED_LLM_MODELS",
    "REQUIRED_EMBEDDING_MODELS",
    "REQUIRED_TABLES",
    "REQUIRED_EXTENSIONS",
    "REQUIRED_INDEXES",
    "REQUIRED_FKS",
    "REQUIRED_COLUMNS",
    "CHUNK_ASSIST_MAX_TOKENS_OVERRIDE",
    "JOB_MATCHING_EXTRACTION_MODEL",
    "JOB_MATCHING_EVALUATOR_MODEL",
    "JOB_MATCHING_SEARCH_LIMIT",
    "JOB_MATCHING_MIN_MATCH_SCORE",
    "JOB_MATCHING_EXTRACTION_MAX_TOKENS",
    "JOB_MATCHING_EVALUATION_MAX_TOKENS",
    "JOB_MATCHING_JOB_TEXT_LIMIT",
    "PROGRESS_START_STAGE_PCT",
    "PROGRESS_START_DETAIL_PCT",
    "PROGRESS_CHUNK_STAGE_PCT",
    "PROGRESS_CHUNK_DETAIL_PCT",
    "PROGRESS_EMBED_STAGE_PCT",
    "PROGRESS_EMBED_DETAIL_PCT",
    "PROGRESS_EMBED_DONE_STAGE_PCT",
    "PROGRESS_EMBED_DONE_DETAIL_PCT",
    "PROGRESS_STORE_STAGE_PCT",
    "PROGRESS_STORE_DETAIL_PCT",
    "PROGRESS_DONE_STAGE_PCT",
    "PROGRESS_DONE_DETAIL_PCT",
]
