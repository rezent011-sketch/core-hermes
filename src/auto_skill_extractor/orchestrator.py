"""Core Hermes v2.0 - orchestrator

安全性を優先して、今やるべき改善アクションを決める軽量オーケストレーター。
外部副作用は持たず、判断と次手順だけを返す。
"""
from pathlib import Path

from .models import ExtractionResult, OrchestratorAction, OrchestratorDecision


class CoreHermesOrchestrator:
    """抽出結果・出力状態から次の安全なアクションを判断"""

    def decide(
        self,
        result: ExtractionResult | None = None,
        output_dir: Path | None = None,
        reviewed: bool = False,
    ) -> OrchestratorDecision:
        if result and result.errors:
            return OrchestratorDecision(
                action=OrchestratorAction.IDLE,
                reason="Errors detected; manual review required before automation",
                confidence=0.9,
                next_steps=["Inspect result.errors", "Fix generator/validator issues", "Re-run with --dry-run"],
            )

        if result and result.memory_candidates and not reviewed:
            return OrchestratorDecision(
                action=OrchestratorAction.REVIEW_MEMORIES,
                reason="Memory candidates found but not reviewed",
                confidence=0.86,
                next_steps=["Run with --memory-review", "Approve only durable non-sensitive facts"],
            )

        if result and result.skills_extracted > 0 and not reviewed:
            return OrchestratorDecision(
                action=OrchestratorAction.EXTRACT_SKILLS,
                reason="Quality skill candidates exist and should be reviewed before install",
                confidence=0.82,
                next_steps=["Review generated markdown", "Run --install-from only after manual approval"],
            )

        if output_dir and output_dir.exists() and list(output_dir.rglob("*.md")):
            return OrchestratorDecision(
                action=OrchestratorAction.ENHANCE_CONTEXT,
                reason="Reviewed skill files are available for context enhancement",
                confidence=0.75,
                next_steps=["Use --context-query for task-specific context", "Keep install manual"],
            )

        return OrchestratorDecision(
            action=OrchestratorAction.IDLE,
            reason="No actionable candidates found",
            confidence=0.7,
            next_steps=["Collect more sessions", "Lower thresholds only for dry-run analysis"],
        )
