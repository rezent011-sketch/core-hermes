from pathlib import Path

from auto_skill_extractor.manifest import ManifestWriter
from auto_skill_extractor.models import ExtractionResult


def test_manifest_writer_records_counts_not_raw_content(tmp_path):
    result = ExtractionResult(
        total_messages=100,
        patterns_found=4,
        skills_extracted=2,
        saved_files=[str(tmp_path / "a.md"), str(tmp_path / "b.md")],
        errors=[],
    )

    path = ManifestWriter().write(result, tmp_path / "manifest.json")
    text = path.read_text(encoding="utf-8")

    assert '"total_messages": 100' in text
    assert '"skills_extracted": 2' in text
    assert '"file_count": 2' in text
    assert "saved_files" not in text
    assert str(tmp_path) not in text
