"""安全監査: サニタイズ漏れを検出する"""
from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Iterable, List


@dataclass
class SafetyFinding:
    kind: str
    sample: str


@dataclass
class SafetyAuditResult:
    is_safe: bool
    findings: List[SafetyFinding] = field(default_factory=list)


class SafetyAuditor:
    """秘密情報・PIIの残存を検出する軽量監査"""

    PATTERNS = [
        ("api_key", re.compile(r"sk-[A-Za-z0-9_\-]{20,}")),
        ("github_token", re.compile(r"gh[oprsu]_[A-Za-z0-9_]{20,}")),
        ("telegram_token", re.compile(r"\b\d{8,12}:[A-Za-z0-9_\-]{30,}\b")),
        ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b")),
        ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
        ("numeric_id", re.compile(r"\b\d{8,12}\b")),
        ("key_value_secret", re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|authorization)\s*[:=]\s*(?!\[SECRET\])[^\s'\"]+")),
    ]

    def audit_text(self, text: str) -> SafetyAuditResult:
        findings: List[SafetyFinding] = []
        text = text or ""
        for kind, pattern in self.PATTERNS:
            for match in pattern.finditer(text):
                findings.append(SafetyFinding(kind=kind, sample=match.group(0)[:80]))
        return SafetyAuditResult(is_safe=not findings, findings=findings)

    def audit_files(self, paths: Iterable[Path]) -> SafetyAuditResult:
        findings: List[SafetyFinding] = []
        for path in paths:
            try:
                text = Path(path).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            result = self.audit_text(text)
            findings.extend(SafetyFinding(kind=f"{path}:{f.kind}", sample=f.sample) for f in result.findings)
        return SafetyAuditResult(is_safe=not findings, findings=findings)
