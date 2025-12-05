"""
LLM-assisted CV chunker: uses an LLM to identify semantic section boundaries
and splits the CV by line numbers. Mirrors the QA helper but configured via
constants.
"""

import json
import re
from typing import Callable, List, Tuple

from rag_project.logger import get_logger
from rag_project.config import (
    CV_CHUNKER_MODEL_ID,
    CV_CHUNKER_MAX_OUTPUT_TOKENS,
    CV_PROMPT_MAX_LINES,
    CV_CHUNKER_PROMPT_TEMPLATE,
    CV_MIN_RESPONSE_TOKENS,
    CV_HEADING_KEYWORDS,
    CV_DATE_REGEX,
)

logger = get_logger(__name__)


def _clean_json(text: str) -> str:
    """Extract JSON content from an LLM response."""
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return text.strip()


def _build_prompt(lines: List[str], max_lines: int = CV_PROMPT_MAX_LINES) -> tuple[str, bool]:
    """Build prompt asking the LLM to return end-line numbers for sections."""
    truncated = False
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        truncated = True
    numbered = "\n".join([f"{i}: {line}" for i, line in enumerate(lines)])
    prompt = CV_CHUNKER_PROMPT_TEMPLATE.format(max_line=len(lines) - 1, numbered=numbered)
    return prompt, truncated


def get_llm_splits(
    lines: List[str],
    llm_generate: Callable[[str, int], str],
) -> Tuple[List[int], str, str, bool]:
    """Call the LLM to get split points; return points + prompt/response for debug."""
    prompt, truncated = _build_prompt(lines)
    dynamic_max_tokens = min(CV_CHUNKER_MAX_OUTPUT_TOKENS, max(CV_MIN_RESPONSE_TOKENS, len(lines) * 4))
    try:
        raw_response = llm_generate(prompt, max_tokens=dynamic_max_tokens)
        cleaned = _clean_json(raw_response)
        data = json.loads(cleaned)
        split_points = data.get("split_after_lines", [])
        valid: List[int] = []
        for pt in split_points:
            if isinstance(pt, int) and 0 <= pt < len(lines):
                valid.append(pt)
        return sorted(set(valid)), prompt, raw_response, truncated
    except json.JSONDecodeError as exc:  # noqa: BLE001
        logger.warning("CV chunker JSON parse error: %s", exc)
        return [], prompt, raw_response if 'raw_response' in locals() else "NO RESPONSE", truncated
    except Exception as exc:  # noqa: BLE001
        logger.warning("CV chunker LLM error: %s", exc)
        return [], prompt, str(exc), truncated


def _adjust_split_points(lines: List[str], split_points: List[int]) -> List[int]:
    """Ensure monotonic points and avoid cutting inside bullet blocks."""
    cleaned: List[int] = []
    last = -1
    for pt in sorted(set(split_points)):
        if pt <= last or pt >= len(lines):
            continue
        if pt > 0 and lines[pt].lstrip().startswith("•") and lines[pt - 1].lstrip().startswith("•"):
            back = pt - 1
            while back > 0 and lines[back].lstrip().startswith("•"):
                back -= 1
            if back <= last:
                continue
            pt = back
        cleaned.append(pt)
        last = pt
    return cleaned


def _heuristic_split_points(lines: List[str]) -> List[int]:
    """Fallback deterministic split points based on headings/date hints."""
    headings = CV_HEADING_KEYWORDS
    date_pat = re.compile(CV_DATE_REGEX)
    splits: List[int] = []
    start = 0
    for i, line in enumerate(lines):
        if i == 0:
            continue
        low = line.lower()
        is_heading = any(low.startswith(h) for h in headings)
        is_date = bool(date_pat.search(line))
        if is_heading or is_date:
            if i - 1 >= start:
                splits.append(i - 1)
                start = i
    if lines and splits and splits[-1] != len(lines) - 1:
        splits.append(len(lines) - 1)
    elif lines and not splits:
        splits.append(len(lines) - 1)
    return splits


def split_at_points(lines: List[str], split_points: List[int]) -> List[str]:
    """Split the lines into chunks at the provided split points."""
    if not split_points:
        return ["\n".join(lines).strip()]
    chunks = []
    start = 0
    for end in split_points:
        chunk_lines = lines[start : end + 1]
        chunk_text = "\n".join(chunk_lines).strip()
        if chunk_text:
            chunks.append(chunk_text)
        start = end + 1
    if start < len(lines):
        tail = "\n".join(lines[start:]).strip()
        if tail:
            chunks.append(tail)
    return chunks


def chunk_cv(
    text: str,
    llm_generate: Callable[[str, int], str],
    debug: bool = False,
):
    """Chunk CV text using an LLM-generated set of split points."""
    lines = text.split("\n")
    split_points, prompt, raw_response, truncated = get_llm_splits(lines, llm_generate)
    split_points = _adjust_split_points(lines, split_points)
    if not split_points:
        split_points = _heuristic_split_points(lines)
    chunks = split_at_points(lines, split_points)
    chunks = [c for c in chunks if c.strip()]
    debug_info = {
        "prompt": prompt,
        "llm_response": raw_response,
        "prompt_truncated": truncated,
        "split_points": split_points,
        "num_lines": len(lines),
        "num_chunks": len(chunks),
        "model": CV_CHUNKER_MODEL_ID,
    }
    return (chunks, debug_info) if debug else (chunks, {})
