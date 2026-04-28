"""メモリ候補の人間レビュー用Markdown生成"""
from pathlib import Path
from typing import Iterable, List

from .models import MemoryCandidate
from .sanitizer import ContentSanitizer


class MemoryReviewWriter:
    """保存候補メモリをチェックボックス付きレビュー文書へ変換"""

    def __init__(self, sanitizer: ContentSanitizer | None = None):
        self.sanitizer = sanitizer or ContentSanitizer()

    def write(self, candidates: Iterable[MemoryCandidate], path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(candidates), encoding="utf-8")
        return path

    def render(self, candidates: Iterable[MemoryCandidate]) -> str:
        ordered: List[MemoryCandidate] = sorted(candidates, key=lambda c: c.confidence, reverse=True)
        lines = [
            "# Core Hermes Memory Review",
            "",
            "Review manually. Check only durable, non-sensitive facts.",
            "Do not save task progress, one-off logs, raw IDs, tokens, URLs, or temporary state.",
            "",
        ]
        if not ordered:
            lines.append("No memory candidates.")
            return "\n".join(lines)

        for c in ordered:
            content = self.sanitizer.sanitize(c.content).replace("\n", " ").strip()
            lines.extend([
                f"- [ ] ({c.memory_type.value}, {c.confidence:.2f}) {content}",
            ])
        lines.append("")
        return "\n".join(lines)
