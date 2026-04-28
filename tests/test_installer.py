from pathlib import Path

from auto_skill_extractor.installer import SkillInstaller


def test_installer_copies_reviewed_skill_to_hermes_skills(tmp_path):
    src = tmp_path / "review" / "debug-python.md"
    src.parent.mkdir()
    src.write_text("---\nname: debug-python\ndescription: test\n---\n# debug-python\n", encoding="utf-8")
    hermes_home = tmp_path / "hermes"

    installed = SkillInstaller(hermes_home=hermes_home).install_file(src)

    assert installed.exists()
    assert installed.name == "SKILL.md"
    assert installed.parent.name == "debug-python"
    assert "debug-python" in installed.read_text(encoding="utf-8")


def test_installer_rejects_missing_frontmatter(tmp_path):
    src = tmp_path / "bad.md"
    src.write_text("# no frontmatter", encoding="utf-8")

    installer = SkillInstaller(hermes_home=tmp_path / "hermes")
    try:
        installer.install_file(src)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "frontmatter" in str(e)


def test_install_directory_installs_all_md(tmp_path):
    review = tmp_path / "review"
    review.mkdir()
    for name in ["a", "b"]:
        (review / f"{name}.md").write_text(f"---\nname: {name}\ndescription: test\n---\n# {name}\n", encoding="utf-8")

    installed = SkillInstaller(hermes_home=tmp_path / "hermes").install_directory(review)
    assert len(installed) == 2
