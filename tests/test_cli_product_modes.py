import subprocess
import sys
from pathlib import Path

from tests.test_extractor import create_test_db


def test_cli_writes_manifest_and_report(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    manifest = tmp_path / "manifest.json"
    report = tmp_path / "report.md"
    create_test_db(db)

    completed = subprocess.run(
        [
            sys.executable,
            "run.py",
            "--db", str(db),
            "--output", str(out),
            "--min-confidence", "0.5",
            "--manifest", str(manifest),
            "--report", str(report),
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    assert manifest.exists()
    assert report.exists()


def test_cli_strict_fails_when_no_skills(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    create_test_db(db)

    completed = subprocess.run(
        [
            sys.executable,
            "run.py",
            "--db", str(db),
            "--output", str(out),
            "--min-confidence", "0.99",
            "--strict",
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 2
    assert "Strict mode failed" in completed.stdout
