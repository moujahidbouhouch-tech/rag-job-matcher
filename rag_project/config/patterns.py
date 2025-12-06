"""Regex patterns, weights, and chunking heuristics."""

BOUNDARY_PATTERNS = {
    "markdown_header": r"^#{1,4}\s+\S",
    "bold_line": r"^\*\*(?!(?:Figure|Fig\.|Table|Tab\.|Tableau|Source|Quelle|Reference|Referenz|Référence|Abbildung|Abb\.|Bibliogra|Literatur))[^*]+\*\*\s*$",
    "all_caps": r"^[A-ZÄÖÜẞ\s]{4,}$",
    "colon_ended": r"^[^:]{3,60}:\s*$",
    "date_range": r"\d{2}[./]\d{2,4}\s*[-–]\s*(\d{2}[./]\d{2,4}|heute|present|current)",
    "bullet_start": r"^[\\-•●∙]\s+",
    "numbered": r"^\d+[.)]\s+",
    "blank_line": r"^\s*$",
}

BOUNDARY_WEIGHTS = {
    "markdown_header": 0.9,
    "bold_line": 0.8,
    "all_caps": 0.7,
    "colon_ended": 0.6,
    "date_range": 0.85,
    "bullet_start": 0.3,
    "numbered": 0.3,
    "blank_line": 0.4,
}

BOUNDARY_PRIORITIES = (1, 2, 3, 4, 5, 99)
# Backward-compatible aliases
CHUNK_BOUNDARY_PATTERNS = BOUNDARY_PATTERNS
BOUNDARY_PATTERN_WEIGHTS = BOUNDARY_WEIGHTS
BOUNDARY_PRIORITY_VALUES = BOUNDARY_PRIORITIES

SCRUB_TABLE_REGEX = r"^\s*\|.*$"
SCRUB_CAPTION_REGEX = (
    r"\*\*(?:Figure|Table|Abbildung|Tabelle|Source|Quelle)\s*\d+[\d\.]*.*?(?:\*\*|$)"
)
SCRUB_PAGE_REGEX = r"\b(Page \d+|Seite \d+)\b"
NOISE_PAGE_REGEX = r"^(page\s+)?\d+(\s+of\s+\d+)?$"
NOISE_DOTTED_TOC_REGEX = r"\.{4,}\s*\d*$"
NOISE_TABLE_REGEX = r"^[\s-]+\|[\s-]+\|?$"
NOISE_ARTIFACT_REGEX = r"^_.*_$"
NOISE_CAPTION_TOKENS = (
    "figure ",
    "fig.",
    "table ",
    "tab.",
    "source:",
    "abbildung",
    "abb.",
    "tabelle",
    "quelle:",
    "tableau",
    "image",
    "img",
    "diagram",
)
NOISE_REFERENCE_TOKENS = [
    "references",
    "bibliography",
    "works cited",
    "quellen",
    "literaturverzeichnis",
    "literatur",
    "références",
    "bibliographie",
    "anhang",
    "attachment",
    "list of figures",
    "list of tables",
    "contents",
    "inhaltsverzeichnis",
    "abbildungsverzeichnis",
    "sperrvermerk",
    "blocking notice",
    "declaration",
    "eidesstattliche erklärung",
]
NOISE_REFERENCE_REGEX = (
    r"^([A-Z0-9]+\.|[0-9]+\.)*\s*(" + "|".join(NOISE_REFERENCE_TOKENS) + r")"
)

BOUNDARY_BLANKLINE_BOOST = 0.2
BOUNDARY_CONFIDENCE_THRESHOLD = 0.5
PRIORITY_SPLIT_PATTERNS = {
    "section_header": r"\n(?=## \*\*)",
    "date_role_block": r"\n(?=\d{2}[./]\d{2,4}\s*[-–])",
    "paragraph_break": r"\n\s*\n",
    "sentence_end": r"(?<=[.!?])\s+(?=[A-ZÄÖÜ\-•])",
    "bullet_end": r"(?<=\S)\s*\n(?=\s*[-•]\s)",
}
SPLIT_WEIGHT_FORMULA = (
    "(1 - proximity_weight) * priority_score + proximity_weight * distance_score"
)
BOUNDARY_INCLUSIVE_OFFSET = 1
STRUCTURED_OVERSIZE_FACTOR = 1.2
MIN_SPLIT_RATIO = 0.5
FORCE_SPLIT_THRESHOLD_RULE = "len(chunk_words) > max_chunk_words_hard"
SENTENCE_SPLIT_REGEX = r"(?<!\d)(?<=[\.\?!])\s+(?=[A-Z0-9])"
CHUNK_OVERLAP_RATIO = 0.25

__all__ = [
    "BOUNDARY_PATTERNS",
    "BOUNDARY_WEIGHTS",
    "BOUNDARY_PRIORITIES",
    "CHUNK_BOUNDARY_PATTERNS",
    "BOUNDARY_PATTERN_WEIGHTS",
    "BOUNDARY_PRIORITY_VALUES",
    "SCRUB_TABLE_REGEX",
    "SCRUB_CAPTION_REGEX",
    "SCRUB_PAGE_REGEX",
    "NOISE_PAGE_REGEX",
    "NOISE_DOTTED_TOC_REGEX",
    "NOISE_TABLE_REGEX",
    "NOISE_ARTIFACT_REGEX",
    "NOISE_CAPTION_TOKENS",
    "NOISE_REFERENCE_TOKENS",
    "NOISE_REFERENCE_REGEX",
    "BOUNDARY_BLANKLINE_BOOST",
    "BOUNDARY_CONFIDENCE_THRESHOLD",
    "PRIORITY_SPLIT_PATTERNS",
    "SPLIT_WEIGHT_FORMULA",
    "BOUNDARY_INCLUSIVE_OFFSET",
    "STRUCTURED_OVERSIZE_FACTOR",
    "MIN_SPLIT_RATIO",
    "FORCE_SPLIT_THRESHOLD_RULE",
    "SENTENCE_SPLIT_REGEX",
    "CHUNK_OVERLAP_RATIO",
]
