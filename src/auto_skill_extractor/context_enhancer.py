"""Core Hermes v2.0 - context-enhancer

タスク文と抽出済みメモリ/スキル候補を照合し、次セッションに渡す安全な文脈を作る。
"""
import re
from pathlib import Path
from typing import Iterable, List

from .models import ContextEnhancement, MemoryCandidate
from .sanitizer import ContentSanitizer


class ContextEnhancer:
    """クエリに関連するメモリ・スキルをランキングして短い文脈に圧縮"""

    def __init__(self, sanitizer: ContentSanitizer | None = None):
        self.sanitizer = sanitizer or ContentSanitizer()

    def enhance(
        self,
        query: str,
        memories: Iterable[MemoryCandidate] | None = None,
        skills_dir: Path | None = None,
        max_memories: int = 5,
        max_skills: int = 5,
    ) -> ContextEnhancement:
        query = self.sanitizer.sanitize(query or "")
        memories = list(memories or [])
        ranked_memories = self._rank_memories(query, memories)[:max_memories]
        ranked_skills = self._rank_skills(query, skills_dir)[:max_skills] if skills_dir else []

        summary_parts: List[str] = []
        if ranked_memories:
            summary_parts.append("Relevant memories: " + "; ".join(m.content[:120] for m in ranked_memories))
        if ranked_skills:
            summary_parts.append("Relevant skills: " + ", ".join(ranked_skills))
        if not summary_parts:
            summary_parts.append("No high-confidence context found.")

        warnings = []
        if any("[SECRET]" in m.content for m in ranked_memories):
            warnings.append("Some context was redacted before use")

        return ContextEnhancement(
            summary=self.sanitizer.sanitize(" ".join(summary_parts))[:1200],
            relevant_memories=ranked_memories,
            relevant_skills=ranked_skills,
            warnings=warnings,
        )

    def _rank_memories(self, query: str, memories: List[MemoryCandidate]) -> List[MemoryCandidate]:
        q_terms = self._terms(query)
        scored = []
        for memory in memories:
            terms = self._terms(memory.content + " " + " ".join(memory.tags))
            overlap = len(q_terms & terms)
            score = overlap + memory.confidence
            if overlap or memory.confidence >= 0.82:
                scored.append((score, memory))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [m for _, m in scored]

    def _rank_skills(self, query: str, skills_dir: Path) -> List[str]:
        if not skills_dir.exists():
            return []
        q_terms = self._terms(query)
        scored = []
        for path in list(skills_dir.rglob("*.md"))[:200]:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:4000]
            except OSError:
                continue
            terms = self._terms(path.stem + " " + text)
            overlap = len(q_terms & terms)
            if overlap:
                scored.append((overlap, path.stem))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [name for _, name in scored]

    def _terms(self, text: str) -> set[str]:
        return set(re.findall(r"[A-Za-z0-9_\-]{3,}|[\u3040-\u30ff\u4e00-\u9fff]{2,}", (text or "").lower()))
