from PyQt5 import QtCore  # type: ignore

from rag_project.rag_gui.workers.job_matching_worker import JobMatchingWorker
from rag_project.rag_core.domain.models import RequirementEvaluation, JobRequirement


class FakeReq(JobRequirement):
    def __init__(self, name):
        super().__init__(name=name, category="Hard Skill", search_query=name, inference_rule="rule")


class FakeEval(RequirementEvaluation):
    def __init__(self, req_name):
        super().__init__(
            requirement=FakeReq(req_name),
            verdict="✅ MATCH",
            reasoning="ok",
            retrieved_chunks_count=0,
            evidence_preview="",
            citations=[],
        )


class FakeService:
    def extract_domain_knowledge(self, job_text):
        return None

    def _extract_requirements(self, job_text):
        return [FakeReq("req1"), FakeReq("req2")]

    def _evaluate_requirement(self, req, domain_mappings=None):
        return FakeEval(req.name)

    def _extract_requirements(self, job_text):
        return [FakeReq("req1"), FakeReq("req2")]


def test_worker_signals_fire_in_order(qtbot):
    signals = []
    worker = JobMatchingWorker(FakeService(), "job")
    
    worker.requirements_ready.connect(lambda r: signals.append(("requirements", len(r))))
    worker.evaluation_ready.connect(lambda req, ev: signals.append(("evaluation", req.name)))
    worker.analysis_complete.connect(lambda r: signals.append(("complete", r.match_rate)))
    
    # Wait for signal AND process event queue
    with qtbot.waitSignal(worker.analysis_complete, timeout=5000):
        worker.start()
    
    # Force event loop processing
    qtbot.wait(100)  # Give slots time to execute
    
    # Now assert
    assert len(signals) > 0, f"No signals captured! signals={signals}"
    assert signals[0][0] == "requirements", f"Expected 'requirements' first, got {signals[0]}"
    assert signals[-1][0] == "complete", f"Expected 'complete' last, got {signals[-1]}"
        
    # Verify we got evaluations for both requirements
    evaluation_signals = [s for s in signals if s[0] == "evaluation"]
    assert len(evaluation_signals) == 2, f"Expected 2 evaluations, got {len(evaluation_signals)}"
