"""LLM judge互換の品質評価抽象化。

現時点ではAPI費用を発生させないHeuristicJudgeを標準にする。
将来LLM judgeを差し込めるよう、JudgeDecisionを共通出力にしている。
"""
from dataclasses import dataclass, field
from typing import Iterable, List

from .models import MemoryCandidate, SkillDefinition
from .quality import SkillQualityScorer
from .risk import RiskScorer


@dataclass
class JudgeDecision:
    approved: bool
    score: float
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class HeuristicJudge:
    """生成スキル・メモリ候補を製品運用前提で評価"""

    def __init__(self, approval_threshold: float = 0.85):
        self.approval_threshold = approval_threshold
        self.skill_scorer = SkillQualityScorer()
        self.risk_scorer = RiskScorer()

    def evaluate(
        self,
        skills: Iterable[SkillDefinition] | None = None,
        memories: Iterable[MemoryCandidate] | None = None,
    ) -> JudgeDecision:
        skills = list(skills or [])
        memories = list(memories or [])
        blockers: List[str] = []
        warnings: List[str] = []

        skill_scores = [self.skill_scorer.score(skill) for skill in skills]
        memory_scores = [self._memory_quality(memory) for memory in memories]
        risk_scores = []

        for skill in skills:
            risk_scores.append(self.risk_scorer.score_text("\n".join([
                skill.name,
                skill.description,
                "\n".join(skill.patterns),
                " ".join(skill.tags),
            ])))
        for memory in memories:
            risk_scores.append(self.risk_scorer.score_text(memory.content))

        for risk in risk_scores:
            if risk.score >= 0.7:
                blockers.append(f"risk too high: {', '.join(risk.reasons)}")
            elif risk.score >= 0.3:
                warnings.append(f"risk warning: {', '.join(risk.reasons)}")

        if skills and min(skill_scores) < 0.65:
            blockers.append("skill quality below 0.65")
        if memories and min(memory_scores) < 0.55:
            blockers.append("memory quality below 0.55")
        if not skills and not memories:
            blockers.append("nothing to judge")

        score_parts: List[float] = []
        if skill_scores:
            score_parts.append(sum(skill_scores) / len(skill_scores))
        if memory_scores:
            score_parts.append(sum(memory_scores) / len(memory_scores))
        if risk_scores:
            score_parts.append(1.0 - max(r.score for r in risk_scores))

        score = sum(score_parts) / len(score_parts) if score_parts else 0.0
        score = round(max(0.0, min(score, 1.0)), 3)
        approved = not blockers and score >= self.approval_threshold
        if score < self.approval_threshold:
            blockers.append(f"judge score below threshold: {score:.2f}")

        return JudgeDecision(approved=approved, score=score, blockers=blockers, warnings=warnings)

    def _memory_quality(self, memory: MemoryCandidate) -> float:
        text = memory.content.strip()
        score = min(max(memory.confidence, 0.0), 1.0) * 0.55
        if len(text) >= 20:
            score += 0.2
        if any(marker in text for marker in ["ユーザーは", "環境", "設定", "必要", "好む", "使う", "必須"]):
            score += 0.2
        if len(text) > 700:
            score -= 0.15
        if text in {"お願いします", "ありがとう", "こんにちは"}:
            score = 0.0
        return round(max(0.0, min(score, 1.0)), 3)
