from datetime import datetime

from auto_skill_extractor.models import SessionMessage, MemoryType
from auto_skill_extractor.smart_memory import SmartMemoryExtractor


def msg(content, role="assistant", id="1"):
    return SessionMessage(id=id, role=role, content=content, timestamp=datetime.now(), session_id="s1")


def test_smart_memory_rejects_task_completion_logs_and_questions():
    messages = [
        msg("## タスク完了 auto-skill-extractorの技術設計書を作成しました。ファイルサイズは20KBです。", id="1"),
        msg("あなたの今のバージョンはなんですか？ 最新のHermesですか？", role="user", id="2"),
        msg("ユーザーは再起動が必要な時は自分で実行せず、手順だけを教えてほしい", id="3"),
    ]

    candidates = SmartMemoryExtractor().extract(messages)

    assert len(candidates) == 1
    assert candidates[0].memory_type == MemoryType.USER_PREFERENCE
    assert "再起動" in candidates[0].content


def test_smart_memory_prefers_declarative_facts_not_assistant_promises():
    messages = [
        msg("次回から必ずこの形式でお届けします。何か画像を生成しますか？", id="1"),
        msg("開発環境のcore-hermes作業ディレクトリは ~/projects/core-hermes", id="2"),
    ]

    candidates = SmartMemoryExtractor().extract(messages)

    assert len(candidates) == 1
    assert candidates[0].memory_type == MemoryType.ENVIRONMENT
    assert "~/projects/core-hermes" in candidates[0].content
