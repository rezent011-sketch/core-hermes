from datetime import datetime

from auto_skill_extractor.judge import HeuristicJudge, JudgeDecision
from auto_skill_extractor.models import MemoryCandidate, MemoryType, SkillDefinition, SkillType, SessionMessage


def msg(content="Tracebackを修正して"):
    return SessionMessage(id="m1", role="user", content=content, timestamp=datetime.now(), session_id="s1")


def skill(name="debug-python", description="Python Traceback debugging workflow"):
    return SkillDefinition(
        name=name,
        description=description,
        skill_type=SkillType.DEBUG,
        patterns=["Traceback", "エラー修正", "debug"],
        example_conversation=[msg(), SessionMessage(id="m2", role="assistant", content="原因を修正します", timestamp=datetime.now(), session_id="s1")],
        confidence=0.9,
        tags=["python", "debug"],
    )


def memory(content="ユーザーは簡潔な日本語報告を好む"):
    return MemoryCandidate(
        content=content,
        memory_type=MemoryType.USER_PREFERENCE,
        confidence=0.9,
        evidence_session_id="s1",
        source_message_id="m1",
    )


def test_heuristic_judge_approves_high_quality_skill_and_memory():
    decision = HeuristicJudge().evaluate(skills=[skill()], memories=[memory()])

    assert decision.approved
    assert decision.score >= 0.85
    assert decision.blockers == []


def test_heuristic_judge_blocks_secret_leak():
    decision = HeuristicJudge().evaluate(skills=[skill(description="token=abc1234567890")], memories=[])

    assert not decision.approved
    assert decision.score < 0.85
    assert any("risk" in b for b in decision.blockers)


def test_heuristic_judge_blocks_low_signal_memory():
    decision = HeuristicJudge().evaluate(skills=[], memories=[memory("お願いします")])

    assert not decision.approved
    assert any("memory" in b for b in decision.blockers)
