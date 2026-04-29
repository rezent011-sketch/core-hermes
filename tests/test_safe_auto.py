from datetime import datetime
from pathlib import Path

from auto_skill_extractor.models import SkillDefinition, SkillType, SessionMessage
from auto_skill_extractor.safe_auto import SafeAutoPolicy, SafeAutoDecision, SafeAutoRunner


def msg():
    return SessionMessage(id="m1", role="user", content="Tracebackを修正して", timestamp=datetime.now(), session_id="s1")


def skill(name="debug-python", confidence=0.95):
    return SkillDefinition(
        name=name,
        description="Python Traceback debugging workflow",
        skill_type=SkillType.DEBUG,
        patterns=["Traceback", "debug", "エラー修正"],
        example_conversation=[msg(), SessionMessage(id="m2", role="assistant", content="修正します", timestamp=datetime.now(), session_id="s1")],
        confidence=confidence,
        tags=["python", "debug"],
    )


def test_safe_auto_policy_auto_installs_only_high_score_zero_risk():
    decision = SafeAutoPolicy(auto_threshold=0.93).decide(skill(), judge_score=0.95, risk_score=0.0, safety_passed=True)

    assert decision.action == "auto_install"
    assert decision.reason == "passed safe-auto policy"


def test_safe_auto_policy_quarantines_medium_score_and_rejects_risk():
    policy = SafeAutoPolicy(auto_threshold=0.93, review_threshold=0.75)

    medium = policy.decide(skill(confidence=0.8), judge_score=0.82, risk_score=0.0, safety_passed=True)
    risky = policy.decide(skill(), judge_score=0.99, risk_score=0.2, safety_passed=True)

    assert medium.action == "review"
    assert risky.action == "reject"
    assert "risk" in risky.reason


def test_safe_auto_runner_writes_review_or_install(tmp_path):
    runner = SafeAutoRunner(
        output_dir=tmp_path / "out",
        hermes_home=tmp_path / "hermes",
        policy=SafeAutoPolicy(auto_threshold=0.93),
    )

    decisions = runner.run([skill()], judge_score=0.95)

    assert decisions[0].action == "auto_install"
    assert list((tmp_path / "hermes" / "skills" / "core-hermes").rglob("SKILL.md"))
    # タイムスタンプ付きマニフェストファイルを検索
    manifests = list((tmp_path / "out").glob("safe-auto-manifest-*.json"))
    assert len(manifests) == 1
