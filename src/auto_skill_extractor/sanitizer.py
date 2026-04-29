"""秘密情報・PIIマスクモジュール"""
import re


class ContentSanitizer:
    """SKILL.md生成前に秘密情報とPIIをマスクする"""

    SECRET_PATTERNS = [
        # OpenAI / generic sk keys
        (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "[SECRET]"),
        # GitHub tokens
        (re.compile(r"gh[oprsu]_[A-Za-z0-9_]{20,}"), "[SECRET]"),
        # Telegram bot token
        (re.compile(r"\b\d{8,12}:[A-Za-z0-9_\-]{30,}\b"), "[SECRET]"),
        # JWT-like tokens
        (re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b"), "[SECRET]"),
        # AWS access key
        (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[SECRET]"),
    ]

    PII_PATTERNS = [
        # Email addresses
        (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
        # Telegram bot tokens: digits + colon + long alphanumeric
        (re.compile(r"\b\d{8,10}:[A-Za-z0-9_\-]{30,}\b"), "[SECRET]"),
        # Long numeric IDs only when preceded by context keywords (case-insensitive)
        # Matches patterns like "user_id: 1234567890" or "chat_id=1234567890"
        (re.compile(r"(?i)(?:user[_\-]?id|chat[_\-]?id|account[_\-]?id|telegram[_\-]?id)\s*[:=]?\s*(\d{9,13})\b"), lambda m: m.group(0).replace(m.group(1), "[ID]")),
    ]

    KEY_VALUE_PATTERNS = [
        re.compile(r"(?i)\b(api[_-]?key|token|secret|password|passwd|authorization)\s*[:=]\s*[^\s'\"]+"),
    ]

    def sanitize(self, text: str) -> str:
        """テキスト中の秘密情報・PIIをマスク"""
        if not text:
            return ""

        sanitized = str(text)

        for pattern in self.KEY_VALUE_PATTERNS:
            sanitized = pattern.sub(lambda m: f"{m.group(1)}=[SECRET]", sanitized)

        for pattern, replacement in self.SECRET_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)

        for pattern, replacement in self.PII_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)

        return sanitized
