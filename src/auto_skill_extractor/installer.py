"""Hermes skillsディレクトリへの安全インストール"""
import re
import shutil
from pathlib import Path
from typing import List, Optional


class SkillInstaller:
    """レビュー済みSKILL.mdをHermes skillsへ導入"""

    def __init__(self, hermes_home: Optional[Path] = None):
        self.hermes_home = Path(hermes_home).expanduser() if hermes_home else Path("~/.hermes").expanduser()
        self.skills_dir = self.hermes_home / "skills" / "core-hermes"

    def install_file(self, source: Path) -> Path:
        """単一Markdownファイルをスキルとして導入"""
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(source)

        content = source.read_text(encoding="utf-8")
        self._validate_skill_markdown(content)
        skill_name = self._extract_name(content) or source.stem
        safe_name = self._safe_name(skill_name)

        target_dir = self.skills_dir / safe_name
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "SKILL.md"

        # 既存があればバックアップ
        if target.exists():
            backup = target.with_suffix(".md.bak")
            shutil.copy2(target, backup)

        target.write_text(content, encoding="utf-8")
        return target

    def install_directory(self, source_dir: Path) -> List[Path]:
        """ディレクトリ内の.mdをすべて導入"""
        source_dir = Path(source_dir)
        if not source_dir.exists():
            raise FileNotFoundError(source_dir)

        installed: List[Path] = []
        for md in sorted(source_dir.glob("*.md")):
            installed.append(self.install_file(md))
        return installed

    def _validate_skill_markdown(self, content: str) -> None:
        if not content.startswith("---\n"):
            raise ValueError("missing frontmatter")
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("invalid frontmatter")
        frontmatter = parts[1]
        if "name:" not in frontmatter:
            raise ValueError("frontmatter missing name")
        if "description:" not in frontmatter:
            raise ValueError("frontmatter missing description")
        if "# " not in parts[2]:
            raise ValueError("missing markdown heading")

    def _extract_name(self, content: str) -> Optional[str]:
        match = re.search(r"(?m)^name:\s*['\"]?([^'\"\n]+)['\"]?\s*$", content)
        return match.group(1).strip() if match else None

    def _safe_name(self, name: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower())
        safe = re.sub(r"-+", "-", safe).strip("-")
        return safe or "unnamed-skill"
