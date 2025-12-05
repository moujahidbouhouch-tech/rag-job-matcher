from typing import Optional

from rag_project.rag_core.config import AppSettings, get_settings
from rag_project.rag_core.infra.db_pgvector import PgVectorRepository
from rag_project.rag_core.infra.embedding_bgem3 import BgeM3EmbeddingProvider
from rag_project.rag_core.infra.llm_ollama import OllamaLLMProvider
from rag_project.rag_core.retrieval.job_matching_service import JobMatchingService
from rag_project.rag_core.retrieval.router_service import RouterService
from rag_project.rag_core.retrieval.domain_extraction_service import DomainExtractionService
from rag_project.rag_core.ingestion.service import IngestionService
from rag_project.rag_core.retrieval.service import QueryService
from rag_project.logger import get_logger


logger = get_logger(__name__)


class RAGApp:
    def __init__(self, settings: Optional[AppSettings] = None) -> None:
        self.settings = settings or get_settings()
        logger.info(
            "Initializing RAGApp with db=%s:%s/%s use_structured_chunker=%s",
            self.settings.db_host,
            self.settings.db_port,
            self.settings.db_name,
            self.settings.use_structured_chunker,
        )
        self.repo = PgVectorRepository(self._dsn())
        self.embedder = BgeM3EmbeddingProvider(self.settings.embedding_model_id)
        self.llm = OllamaLLMProvider(
            base_url=str(self.settings.ollama_host),
            model=self.settings.ollama_model,
            fallback_model=self.settings.ollama_fallback_model,
            timeout=self.settings.ollama_timeout,
            num_ctx=self.settings.ollama_num_ctx
        )
        self.ingestion = IngestionService(
            document_repo=self.repo,
            chunk_repo=self.repo,
            embedder=self.embedder,
            max_tokens=self.settings.chunk_token_target,
            overlap_tokens=self.settings.chunk_overlap_tokens,
            use_structured_chunker=self.settings.use_structured_chunker,
            structured_min_chunk_words=self.settings.structured_min_chunk_words,
            structured_max_llm_input_words=self.settings.structured_max_llm_input_words,
            structured_use_llm=self.settings.structured_use_llm,
            chunk_assist_model_id=self.settings.chunk_assist_model_id,
            llm_provider=self.llm,
            chunk_profiles=self.settings.chunk_profiles,
        )
        self.query = QueryService(
            embedder=self.embedder,
            llm=self.llm,
            chunk_repo=self.repo,
        )
        self.router = RouterService(llm=self.llm)
        self.domain_extractor = DomainExtractionService(self.llm, self.embedder, self.repo)
        self.job_matching = JobMatchingService(
            embedder=self.embedder,
            llm=self.llm,
            chunk_repo=self.repo,
            domain_extractor=self.domain_extractor,
        )
        logger.info("RAGApp initialized successfully")

    def _dsn(self) -> str:
        password_part = f" password={self.settings.db_password}" if self.settings.db_password else ""
        return (
            f"host={self.settings.db_host} "
            f"port={self.settings.db_port} "
            f"dbname={self.settings.db_name} "
            f"user={self.settings.db_user}"
            f"{password_part}"
        )
