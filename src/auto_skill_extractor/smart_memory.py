"""Core Hermes v2.0 - smart-memory

会話履歴から、長期記憶に保存する価値がある候補だけを抽出する。
自動保存はしない。必ずreview前提で候補を返す。
"""
import re
from typing import Iterable, List

from .models import MemoryCandidate, MemoryType, SessionMessage
from .sanitizer import ContentSanitizer


class SmartMemoryExtractor:
    """ユーザー設定・環境事実・プロジェクト事実・ワークフローを抽出"""

    RULES = [
        (MemoryType.USER_PREFERENCE, re.compile(r"(?:好む|嫌い|優先|必ず|しないで|してほしい|敬語不要|日本語|コスト|簡潔)"), 0.78),
        (MemoryType.ENVIRONMENT, re.compile(r"(?:Mac mini|VPS|Tailscale|/Users/|~/|ポート|環境|インストール済み|設定ファイル)"), 0.72),
        (MemoryType.PROJECT_FACT, re.compile(r"(?:プロジェクト|リポジトリ|GitHub|ブランチ|README|スキルエンジン|core-hermes)"), 0.70),
        (MemoryType.WORKFLOW, re.compile(r"(?:手順|方法|次回|コマンド|実行|修復|回避|ワークフロー|運用)"), 0.68),
    ]

    NOISE = re.compile(r"^(はい|お願いします|ありがとう|こんにちは|了解|ok|OK|done)$")

    def __init__(self, sanitizer: ContentSanitizer | None = None, max_candidates: int = 20):
        self.sanitizer = sanitizer or ContentSanitizer()
        self.max_candidates = max_candidates

    def extract(self, messages: Iterable[SessionMessage]) -> List[MemoryCandidate]:
        candidates: List[MemoryCandidate] = []
        seen = set()

        for msg in messages:
            if msg.role not in {"user", "assistant"}:
                continue
            text = self._normalize(msg.content)
            if not self._is_candidate_text(text):
                continue

            for memory_type, pattern, base_confidence in self.RULES:
                if not pattern.search(text):
                    continue
                content = self.sanitizer.sanitize(text)
                key = (memory_type.value, content[:120])
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(MemoryCandidate(
                    content=content[:500],
                    memory_type=memory_type,
                    confidence=self._score(content, base_confidence),
                    evidence_session_id=msg.session_id,
                    source_message_id=msg.id,
                    tags=self._tags(memory_type, content),
                ))
                break

        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates[: self.max_candidates]

    def _normalize(self, text: str) -> str:
        text = re.sub(r"```[\s\S]*?```", "[CODE]", text or "")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _is_candidate_text(self, text: str) -> bool:
        if len(text) < 12 or self.NOISE.match(text):
            return False
        if len(text) > 1500:
            return False
        return True

    def _score(self, text: str, base: float) -> float:
        score = base
        if any(w in text for w in ["必ず", "次回", "設定", "環境", "好む", "嫌い"]):
            score += 0.08
        if "[SECRET]" in text or "[EMAIL]" in text or "[ID]" in text:
            score -= 0.12
        if len(text) > 80:
            score += 0.04
        return round(max(0.0, min(score, 0.98)), 3)

    def _tags(self, memory_type: MemoryType, text: str) -> List[str]:
        tags = [memory_type.value]
        for keyword in ["hermes", "github", "mac", "vps", "cost", "japanese", "workflow"]:
            if keyword.lower() in text.lower():
                tags.append(keyword)
        return tags[:5]
