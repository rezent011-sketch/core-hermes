from datetime import datetime

from auto_skill_extractor.memory_review import MemoryReviewWriter
from auto_skill_extractor.models import MemoryCandidate, MemoryType


def candidate(content="ユーザーは簡潔な日本語報告を好む", confidence=0.9):
    return MemoryCandidate(
        content=content,
        memory_type=MemoryType.USER_PREFERENCE,
        confidence=confidence,
        evidence_session_id="s1",
        source_message_id="m1",
        tags=["user_preference"],
    )


def test_memory_review_writer_outputs_checkbox_file_without_raw_ids(tmp_path):
    path = MemoryReviewWriter().write([candidate()], tmp_path / "memory_review.md")
    text = path.read_text(encoding="utf-8")

    assert "- [ ]" in text
    assert "ユーザーは簡潔な日本語報告を好む" in text
    assert "s1" not in text
    assert "m1" not in text


def test_memory_review_writer_sorts_by_confidence(tmp_path):
    low = candidate("ユーザーは低優先", 0.5)
    high = candidate("ユーザーは高優先", 0.95)

    path = MemoryReviewWriter().write([low, high], tmp_path / "memory_review.md")
    text = path.read_text(encoding="utf-8")

    assert text.index("ユーザーは高優先") < text.index("ユーザーは低優先")
