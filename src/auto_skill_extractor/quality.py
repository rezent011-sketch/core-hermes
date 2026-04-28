"""スキル品質評価・重複統合・検証"""
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import List

from .models import SkillDefinition


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SkillQualityScorer:
    """生成スキルの品質スコアを算出"""

    def score(self, skill: SkillDefinition) -> float:
        score = 0.0

        # ベース信頼度
        score += min(max(skill.confidence, 0.0), 1.0) * 0.25

        # 説明品質
        if len(skill.description.strip()) >= 20:
            score += 0.20
        elif len(skill.description.strip()) >= 8:
            score += 0.10

        # パターン数
        meaningful_patterns = [p for p in skill.patterns if len(p.strip()) >= 4]
        score += min(len(meaningful_patterns) / 3, 1.0) * 0.20

        # 例示会話
        if len(skill.example_conversation) >= 2:
            roles = {m.role for m in skill.example_conversation}
            if "user" in roles and "assistant" in roles:
                score += 0.20
            else:
                score += 0.10

        # タグ
        score += min(len(set(skill.tags)) / 3, 1.0) * 0.15

        return round(min(score, 1.0), 3)


class SkillValidator:
    """SKILL.md化前の最低品質チェック"""

    def __init__(self, min_score: float = 0.5):
        self.min_score = min_score
        self.scorer = SkillQualityScorer()

    def validate(self, skill: SkillDefinition) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if not skill.name or len(skill.name.strip()) < 3:
            errors.append("name is required and must be at least 3 chars")
        if not skill.description or len(skill.description.strip()) < 8:
            errors.append("description is too short")
        if not skill.patterns:
            errors.append("patterns are required")
        if not skill.example_conversation:
            warnings.append("example_conversation is empty")
        if skill.confidence < 0 or skill.confidence > 1:
            errors.append("confidence must be between 0 and 1")

        quality = self.scorer.score(skill)
        if quality < self.min_score:
            errors.append(f"quality score too low: {quality:.2f}")

        return ValidationResult(is_valid=not errors, errors=errors, warnings=warnings)


class SkillDeduplicator:
    """類似スキルを統合"""

    def __init__(self, similarity_threshold: float = 0.72):
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, skills: List[SkillDefinition]) -> List[SkillDefinition]:
        merged: List[SkillDefinition] = []

        for skill in sorted(skills, key=lambda s: s.confidence, reverse=True):
            match = self._find_match(skill, merged)
            if match is None:
                merged.append(skill)
            else:
                self._merge_into(match, skill)

        return sorted(merged, key=lambda s: s.confidence, reverse=True)

    def _find_match(self, skill: SkillDefinition, candidates: List[SkillDefinition]):
        for candidate in candidates:
            if skill.skill_type != candidate.skill_type:
                continue
            if self._similarity(skill, candidate) >= self.similarity_threshold:
                return candidate
        return None

    def _similarity(self, a: SkillDefinition, b: SkillDefinition) -> float:
        name_sim = SequenceMatcher(None, a.name, b.name).ratio()
        if a.name == b.name:
            return 1.0
        tag_overlap = self._jaccard(set(a.tags), set(b.tags))
        pattern_overlap = self._jaccard(set(a.patterns), set(b.patterns))
        return (name_sim * 0.45) + (tag_overlap * 0.35) + (pattern_overlap * 0.20)

    def _jaccard(self, a: set, b: set) -> float:
        if not a and not b:
            return 0.0
        return len(a & b) / len(a | b)

    def _merge_into(self, target: SkillDefinition, incoming: SkillDefinition) -> None:
        target.confidence = max(target.confidence, incoming.confidence)
        target.patterns = list(dict.fromkeys(target.patterns + incoming.patterns))[:8]
        target.tags = list(dict.fromkeys(target.tags + incoming.tags))[:8]
        target.example_conversation = (target.example_conversation + incoming.example_conversation)[:8]
        if len(incoming.description) > len(target.description):
            target.description = incoming.description
