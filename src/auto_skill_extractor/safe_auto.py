"""安全付き自動運用モード。

高スコア・低リスクだけを自動導入し、それ以外はreview隔離または破棄する。
"""
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, List

from .installer import SkillInstaller
from .models import SkillDefinition
from .risk import RiskScorer
from .safety import SafetyAuditor
from .skill_generator import SkillGenerator


@dataclass
class SafeAutoDecision:
    skill_name: str
    action: str  # auto_install | review | reject
    reason: str
    judge_score: float
    risk_score: float


class SafeAutoPolicy:
    """safe-auto採用ルール"""

    def __init__(self, auto_threshold: float = 0.93, review_threshold: float = 0.75):
        self.auto_threshold = auto_threshold
        self.review_threshold = review_threshold

    def decide(
        self,
        skill: SkillDefinition,
        judge_score: float,
        risk_score: float,
        safety_passed: bool,
    ) -> SafeAutoDecision:
        if not safety_passed:
            return SafeAutoDecision(skill.name, "reject", "safety audit failed", judge_score, risk_score)
        if risk_score > 0:
            return SafeAutoDecision(skill.name, "reject", "risk score must be zero", judge_score, risk_score)
        if judge_score >= self.auto_threshold and skill.confidence >= self.auto_threshold:
            return SafeAutoDecision(skill.name, "auto_install", "passed safe-auto policy", judge_score, risk_score)
        if judge_score >= self.review_threshold and skill.confidence >= self.review_threshold:
            return SafeAutoDecision(skill.name, "review", "below auto threshold; needs review", judge_score, risk_score)
        return SafeAutoDecision(skill.name, "reject", "below review threshold", judge_score, risk_score)


class SafeAutoRunner:
    """safe-auto実行器"""

    def __init__(
        self,
        output_dir: Path,
        hermes_home: Path,
        policy: SafeAutoPolicy | None = None,
        generator: SkillGenerator | None = None,
        installer: SkillInstaller | None = None,
    ):
        self.output_dir = Path(output_dir)
        self.hermes_home = Path(hermes_home).expanduser()
        self.policy = policy or SafeAutoPolicy()
        self.generator = generator or SkillGenerator(self.output_dir)
        self.installer = installer or SkillInstaller(self.hermes_home)
        self.auditor = SafetyAuditor()
        self.risk_scorer = RiskScorer()

    def run(self, skills: Iterable[SkillDefinition], judge_score: float) -> List[SafeAutoDecision]:
        decisions: List[SafeAutoDecision] = []
        review_dir = self.output_dir / "review"
        rejected_dir = self.output_dir / "rejected"

        for skill in skills:
            text = "\n".join([skill.name, skill.description, "\n".join(skill.patterns), " ".join(skill.tags)])
            safety = self.auditor.audit_text(text)
            risk = self.risk_scorer.score_text(text)
            decision = self.policy.decide(skill, judge_score, risk.score, safety.is_safe)
            decisions.append(decision)

            if decision.action == "auto_install":
                generated = self.generator.generate(skill, self.output_dir / "auto")
                self.installer.install_file(generated)
            elif decision.action == "review":
                self.generator.generate(skill, review_dir)
            else:
                self.generator.generate(skill, rejected_dir)

        self._write_manifest(decisions)
        return decisions

    def _write_manifest(self, decisions: List[SafeAutoDecision]) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        counts = {"auto_install": 0, "review": 0, "reject": 0}
        for decision in decisions:
            counts[decision.action] = counts.get(decision.action, 0) + 1
        payload = {
            **counts,
            "decisions": [decision.__dict__ for decision in decisions],
            "policy": {
                "auto_threshold": self.policy.auto_threshold,
                "review_threshold": self.policy.review_threshold,
            },
        }
        path = self.output_dir / "safe-auto-manifest.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return path
