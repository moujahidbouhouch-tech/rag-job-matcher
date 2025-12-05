"""Job Matching Worker

Background thread for running job matching analysis so the GUI stays responsive.
"""

from PyQt5.QtCore import QThread, pyqtSignal  # type: ignore

from rag_project.logger import get_logger

logger = get_logger(__name__)


class JobMatchingWorker(QThread):
    """
    Qt worker thread for job matching analysis.

    Signals:
        analysis_complete: emits JobMatchResult
        error_occurred: emits str
        progress_update: emits str
    """

    analysis_complete = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    requirements_ready = pyqtSignal(object)
    evaluation_ready = pyqtSignal(object, object)  # (requirement, evaluation)

    def __init__(self, job_matching_service, job_text: str):
        super().__init__()
        self.job_matching_service = job_matching_service
        self.job_text = job_text
        self._is_cancelled = False

    def run(self):
        try:
            self.progress_update.emit("🔍 Extracting requirements from job posting...")
            domain_mappings = self.job_matching_service.extract_domain_knowledge(self.job_text)  # type: ignore[attr-defined]
            requirements = self.job_matching_service._extract_requirements(self.job_text)  # type: ignore[attr-defined]

            if self._is_cancelled:
                logger.info("Job matching analysis cancelled by user")
                return

            self.requirements_ready.emit(requirements)

            if not requirements:
                self.analysis_complete.emit(
                    self.job_matching_service.analyze_match(self.job_text)
                )
                return

            evaluations = []
            for idx, req in enumerate(requirements, 1):
                if self._is_cancelled:
                    logger.info("Job matching analysis cancelled during evaluation")
                    return
                self.progress_update.emit(f"⚙️ Evaluating requirement {idx}/{len(requirements)}: {req.name}")
                evaluation = self.job_matching_service._evaluate_requirement(req, domain_mappings)  # type: ignore[attr-defined]
                evaluations.append(evaluation)
                self.evaluation_ready.emit(req, evaluation)

            match_count = sum(
                1 for e in evaluations if "MATCH" in e.verdict.upper() and "MISSING" not in e.verdict.upper()
            )
            missing_count = len(evaluations) - match_count
            match_rate = (match_count / len(evaluations) * 100) if evaluations else 0.0

            result = type("_Result", (), {})()
            result.job_text = self.job_text
            result.extracted_requirements = requirements
            result.evaluations = evaluations
            result.match_count = match_count
            result.missing_count = missing_count
            result.match_rate = match_rate

            self.progress_update.emit(
                f"✅ Analysis complete: {match_count}/{len(evaluations)} matches"
            )
            self.analysis_complete.emit(result)
        except Exception as exc:  # noqa: BLE001
            logger.error("Job matching analysis failed: %s", exc, exc_info=True)
            self.error_occurred.emit(f"Analysis failed: {exc}")

    def cancel(self):
        self._is_cancelled = True
        logger.info("Job matching analysis cancellation requested")
