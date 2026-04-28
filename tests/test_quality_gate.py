from auto_skill_extractor.quality_gate import QualityGate
from auto_skill_extractor.judge import JudgeDecision
from auto_skill_extractor.models import ExtractionResult


def result(errors=None, skills=5):
    return ExtractionResult(
        total_messages=100,
        patterns_found=5,
        skills_extracted=skills,
        saved_files=[],
        errors=errors or [],
        memory_candidates=[],
    )


def test_quality_gate_passes_clean_result_with_approved_judge():
    gate_result = QualityGate(min_judge_score=0.85).check(
        result(),
        JudgeDecision(approved=True, score=0.91, blockers=[], warnings=[]),
    )

    assert gate_result.passed
    assert gate_result.exit_code == 0


def test_quality_gate_fails_errors_or_rejected_judge():
    failed = QualityGate().check(
        result(errors=["safety audit failed"], skills=5),
        JudgeDecision(approved=False, score=0.5, blockers=["risk"], warnings=[]),
    )

    assert not failed.passed
    assert failed.exit_code == 2
    assert "safety audit failed" in " ".join(failed.reasons)
    assert "risk" in " ".join(failed.reasons)
