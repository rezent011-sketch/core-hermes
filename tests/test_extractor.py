import sqlite3
from pathlib import Path

from auto_skill_extractor import AutoSkillExtractor, ExtractionConfig


def create_test_db(path: Path):
    conn = sqlite3.connect(path)
    conn.execute("""
        CREATE TABLE sessions (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            started_at REAL NOT NULL,
            ended_at REAL,
            message_count INTEGER DEFAULT 0,
            title TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT,
            tool_calls TEXT,
            timestamp REAL NOT NULL
        )
    """)
    conn.execute(
        "INSERT INTO sessions (id, source, started_at, ended_at, message_count, title) VALUES (?, ?, ?, ?, ?, ?)",
        ("s1", "test", 1710000000.0, 1710000100.0, 4, "debug session"),
    )
    rows = [
        (1, "s1", "user", "Pythonでエラーが出る。Tracebackを見て修正して", "[]", 1710000001.0),
        (2, "s1", "assistant", "エラー内容を確認して修正します", "[]", 1710000002.0),
        (3, "s1", "tool", '{"output":"Traceback: ValueError"}', "[]", 1710000003.0),
        (4, "s1", "assistant", "原因は入力値です。修正しました", "[]", 1710000004.0),
    ]
    conn.executemany("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()


def test_extractor_generates_skill(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    create_test_db(db)

    cfg = ExtractionConfig(db_path=db, output_dir=out, min_confidence=0.5, max_skills_per_run=3)
    result = AutoSkillExtractor(cfg).run()

    assert result.skills_extracted >= 1
    assert result.saved_files
    assert Path(result.saved_files[0]).exists()
    assert "debug" in Path(result.saved_files[0]).read_text(encoding="utf-8")
