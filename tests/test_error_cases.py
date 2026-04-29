"""エラーケースのテスト"""
import sqlite3
import tempfile
from pathlib import Path

import pytest
from auto_skill_extractor.session_reader import SessionReader
from auto_skill_extractor.skill_generator import SkillGenerator
from auto_skill_extractor.models import SkillDefinition, SkillType, SessionMessage
from datetime import datetime


def msg(content, role="user", id="1"):
    return SessionMessage(id=id, role=role, content=content, timestamp=datetime.now(), session_id="s1")


def test_session_reader_missing_db():
    reader = SessionReader(Path("/nonexistent/path.db"))
    with pytest.raises(FileNotFoundError):
        reader.connect()


def test_session_reader_empty_db(tmp_path):
    db = tmp_path / "empty.db"
    conn = sqlite3.connect(str(db))
    conn.execute("CREATE TABLE IF NOT EXISTS sessions (id TEXT, title TEXT, started_at REAL, ended_at REAL, message_count INTEGER)")
    conn.execute("CREATE TABLE IF NOT EXISTS messages (id TEXT, session_id TEXT, role TEXT, content TEXT, timestamp REAL, tool_calls TEXT)")
    conn.commit()
    conn.close()

    reader = SessionReader(db)
    with reader:
        sessions = reader.get_recent_sessions()
        assert sessions == []

def test_session_reader_corrupt_db(tmp_path):
    """壊れた DB ファイルのテスト"""
    db = tmp_path / "corrupt.db"
    db.write_text("this is not a database")

    reader = SessionReader(db)
    reader.connect()  # connect 自体は成功する（遅延評価）
    # 実際のクエリ実行時にエラーになる
    with pytest.raises(sqlite3.DatabaseError):
        reader.get_recent_sessions()


def test_skill_generator_permission_error(tmp_path, monkeypatch):
    """書き込み権限がない場合のエラーハンドリング"""
    skill = SkillDefinition(
        name="test-skill",
        description="Test skill for permission error",
        skill_type=SkillType.DEBUG,
        patterns=["test"],
        example_conversation=[msg("test")],
        confidence=0.9,
        tags=["test"],
    )

    generator = SkillGenerator(output_dir=tmp_path / "readonly")

    # ディレクトリを作成して読み取り専用にする
    out = tmp_path / "readonly"
    out.mkdir()
    # 書き込み権限を奪う
    out.chmod(0o444)

    try:
        with pytest.raises(PermissionError):
            generator.generate(skill)
    finally:
        out.chmod(0o755)  # 後始末


def test_skill_generator_empty_skill():
    """空のスキル定義でも最低限の出力ができる"""
    skill = SkillDefinition(
        name="",
        description="",
        skill_type=SkillType.CUSTOM,
        patterns=[],
        example_conversation=[],
        confidence=0.0,
        tags=[],
    )

    generator = SkillGenerator()
    with tempfile.TemporaryDirectory() as tmp:
        path = generator.generate(skill, Path(tmp))
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "---" in content  # YAML frontmatter がある


def test_structured_logger(tmp_path):
    """構造化ロガーのテスト"""
    from auto_skill_extractor.logger import StructuredLogger

    log_path = tmp_path / "test.log"
    logger = StructuredLogger(log_path=log_path)

    logger.info("Test info message", key="value")
    logger.warning("Test warning", count=5)
    logger.error("Test error", error_type="test")

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3

    import json
    for line in lines:
        entry = json.loads(line)
        assert "timestamp" in entry
        assert "level" in entry
        assert "message" in entry


def test_structured_logger_level_filter(tmp_path):
    """ログレベルのフィルタリング"""
    from auto_skill_extractor.logger import StructuredLogger

    log_path = tmp_path / "filtered.log"
    logger = StructuredLogger(log_path=log_path, level="WARNING")

    logger.debug("Debug message")  # 出力されない
    logger.info("Info message")    # 出力されない
    logger.warning("Warning message")
    logger.error("Error message")

    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2  # WARNING と ERROR のみ


def test_llm_judge_no_api_key():
    """API キーなしでの LLM judge の挙動"""
    from auto_skill_extractor.llm_judge import LLMJudge

    judge = LLMJudge(api_key="", model="gpt-4o")
    result = judge.evaluate(skills=[], memories=[])

    assert not result.approved
    assert result.score == 0.0
    assert "nothing to judge" in result.blockers[0]


def test_llm_judge_invalid_api():
    """無効な API エンドポイントでのエラーハンドリング"""
    from auto_skill_extractor.llm_judge import LLMJudge

    skill = SkillDefinition(
        name="test-skill",
        description="A test skill",
        skill_type=SkillType.DEBUG,
        patterns=["test"],
        example_conversation=[msg("test")],
        confidence=0.9,
        tags=["test"],
    )

    judge = LLMJudge(api_key="invalid", base_url="http://localhost:1", model="gpt-4o")
    result = judge.evaluate(skills=[skill])

    assert not result.approved
    assert "API" in result.blockers[0] or "Connection" in result.blockers[0]


def test_incremental_mode_marker(tmp_path):
    """増分モードのマーカーファイルの動作確認"""
    marker = tmp_path / ".last_run"
    assert not marker.exists()

    # 初回実行
    marker.write_text(str(datetime.now().timestamp()))
    assert marker.exists()

    # 2回目：タイムスタンプが更新される
    import time
    time.sleep(0.1)
    new_ts = datetime.now().timestamp()
    marker.write_text(str(new_ts))
    assert float(marker.read_text().strip()) == new_ts