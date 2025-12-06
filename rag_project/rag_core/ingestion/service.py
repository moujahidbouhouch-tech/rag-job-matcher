import time
import json
import re
import os
from pathlib import Path
from typing import Callable, List, Optional
from uuid import UUID

from rag_project.rag_core.domain.models import (
    Chunk,
    Document,
    JobPosting,
    PersonalDocument,
    CompanyInfo,
)
from rag_project.rag_core.ingestion.chunker import chunk_text
from rag_project.rag_core.ingestion.structured_chunker import (
    ChunkConfig,
    chunk_structured,
    _clean_segment_text,
    _dedup_lines,
)
from rag_project.rag_core.ingestion.cv_chunker import chunk_cv
from rag_project.rag_core.ingestion.parser import parse_file, parse_job
from rag_project.rag_core.ports.embedding_port import EmbeddingProvider
from rag_project.rag_core.ports.repo_port import ChunkRepository, DocumentRepository
from rag_project.config import (
    CHUNK_ASSIST_MODEL_ID,
    CHUNK_ASSIST_MAX_TOKENS_OVERRIDE,
    PROGRESS_CHUNK_DETAIL_PCT,
    PROGRESS_CHUNK_STAGE_PCT,
    PROGRESS_DONE_DETAIL_PCT,
    PROGRESS_DONE_STAGE_PCT,
    PROGRESS_EMBED_DETAIL_PCT,
    PROGRESS_EMBED_DONE_DETAIL_PCT,
    PROGRESS_EMBED_DONE_STAGE_PCT,
    PROGRESS_EMBED_STAGE_PCT,
    PROGRESS_START_DETAIL_PCT,
    PROGRESS_START_STAGE_PCT,
    PROGRESS_STORE_DETAIL_PCT,
    PROGRESS_STORE_STAGE_PCT,
    STRUCTURED_MAX_LLM_INPUT_WORDS,
    STRUCTURED_MIN_CHUNK_WORDS,
    STRUCTURED_DEFAULT_PROXIMITY_WEIGHT,
    SUPPORTED_DOC_TYPES,
    DEFAULT_DOC_TYPE,
    DOC_TYPE_JOB_POSTING,
    DOC_TYPE_CV,
    DOC_TYPE_COVER_LETTER,
    DOC_TYPE_THESIS,
    DOC_TYPE_PERSONAL_PROJECT,
    DOC_TYPE_COMPANY,
    STRUCTURED_MIN_CHUNK_RATIO,
    STRUCTURED_MAX_CHUNK_RATIO,
    METADATA_EXTRACTION_PROMPT,
    CHUNK_STRATEGY,
    CV_CHUNKER_MODEL_ID,
    CV_CHUNKER_MAX_OUTPUT_TOKENS,
    INGEST_DEBUG_LOG_CHUNKS,
    INGEST_DEBUG_LOG_PATH,
    METADATA_SNIPPET_CHARS,
    MSG_METADATA_EXTRACTION,
    MSG_PARSE_PROGRESS,
    DEFAULT_CHUNK_STRATEGY,
    MSG_CV_CHUNK_STRATEGY,
    CV_CHUNK_DEBUG_FORMATS,
    MSG_STRUCTURED_STRATEGY,
    MSG_CHUNKING_COMPLETE,
    MSG_EMBEDDING_START,
    EMBED_PROGRESS_FORMULA,
    MSG_EMBEDDING_FINISHED,
    MSG_WRITE_STAGE,
    MSG_INGESTION_DONE,
)
from rag_project.logger import get_logger

logger = get_logger(__name__)


