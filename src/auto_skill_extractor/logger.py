"""構造化ログ出力モジュール

print() の代わりに JSON Lines 形式でログを出力する。
本番運用でのモニタリング・トラブルシューティング用。
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class StructuredLogger:
    """JSON Lines 形式の構造化ログを出力"""

    def __init__(self, log_path: Optional[Path] = None, level: str = "INFO"):
        self.log_path = Path(log_path) if log_path else None
        self.level = level.upper()
        self._levels = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}

    def _should_log(self, level: str) -> bool:
        return self._levels.get(level.upper(), 20) >= self._levels.get(self.level, 20)

    def _emit(self, entry: dict) -> None:
        line = json.dumps(entry, ensure_ascii=False, default=str)
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        # コンソールにも出力（互換性のため）
        print(line, file=sys.stderr)

    def debug(self, message: str, **kwargs) -> None:
        if self._should_log("DEBUG"):
            self._emit({"timestamp": datetime.now().isoformat(), "level": "DEBUG", "message": message, **kwargs})

    def info(self, message: str, **kwargs) -> None:
        if self._should_log("INFO"):
            self._emit({"timestamp": datetime.now().isoformat(), "level": "INFO", "message": message, **kwargs})

    def warning(self, message: str, **kwargs) -> None:
        if self._should_log("WARNING"):
            self._emit({"timestamp": datetime.now().isoformat(), "level": "WARNING", "message": message, **kwargs})

    def error(self, message: str, **kwargs) -> None:
        if self._should_log("ERROR"):
            self._emit({"timestamp": datetime.now().isoformat(), "level": "ERROR", "message": message, **kwargs})

    def extraction_start(self, db_path: str, output_dir: str, **kwargs) -> None:
        self.info("Extraction started", event="extraction_start", db_path=db_path, output_dir=output_dir, **kwargs)

    def extraction_complete(self, result: dict, **kwargs) -> None:
        self.info("Extraction complete", event="extraction_complete", **result, **kwargs)

    def skill_extracted(self, name: str, confidence: float, **kwargs) -> None:
        self.info(f"Skill extracted: {name}", event="skill_extracted", skill_name=name, confidence=confidence, **kwargs)

    def skill_installed(self, name: str, path: str, **kwargs) -> None:
        self.info(f"Skill installed: {name}", event="skill_installed", skill_name=name, path=path, **kwargs)

    def error_occurred(self, message: str, exc_info: bool = False, **kwargs) -> None:
        import traceback
        entry = {"timestamp": datetime.now().isoformat(), "level": "ERROR", "message": message, **kwargs}
        if exc_info:
            entry["traceback"] = traceback.format_exc()
        self._emit(entry)


# シングルトンインスタンス
_logger: Optional[StructuredLogger] = None


def get_logger(log_path: Optional[Path] = None, level: str = "INFO") -> StructuredLogger:
    global _logger
    if _logger is None:
        _logger = StructuredLogger(log_path=log_path, level=level)
    return _logger