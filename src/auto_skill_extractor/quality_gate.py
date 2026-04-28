"""最終品質ゲート"""
from dataclasses import dataclass, field
from typing import List

from .judge import JudgeDecision
from .models import ExtractionResult


@dataclass
class QualityGateResult:
    passed: bool
    exit_code: int
    reasons: List[str] = field(default_factory=list)


class QualityGate:
    """strict運用時に出荷可否を一元判断"""

    def __init__(self, min_judge_score: float = 0.85):
        self.min_judge_score = min_judge_score

    def check(self, result: ExtractionResult, judge_decision: JudgeDecision | None = None) -> QualityGateResult:
        reasons: List[str] = []
        if result.errors:
            reasons.extend(result.errors)
        if result.skills_extracted == 0:
            reasons.append("no skills extracted")
        if judge_decision:
            if not judge_decision.approved:
                reasons.extend(judge_decision.blockers or ["judge rejected output"])
            if judge_decision.score < self.min_judge_score:
                reasons.append(f"judge score below quality threshold: {judge_decision.score:.2f}")
        passed = not reasons
        return QualityGateResult(passed=passed, exit_code=0 if passed else 2, reasons=reasons)
