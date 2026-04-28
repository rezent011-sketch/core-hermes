"""生成物の漏洩リスクスコアリング"""
from dataclasses import dataclass, field
import re
from typing import List

from .safety import SafetyAuditor


@dataclass
class RiskScore:
    score: float
    reasons: List[str] = field(default_factory=list)


class RiskScorer:
    """秘密情報・PII・外部URLの混入リスクを0.0-1.0で評価"""

    URL_PATTERN = re.compile(r"https?://[^\s)\]]+")

    WEIGHTS = {
        "api_key": 0.9,
        "github_token": 0.9,
        "telegram_token": 0.9,
        "jwt": 0.9,
        "key_value_secret": 0.8,
        "email": 0.35,
        "numeric_id": 0.35,
        "url": 0.25,
    }

    def __init__(self, auditor: SafetyAuditor | None = None):
        self.auditor = auditor or SafetyAuditor()

    def score_text(self, text: str) -> RiskScore:
        reasons: List[str] = []
        result = self.auditor.audit_text(text or "")
        for finding in result.findings:
            reasons.append(finding.kind)
        if self.URL_PATTERN.search(text or ""):
            reasons.append("url")

        unique = list(dict.fromkeys(reasons))
        score = min(sum(self.WEIGHTS.get(reason, 0.2) for reason in unique), 1.0)
        return RiskScore(score=round(score, 3), reasons=unique)
