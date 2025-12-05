import re
from typing import List

from rag_project.config import (
    CHUNKER_DEFAULT_MAX_TOKENS,
    CHUNKER_DEFAULT_OVERLAP_TOKENS,
    SENTENCE_SPLIT_REGEX,
    CHUNK_OVERLAP_RATIO,
)
from rag_project.logger import get_logger


logger = get_logger(__name__)

def split_into_sentences(text: str) -> List[str]:
    """Basic sentence splitter that avoids cutting decimals."""
    # Split on ., ?, ! followed by space/newline and uppercase/start; negative lookbehind for digit.
    pattern = re.compile(SENTENCE_SPLIT_REGEX)
    sentences = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        sentences.extend([s.strip() for s in re.split(pattern, paragraph) if s.strip()])
    return sentences


def chunk_text(
    text: str,
    max_tokens: int = CHUNKER_DEFAULT_MAX_TOKENS,
    overlap_tokens: int = CHUNKER_DEFAULT_OVERLAP_TOKENS,
) -> List[str]:
    """
    Chunk text into roughly max_tokens units with ~{overlap_pct}% overlap.
    Token proxy is words; avoids splitting inside words and prioritizes sentence boundaries.
    """.format(
        overlap_pct=int(CHUNK_OVERLAP_RATIO * 100)
    )
    sentences = split_into_sentences(text)
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for sent in sentences:
        words = sent.split()
        sent_len = len(words)
        if current_len + sent_len <= max_tokens:
            current.append(sent)
            current_len += sent_len
        else:
            if current:
                chunks.append(" ".join(current))
            # start new chunk; include overlap from previous chunk
            if chunks and overlap_tokens > 0:
                last_words = chunks[-1].split()
                overlap_slice = last_words[-overlap_tokens:] if len(last_words) > overlap_tokens else last_words
                current = [" ".join(overlap_slice), sent]
                current_len = len(overlap_slice) + sent_len
            else:
                current = [sent]
                current_len = sent_len

    if current:
        chunks.append(" ".join(current))

    logger.debug("Chunked text into %d chunks (max_tokens=%d overlap_tokens=%d)", len(chunks), max_tokens, overlap_tokens)
    return chunks
