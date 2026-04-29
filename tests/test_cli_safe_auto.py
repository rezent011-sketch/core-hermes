import json
import subprocess
import sys
from pathlib import Path

from tests.test_extractor import create_test_db


def test_cli_safe_auto_writes_manifest_and_review(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    hermes_home = tmp_path / "hermes"
    create_test_db(db)

    completed = subprocess.run(
        [
            sys.executable,
            "run.py",
            "--db", str(db),
            "--output", str(out),
            "--min-confidence", "0.5",
            "--safe-auto",
            "--auto-threshold", "0.99",
            "--hermes-home", str(hermes_home),
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    # タイムスタンプ付きマニフェストファイルを検索
    manifests = list(out.glob("safe-auto-manifest-*.json"))
    assert len(manifests) == 1
    manifest = manifests[0]
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["review"] >= 1
    assert data["auto_install"] == 0
    assert list((out / "review").glob("*.md"))


def test_cli_safe_auto_can_auto_install_with_low_test_threshold(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    hermes_home = tmp_path / "hermes"
    create_test_db(db)

    completed = subprocess.run(
        [
            sys.executable,
            "run.py",
            "--db", str(db),
            "--output", str(out),
            "--min-confidence", "0.5",
            "--safe-auto",
            "--auto-threshold", "0.5",
            "--hermes-home", str(hermes_home),
        ],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0
    assert list((hermes_home / "skills" / "core-hermes").rglob("SKILL.md"))
