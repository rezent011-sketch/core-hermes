from datetime import datetime

from auto_skill_extractor.context_enhancer import ContextEnhancer
from auto_skill_extractor.models import ExtractionResult, MemoryType, OrchestratorAction, SessionMessage
from auto_skill_extractor.orchestrator import CoreHermesOrchestrator
from auto_skill_extractor.smart_memory import SmartMemoryExtractor


def msg(content, role="user", id="1"):
    return SessionMessage(id=id, role=role, content=content, timestamp=datetime.now(), session_id="s1")


def test_smart_memory_extracts_durable_preferences_and_sanitizes():
    messages = [
        msg("こんにちは"),
        msg("ユーザーは日本語で簡潔な報告を好む。APIキー sk-abcdefghijklmnopqrstuvwxyz は保存しない"),
        msg("Mac mini環境は /Users/apple/projects を使う", id="3"),
    ]

    candidates = SmartMemoryExtractor().extract(messages)

    assert len(candidates) >= 2
    assert candidates[0].confidence >= candidates[-1].confidence
    assert any(c.memory_type == MemoryType.USER_PREFERENCE for c in candidates)
    assert all("sk-abcdefghijklmnopqrstuvwxyz" not in c.content for c in candidates)


def test_context_enhancer_ranks_relevant_memory():
    memories = SmartMemoryExtractor().extract([
        msg("core-hermesプロジェクトはGitHub公開済みでレビュー前提", id="1"),
        msg("音楽生成は後回し", id="2"),
    ])

    enhancement = ContextEnhancer().enhance("core-hermes GitHub review", memories)

    assert "core-hermes" in enhancement.summary.lower()
    assert enhancement.relevant_memories


def test_orchestrator_requests_memory_review_before_automation():
    memories = SmartMemoryExtractor().extract([msg("ユーザーは簡潔な日本語報告を好む")])
    result = ExtractionResult(
        total_messages=1,
        patterns_found=0,
        skills_extracted=0,
        saved_files=[],
        memory_candidates=memories,
    )

    decision = CoreHermesOrchestrator().decide(result)

    assert decision.action == OrchestratorAction.REVIEW_MEMORIES
    assert decision.next_steps
