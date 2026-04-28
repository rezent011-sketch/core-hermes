from pathlib import Path

from auto_skill_extractor.models import ExtractionResult, OrchestratorAction, OrchestratorDecision
from auto_skill_extractor.reporter import ReportWriter


def test_report_writer_creates_safe_summary_without_raw_json(tmp_path):
    result = ExtractionResult(
        total_messages=3932,
        patterns_found=29,
        skills_extracted=5,
        saved_files=["/tmp/skill.md"],
        orchestrator_decision=OrchestratorDecision(
            action=OrchestratorAction.IDLE,
            reason="No action",
            confidence=0.7,
            next_steps=["Review output"],
        ),
    )

    report = ReportWriter().write(result, tmp_path / "report.md")
    text = report.read_text(encoding="utf-8")

    assert report.exists()
    assert "3932" in text
    assert "5" in text
    assert "Review output" in text
    assert "saved_files" not in text
    assert "/tmp/skill.md" not in text
