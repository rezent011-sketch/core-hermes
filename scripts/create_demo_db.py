#!/usr/bin/env python3
"""Create a synthetic Hermes-like state.db for demos."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "examples" / "demo_state.db"
DB.parent.mkdir(parents=True, exist_ok=True)
if DB.exists():
    DB.unlink()

conn = sqlite3.connect(DB)
conn.execute("""
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    user_id TEXT,
    model TEXT,
    started_at REAL NOT NULL,
    ended_at REAL,
    title TEXT,
    message_count INTEGER DEFAULT 0
)
""")
conn.execute("""
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,
    tool_name TEXT,
    timestamp REAL NOT NULL,
    token_count INTEGER DEFAULT 0
)
""")

sessions = [
    ("demo-debug", "demo", "demo-user", "demo-model", 1710000000.0, 1710000200.0, "Debug Python CLI", 4),
    ("demo-search", "demo", "demo-user", "demo-model", 1710000300.0, 1710000500.0, "Search project files", 4),
    ("demo-pref", "demo", "demo-user", "demo-model", 1710000600.0, 1710000800.0, "User preference", 3),
]
conn.executemany("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?)", sessions)

rows = [
    (1, "demo-debug", "user", "Python CLIでTracebackが出る。原因を調べて修正して", None, "[]", None, 1710000001.0, 20),
    (2, "demo-debug", "assistant", "エラーを再現し、入力検証の不足を確認します", None, "[]", None, 1710000002.0, 20),
    (3, "demo-debug", "tool", "Traceback: ValueError: invalid input", None, "[]", "terminal", 1710000003.0, 20),
    (4, "demo-debug", "assistant", "入力検証を追加し、テストで回帰を防ぎます", None, "[]", None, 1710000004.0, 20),
    (5, "demo-search", "user", "プロジェクト内の設定ファイルを検索して、READMEに手順をまとめて", None, "[]", None, 1710000301.0, 20),
    (6, "demo-search", "assistant", "設定ファイルを検索し、関連箇所を確認します", None, "[]", None, 1710000302.0, 20),
    (7, "demo-search", "tool", "Found config.yaml and pyproject.toml", None, "[]", "search_files", 1710000303.0, 20),
    (8, "demo-search", "assistant", "READMEに安全な手順としてdry-runから始める説明を追加します", None, "[]", None, 1710000304.0, 20),
    (9, "demo-pref", "user", "ユーザーは短く実行結果から報告される形式を好む", None, "[]", None, 1710000601.0, 20),
    (10, "demo-pref", "assistant", "ユーザーは簡潔な報告を好む、という長期設定候補として扱います", None, "[]", None, 1710000602.0, 20),
    (11, "demo-pref", "user", "環境はデモ用で、秘密情報を含まない", None, "[]", None, 1710000603.0, 20),
]
conn.executemany("INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
conn.commit()
conn.close()
print(DB)