class IngestionService:
    def __init__(
        self,
        document_repo: DocumentRepository,
        chunk_repo: ChunkRepository,
        embedder: EmbeddingProvider,
        max_tokens: int,
        overlap_tokens: int,
        use_structured_chunker: bool = False,
        structured_min_chunk_words: int = STRUCTURED_MIN_CHUNK_WORDS,
        structured_max_llm_input_words: int = STRUCTURED_MAX_LLM_INPUT_WORDS,
        structured_use_llm: bool = False,
        chunk_assist_model_id: str = CHUNK_ASSIST_MODEL_ID,
        llm_provider=None,
        chunk_profiles: Optional[dict] = None,
    ) -> None:
        self.document_repo = document_repo
        self.chunk_repo = chunk_repo
        self.embedder = embedder
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.use_structured_chunker = use_structured_chunker
        self.structured_min_chunk_words = structured_min_chunk_words
        self.structured_max_llm_input_words = structured_max_llm_input_words
        self.structured_use_llm = structured_use_llm
        self.chunk_assist_model_id = chunk_assist_model_id
        self.llm_provider = llm_provider
        self.chunk_profiles = chunk_profiles or {}

    def _clean_json(self, text: str) -> str:
        """Helper to extract JSON from LLM response."""
        match = re.search(r"```(?:json)?\s*(.*)\s*```", text, re.DOTALL)
        if match:
            return match.group(1)
        return text.strip()

    def _extract_metadata_with_llm(self, text: str) -> dict:
        """
        Calls the LLM to extract metadata fields from the document text.
        Uses only the first 6000 characters to save context/time.
        """
        if not self.llm_provider:
            return {}

        # Limit context to first ~1000 words (header info usually at top)
        snippet = text[:METADATA_SNIPPET_CHARS]

        prompt = METADATA_EXTRACTION_PROMPT.format(text=snippet)

        try:
            # We use the primary LLM for this intelligence task
            # Assuming llm_provider has a generate method
            response = self.llm_provider.generate(prompt)
            cleaned_json = self._clean_json(response)
            data = json.loads(cleaned_json)

            # Filter out nulls so we don't overwrite existing non-null metadata
            # Also filter empty strings or "None" strings if the LLM hallucinates them
            return {
                k: v for k, v in data.items() if v not in [None, "null", "None", ""]
            }
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")
            return {}

    def ingest_job(
        self,
        title: str,
        body: str,
        metadata: Optional[dict] = None,
        progress_cb: Optional[Callable[[str, dict], None]] = None,
    ) -> UUID:
        text = parse_job(title, body, metadata)

        # For jobs, we might want extraction too if metadata is sparse
        self._emit(progress_cb, "extracting", {"message": MSG_METADATA_EXTRACTION})
        extracted_meta = self._extract_metadata_with_llm(text)

        final_metadata = extracted_meta.copy()
        if metadata:
            final_metadata.update(metadata)

        return self._ingest_text(text, final_metadata, progress_cb)

    def ingest_file(
        self,
        file_path: str,
        metadata: Optional[dict] = None,
        progress_cb: Optional[Callable[[str, dict], None]] = None,
    ) -> UUID:
        # 1. Parse
        text = parse_file(Path(file_path))

        # 2. LLM Extraction (The New Step)
        self._emit(progress_cb, "extracting", {"message": MSG_METADATA_EXTRACTION})
        extracted_meta = self._extract_metadata_with_llm(text)

        logger.info(f"LLM Extracted Metadata: {extracted_meta}")

        # 3. Merge Metadata (User input overrides LLM)
        final_metadata = extracted_meta.copy()
        if metadata:
            final_metadata.update(metadata)

        # 4. Ingest as normal
        return self._ingest_text(text, final_metadata, progress_cb)

    def _emit(
        self, progress_cb: Optional[Callable[[str, dict], None]], stage: str, info: dict
    ):
        if progress_cb:
            progress_cb(stage, info)

    def _ingest_text(
        self,
        text: str,
        metadata: Optional[dict],
        progress_cb: Optional[Callable[[str, dict], None]],
    ) -> UUID:
        t0 = time.time()
        word_count = len(text.split())
        doc_type = metadata.get("doc_type") if metadata else DEFAULT_DOC_TYPE
        if doc_type not in SUPPORTED_DOC_TYPES:
            raise ValueError(
                f"Unsupported doc_type '{doc_type}'. Supported: {SUPPORTED_DOC_TYPES}"
            )
        self._emit(
            progress_cb,
            "start",
            {
                "message": MSG_PARSE_PROGRESS.format(word_count=word_count),
                "stage_pct": PROGRESS_START_STAGE_PCT,
                "detail_pct": PROGRESS_START_DETAIL_PCT,
            },
        )
        document = Document(doc_type=doc_type, metadata=metadata)
        # Insert document + subtype
        self.document_repo.insert_document(document)
        if doc_type == DOC_TYPE_JOB_POSTING:
            jp = JobPosting(
                document_id=document.id,
                related_company_id=(
                    metadata.get("related_company_id") if metadata else None
                ),
                title=metadata.get("title") if metadata else None,
                location_text=(
                    metadata.get("location") or metadata.get("location_text")
                    if metadata
                    else None
                ),  # Check both keys
                salary_range=(
                    metadata.get("salary") or metadata.get("salary_range")
                    if metadata
                    else None
                ),
                url=metadata.get("url") if metadata else None,
                language=metadata.get("language") if metadata else None,
                posted_at=metadata.get("posted_at") if metadata else None,
                match_score=metadata.get("match_score") if metadata else None,
                company=metadata.get("company") if metadata else None,
            )
            self.document_repo.insert_job_posting(jp)
        elif doc_type in {
            DOC_TYPE_CV,
            DOC_TYPE_COVER_LETTER,
            DOC_TYPE_THESIS,
            DOC_TYPE_PERSONAL_PROJECT,
        }:
            pd = PersonalDocument(document_id=document.id, category=doc_type)
            self.document_repo.insert_personal_document(pd)
        elif doc_type == DOC_TYPE_COMPANY:
            ci = CompanyInfo(
                document_id=document.id,
                name=(
                    metadata.get("company") or metadata.get("name")
                    if metadata
                    else None
                ),
                industry=metadata.get("industry") if metadata else None,
            )
            self.document_repo.insert_company_info(ci)
        chunk_strategy = CHUNK_STRATEGY.get(
            doc_type, CHUNK_STRATEGY.get("default", DEFAULT_CHUNK_STRATEGY)
        )
        text_for_chunk = (
            text if doc_type == DOC_TYPE_CV else _dedup_lines(_clean_segment_text(text))
        )

        if chunk_strategy == "llm_cv_chunker":
            if self.llm_provider is None:
                raise ValueError("LLM provider is required for CV chunking.")
            self._emit(
                progress_cb,
                "chunk_strategy",
                {"message": MSG_CV_CHUNK_STRATEGY.format(model=CV_CHUNKER_MODEL_ID)},
            )

            def llm_call(prompt: str, max_tokens: int = CV_CHUNKER_MAX_OUTPUT_TOKENS):
                return self.llm_provider.generate(
                    prompt, model=CV_CHUNKER_MODEL_ID, max_tokens=max_tokens
                )

            chunks_text, cv_debug = chunk_cv(
                text_for_chunk, llm_generate=llm_call, debug=INGEST_DEBUG_LOG_CHUNKS
            )

            if INGEST_DEBUG_LOG_CHUNKS:
                try:
                    os.makedirs(os.path.dirname(INGEST_DEBUG_LOG_PATH), exist_ok=True)
                    with open(INGEST_DEBUG_LOG_PATH, "a", encoding="utf-8") as dbg:
                        dbg.write("\n")
                        dbg.write(
                            CV_CHUNK_DEBUG_FORMATS["header"].format(doc_id=document.id)
                        )
                        dbg.write(
                            CV_CHUNK_DEBUG_FORMATS["split_points"].format(
                                split_points=cv_debug.get("split_points")
                            )
                        )
                        dbg.write(
                            CV_CHUNK_DEBUG_FORMATS["num_chunks"].format(
                                num_chunks=cv_debug.get("num_chunks"),
                                num_lines=cv_debug.get("num_lines"),
                            )
                        )
                        dbg.write(
                            CV_CHUNK_DEBUG_FORMATS["prompt_truncated"].format(
                                prompt_truncated=cv_debug.get("prompt_truncated")
                            )
                        )
                        dbg.write(CV_CHUNK_DEBUG_FORMATS["prompt_label"])
                        dbg.write(cv_debug.get("prompt", "") + "\n---\n")
                        dbg.write(CV_CHUNK_DEBUG_FORMATS["response_label"])
                        dbg.write(cv_debug.get("llm_response", "") + "\n")
                except Exception as log_exc:  # noqa: BLE001
                    logger.warning("Failed to write CV chunk debug log: %s", log_exc)
        else:
            profile = self.chunk_profiles.get(
                doc_type, self.chunk_profiles.get("default", {})
            )
            target_words = profile.get("target_words", self.max_tokens)
            overlap_words = profile.get("overlap_words", self.overlap_tokens)
            proximity_weight = profile.get(
                "proximity_weight", STRUCTURED_DEFAULT_PROXIMITY_WEIGHT
            )
            use_llm_flag = profile.get("use_llm", self.structured_use_llm)
            max_llm_input = profile.get(
                "max_llm_input_words", self.structured_max_llm_input_words
            )
            cfg = ChunkConfig(
                max_chunk_words=target_words,
                overlap_words=overlap_words,
                min_chunk_words=max(
                    self.structured_min_chunk_words,
                    int(target_words * STRUCTURED_MIN_CHUNK_RATIO),
                ),
                max_chunk_words_hard=int(target_words * STRUCTURED_MAX_CHUNK_RATIO),
                use_llm=use_llm_flag,
                max_llm_input_words=max_llm_input,
                proximity_weight=proximity_weight,
            )
            self._emit(
                progress_cb,
                "chunk_strategy",
                {
                    "message": MSG_STRUCTURED_STRATEGY.format(
                        max_chunk=cfg.max_chunk_words,
                        overlap=cfg.overlap_words,
                        min_chunk=cfg.min_chunk_words,
                        llm_flag="on" if cfg.use_llm else "off",
                    )
                },
            )
            llm_call = None
            if cfg.use_llm and self.llm_provider is not None:
                llm_call = lambda prompt, max_tokens=CHUNK_ASSIST_MAX_TOKENS_OVERRIDE: self.llm_provider.generate(  # noqa: E731
                    prompt, model=self.chunk_assist_model_id, max_tokens=max_tokens
                )
            logger.info(
                "Structured chunking | doc_type=%s target=%s overlap=%s min=%s llm=%s",
                doc_type,
                cfg.max_chunk_words,
                cfg.overlap_words,
                cfg.min_chunk_words,
                cfg.use_llm,
            )
            chunks_text = chunk_structured(text_for_chunk, cfg, llm_generate=llm_call)
        self._emit(
            progress_cb,
            "chunk",
            {
                "message": MSG_CHUNKING_COMPLETE.format(count=len(chunks_text)),
                "stage_pct": PROGRESS_CHUNK_STAGE_PCT,
                "detail_pct": PROGRESS_CHUNK_DETAIL_PCT,
            },
        )
        logger.info(
            "Chunking complete: %s chunks (doc_type=%s)", len(chunks_text), doc_type
        )
        chunks: List[Chunk] = []
        for idx, ctext in enumerate(chunks_text):
            chunks.append(
                Chunk(
                    document_id=document.id,
                    chunk_index=idx,
                    content=ctext,
                    token_count=len(ctext.split()),
                )
            )

        self._emit(
            progress_cb,
            "embed",
            {
                "message": MSG_EMBEDDING_START.format(count=len(chunks)),
                "stage_pct": PROGRESS_EMBED_STAGE_PCT,
                "detail_pct": PROGRESS_EMBED_DETAIL_PCT,
            },
        )
        texts = [c.content for c in chunks]
        total_embeddings = len(texts)
        embeddings: List[List[float]] = []

        # Emit per-chunk progress during embedding
        for idx, text in enumerate(texts, start=1):
            if progress_cb:
                self._emit(
                    progress_cb,
                    "embed_progress",
                    {
                        "message": f"Embedding {idx}/{total_embeddings}",
                        "stage_pct": PROGRESS_EMBED_STAGE_PCT,
                        "detail_pct": int(idx / total_embeddings * 100),
                    },
                )
            emb = self.embedder.embed([text])[0]
            embeddings.append(emb)

        self._emit(
            progress_cb,
            "embed_done",
            {
                "message": MSG_EMBEDDING_FINISHED,
                "stage_pct": PROGRESS_EMBED_DONE_STAGE_PCT,
                "detail_pct": PROGRESS_EMBED_DONE_DETAIL_PCT,
            },
        )

        self._emit(
            progress_cb,
            "store",
            {
                "message": MSG_WRITE_STAGE,
                "stage_pct": PROGRESS_STORE_STAGE_PCT,
                "detail_pct": PROGRESS_STORE_DETAIL_PCT,
            },
        )
        self.chunk_repo.insert_chunks_with_embeddings(chunks, embeddings)
        total_time = time.time() - t0
        self._emit(
            progress_cb,
            "done",
            {
                "message": MSG_INGESTION_DONE.format(
                    time=total_time, count=len(chunks)
                ),
                "stage_pct": PROGRESS_DONE_STAGE_PCT,
                "detail_pct": PROGRESS_DONE_DETAIL_PCT,
            },
        )
        return document.id
