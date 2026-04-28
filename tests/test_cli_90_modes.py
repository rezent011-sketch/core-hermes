import subprocess
import sys
from pathlib import Path

from tests.test_extractor import create_test_db


def test_cli_memory_review_out_writes_review_file(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    review = tmp_path / "memory_review.md"
    create_test_db(db)

    completed = subprocess.run(
        [
            sys.executable,
            "run.py",
            "--db", str(db),
            "--output", str(out),
            "--min-confidence", "0.5",
            "--memory-review",
            "--memory-review-out", str(review),
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    assert review.exists()
    assert "Memory Review" in review.read_text(encoding="utf-8")


def test_cli_strict_fails_on_safety_audit_leak(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    create_test_db(db)
    import sqlite3
    conn = sqlite3.connect(db)
    conn.execute("UPDATE messages SET content = content || ' token=abc1234567890' WHERE id = 1")
    conn.commit()
    conn.close()

    completed = subprocess.run(
        [
            sys.executable,
            "run.py",
            "--db", str(db),
            "--output", str(out),
            "--min-confidence", "0.5",
            "--strict",
            "--unsafe-no-sanitize",
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 2
    assert "Strict mode failed" in completed.stdout
