import subprocess
import sys
from pathlib import Path

from tests.test_extractor import create_test_db


def test_cli_judge_writes_judge_summary_to_manifest(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    manifest = tmp_path / "manifest.json"
    create_test_db(db)

    completed = subprocess.run(
        [
            sys.executable,
            "run.py",
            "--db", str(db),
            "--output", str(out),
            "--min-confidence", "0.5",
            "--judge",
            "--manifest", str(manifest),
            "--strict",
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    text = manifest.read_text(encoding="utf-8")
    assert "judge_score" in text
    assert "quality_gate_passed" in text


def test_cli_quality_threshold_can_fail_strict(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    create_test_db(db)

    completed = subprocess.run(
        [
            sys.executable,
            "run.py",
            "--db", str(db),
            "--output", str(out),
            "--min-confidence", "0.5",
            "--judge",
            "--quality-threshold", "0.99",
            "--strict",
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 2
    assert "Quality gate failed" in completed.stdout
