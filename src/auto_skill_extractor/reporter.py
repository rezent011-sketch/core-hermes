"""安全な実行レポート生成"""
from pathlib import Path
from typing import Iterable

from .models import ExtractionResult
from .sanitizer import ContentSanitizer


class ReportWriter:
    """ExtractionResultから公開しやすい要約レポートを生成する"""

    def __init__(self, sanitizer: ContentSanitizer | None = None):
        self.sanitizer = sanitizer or ContentSanitizer()

    def write(self, result: ExtractionResult, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(result), encoding="utf-8")
        return path

    def render(self, result: ExtractionResult) -> str:
        lines = [
            "# Core Hermes Extraction Report",
            "",
            "## Summary",
            f"- Total messages: {result.total_messages}",
            f"- Patterns found: {result.patterns_found}",
            f"- Skills extracted: {result.skills_extracted}",
            f"- Memory candidates: {len(result.memory_candidates)}",
            f"- Errors: {len(result.errors)}",
            "",
        ]

        if result.context_enhancement:
            lines.extend([
                "## Context Enhancement",
                self.sanitizer.sanitize(result.context_enhancement.summary[:800]),
                "",
            ])

        if result.orchestrator_decision:
            decision = result.orchestrator_decision
            lines.extend([
                "## Orchestrator Decision",
                f"- Action: {decision.action.value}",
                f"- Reason: {self.sanitizer.sanitize(decision.reason)}",
                f"- Confidence: {decision.confidence:.2f}",
                "- Next steps:",
                *[f"  - {self.sanitizer.sanitize(step)}" for step in decision.next_steps],
                "",
            ])

        if result.errors:
            lines.extend([
                "## Errors",
                *[f"- {self.sanitizer.sanitize(error)}" for error in result.errors[:20]],
                "",
            ])

        lines.extend([
            "## Safety",
            "- Raw message content is not included in this report.",
            "- Generated file paths are intentionally omitted.",
            "- Review generated SKILL.md files before install or publication.",
            "",
        ])
        return "\n".join(lines)
