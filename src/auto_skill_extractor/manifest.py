"""実行マニフェスト生成"""
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import ExtractionResult


class ManifestWriter:
    """Raw content/pathを避けた機械可読マニフェストを生成"""

    def write(self, result: ExtractionResult, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.render(result)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def render(self, result: ExtractionResult) -> dict:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_messages": result.total_messages,
            "patterns_found": result.patterns_found,
            "skills_extracted": result.skills_extracted,
            "memory_candidates": len(result.memory_candidates),
            "errors": len(result.errors),
            "file_count": len(result.saved_files),
            "context_enhancement": result.context_enhancement is not None,
            "orchestrator_action": result.orchestrator_decision.action.value if result.orchestrator_decision else None,
        }
