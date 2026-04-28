import subprocess
import sys
from pathlib import Path


def test_ci_script_uses_venv_or_python3_and_runs_from_repo_root():
    script = Path("scripts/ci.sh").read_text()

    assert "python3" in script
    assert "PYTHON_BIN" in script
    assert "VIRTUAL_ENV" in script
    assert "Using Python:" in script
    assert "cd \"$ROOT_DIR\"" in script
    assert "python -m pytest" not in script


def test_gitignore_blocks_private_databases_and_generated_outputs():
    gitignore = Path(".gitignore").read_text()

    required_patterns = [
        "state.db",
        "*.db",
        "*.sqlite",
        "*.sqlite3",
        "core-hermes-report.md",
        "core-hermes-manifest.json",
        "memory_review.md",
        "*.env",
    ]
    for pattern in required_patterns:
        assert pattern in gitignore


def test_github_actions_workflow_template_exists_with_e2e_demo_check():
    workflow = Path(".github/workflows/ci.yml")
    disabled_template = Path(".github-disabled/workflows/ci.yml")

    assert workflow.exists() or disabled_template.exists()
    text = (workflow if workflow.exists() else disabled_template).read_text()
    assert "python-version" in text
    assert "./scripts/ci.sh" in text
    assert "examples/demo_state.db" in text
    assert "--dry-run" in text
    assert "--strict" in text


def test_release_checklist_exists_and_emphasizes_privacy():
    checklist = Path("RELEASE_CHECKLIST.md")

    assert checklist.exists()
    text = checklist.read_text()
    assert "state.db" in text
    assert "dry-run" in text
    assert "GitHub Actions" in text
    assert "Do not publish" in text


def test_version_is_preview_consistent():
    pyproject = Path("pyproject.toml").read_text()
    init = Path("src/auto_skill_extractor/__init__.py").read_text()
    readme = Path("README.md").read_text()

    assert 'version = "0.1.0"' in pyproject
    assert '__version__ = "0.1.0-preview"' in init
    assert "v0.1.0-preview" in readme
    assert 'version = "2.0.0"' not in pyproject
    assert '__version__ = "2.0.0"' not in init


def test_fresh_install_demo_e2e(tmp_path):
    repo = Path.cwd()
    venv = tmp_path / "venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    py = venv / "bin" / "python"

    subprocess.run([str(py), "-m", "pip", "install", "-e", str(repo), "pytest"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(py), "run.py", "--help"], cwd=repo, check=True, stdout=subprocess.DEVNULL)

    out = tmp_path / "demo-output"
    report = tmp_path / "demo-report.md"
    manifest = tmp_path / "demo-manifest.json"
    memory = tmp_path / "demo-memory.md"
    result = subprocess.run(
        [
            str(py),
            "run.py",
            "--db",
            "examples/demo_state.db",
            "--output",
            str(out),
            "--memory-review",
            "--memory-review-out",
            str(memory),
            "--judge",
            "--strict",
            "--report",
            str(report),
            "--manifest",
            str(manifest),
        ],
        cwd=repo,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert report.exists()
    assert manifest.exists()
    assert memory.exists()
