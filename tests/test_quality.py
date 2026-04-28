from datetime import datetime

from auto_skill_extractor.models import SkillDefinition, SkillType, SessionMessage
from auto_skill_extractor.quality import SkillQualityScorer, SkillDeduplicator, SkillValidator


def make_skill(name="debug-python", confidence=0.8, patterns=None, tags=None, description="Python debug helper"):
    return SkillDefinition(
        name=name,
        description=description,
        skill_type=SkillType.DEBUG,
        patterns=patterns or ["エラー修正", "Traceback"],
        example_conversation=[
            SessionMessage(id="1", role="user", content="Tracebackを修正して", timestamp=datetime.now(), session_id="s1"),
            SessionMessage(id="2", role="assistant", content="原因を確認します", timestamp=datetime.now(), session_id="s1"),
        ],
        confidence=confidence,
        tags=tags or ["python", "debug"],
    )


def test_quality_scorer_penalizes_empty_examples():
    good = make_skill()
    bad = make_skill(name="bad", patterns=[], tags=[], description="x")
    bad.example_conversation = []

    scorer = SkillQualityScorer()
    assert scorer.score(good) > scorer.score(bad)
    assert scorer.score(bad) < 0.5


def test_deduplicator_merges_similar_skills():
    a = make_skill(name="debug-python", tags=["python", "debug"], confidence=0.7)
    b = make_skill(name="debug-python-errors", tags=["python", "debug", "error"], confidence=0.9)

    merged = SkillDeduplicator().deduplicate([a, b])

    assert len(merged) == 1
    assert merged[0].confidence == 0.9
    assert "error" in merged[0].tags


def test_validator_accepts_valid_skill_and_rejects_invalid():
    valid = make_skill()
    invalid = make_skill(name="", patterns=[])
    invalid.description = ""

    validator = SkillValidator()
    assert validator.validate(valid).is_valid
    result = validator.validate(invalid)
    assert not result.is_valid
    assert result.errors
