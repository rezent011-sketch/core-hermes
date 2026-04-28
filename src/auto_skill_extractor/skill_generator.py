"""スキル生成モジュール"""
import re
from pathlib import Path
from typing import Optional

from .models import SkillDefinition


class SkillGenerator:
    """SKILL.mdファイルを生成"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir) if output_dir else Path("./extracted_skills")
    
    def generate(self, skill: SkillDefinition, output_dir: Optional[Path] = None) -> Path:
        """スキル定義からSKILL.mdを生成"""
        target_dir = output_dir or self.output_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名を生成（安全な形式）
        filename = self._sanitize_filename(skill.name) + ".md"
        filepath = target_dir / filename
        
        # Markdownを生成
        content = self._generate_markdown(skill)
        
        # 書き出し
        filepath.write_text(content, encoding="utf-8")
        
        return filepath
    
    def generate_skill_directory(
        self,
        skill: SkillDefinition,
        output_dir: Optional[Path] = None
    ) -> Path:
        """スキルディレクトリ全体を生成（SKILL.md + 補助ファイル）"""
        target_dir = output_dir or self.output_dir
        skill_dir = target_dir / self._sanitize_filename(skill.name)
        skill_dir.mkdir(parents=True, exist_ok=True)
        
        # SKILL.md
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(self._generate_markdown(skill), encoding="utf-8")
        
        return skill_dir
    
    def _generate_markdown(self, skill: SkillDefinition) -> str:
        """SKILL.mdの内容を生成"""
        return f"""---
name: {skill.name}
description: "{skill.description}"
version: 1.0.0
tags: [{self._format_tags(skill.tags)}]
metadata:
  skill_type: {skill.skill_type}
  confidence: {skill.confidence:.2f}
  created_at: {skill.created_at.isoformat()}
---

# {skill.name}

{skill.description}

## 検出パターン

{self._format_patterns(skill.patterns)}

## 例示会話

{self._format_examples(skill.example_conversation)}

## 使用ガイド

### 前提条件

- Hermes Agent環境
- Python 3.10+

### 適用シナリオ

{self._format_scenarios(skill.skill_type)}

### 関連機能

{self._format_related(skill.skill_type, skill.tags)}

---

*自動生成されたスキル定義（Core Hermes auto-skill-extractor）*
"""
    
    def _sanitize_filename(self, name: str) -> str:
        """ファイル名として安全な文字列に変換"""
        # 日本語を含む場合はASCIIに変換するか、そのまま許可
        sanitized = re.sub(r"[^\w\-]", "-", name)
        sanitized = re.sub(r"-+", "-", sanitized)  # 連続ハイフンを単一に
        return sanitized.strip("-").lower() or "unnamed-skill"
    
    def _format_tags(self, tags: list) -> str:
        """タグをYAML形式に整形"""
        if not tags:
            return '"auto-generated"'
        return ", ".join(f'"{t}"' for t in tags[:5])
    
    def _format_patterns(self, patterns: list) -> str:
        """パターンリストを整形"""
        if not patterns:
            return "- パターンが検出されませんでした"
        return "\n".join(f"- {p}" for p in patterns)
    
    def _format_examples(self, messages: list) -> str:
        """例示会話を整形"""
        if not messages:
            return "*例示記録なし*"
        
        lines = []
        for msg in messages:
            role_icon = {"user": "👤", "assistant": "🤖", "tool": "🔧"}.get(
                msg.role, "📝"
            )
            content = msg.content[:150] + "..." if len(msg.content) > 150 else msg.content
            lines.append(f"### {role_icon} {msg.role.capitalize()}\n\n{content}\n")
        
        return "\n---\n\n".join(lines)
    
    def _format_scenarios(self, skill_type) -> str:
        """シナリオを整形"""
        scenarios = {
            "code_generation": "- 新規機能実装\\n- コードテンプレート作成",
            "debugging": "- エラートラブルシュート\\n- ログ分析",
            "analysis": "- データパターン調査\\n- 比較評価",
            "search": "- 情報探索\\n- ファイル検索",
            "refactoring": "- コード改善\\n- 構造整理",
            "integration": "- API連携\\n- サービス統合",
        }
        return scenarios.get(skill_type.value, "- 汎用ユースケース")
    
    def _format_related(self, skill_type, tags: list) -> str:
        """関連機能を整形"""
        related = [f"- `{skill_type.value}` タイプのスキル"]
        if tags:
            related.append(f"- タグ: {', '.join(tags[:3])}")
        return "\n".join(related)
