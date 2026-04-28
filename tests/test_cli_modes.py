from pathlib import Path
from unittest.mock import patch

from auto_skill_extractor import AutoSkillExtractor, ExtractionConfig
from auto_skill_extractor.main import main
from tests.test_extractor import create_test_db


def test_dry_run_does_not_write_files(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    create_test_db(db)

    cfg = ExtractionConfig(db_path=db, output_dir=out, min_confidence=0.5, max_skills_per_run=3, dry_run=True)
    result = AutoSkillExtractor(cfg).run()

    assert result.skills_extracted >= 1
    assert not out.exists()
    assert result.saved_files == []


def test_review_writes_review_directory(tmp_path):
    db = tmp_path / "state.db"
    out = tmp_path / "skills"
    create_test_db(db)

    cfg = ExtractionConfig(db_path=db, output_dir=out, min_confidence=0.5, max_skills_per_run=3, review=True)
    result = AutoSkillExtractor(cfg).run()

    review_dir = out / "review"
    assert review_dir.exists()
    assert list(review_dir.glob("*.md"))
    assert all("review" in p for p in result.saved_files)
