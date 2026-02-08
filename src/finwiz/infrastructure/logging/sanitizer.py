"""Log sanitization filter for sensitive data.

Attaches to logging handlers to redact API keys, tokens, and credentials
from log output — even if code accidentally logs a secret value.
"""

import logging
import os
import re

# Environment variables whose values should be redacted from logs
_SENSITIVE_ENV_VARS: list[str] = [
    "OPENAI_API_KEY",
    "SERPER_API_KEY",
    "PPLX_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "TWELVE_DATA_API_KEY",
    "X-CMC_PRO_API_KEY",
    "SEC_API_API_KEY",
    "CHART_IMG_API_KEY",
    "FIRECRAWL_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "KRAKEN_API_KEY",
    "KRAKEN_API_SECRET",
]

# Regex patterns for common key formats (sk-..., pplx-..., Bearer tokens, etc.)
_KEY_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"pplx-[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
]

_REDACTED = "***REDACTED***"


def _build_literal_patterns() -> list[tuple[str, str]]:
    """Build literal replacement pairs from current env var values."""
    pairs: list[tuple[str, str]] = []
    for var in _SENSITIVE_ENV_VARS:
        value = os.getenv(var)
        if value and len(value) >= 8:
            pairs.append((value, _REDACTED))
    return pairs


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts known API keys and token patterns."""

    def __init__(self) -> None:
        super().__init__()
        self._literal_pairs = _build_literal_patterns()

    def refresh_patterns(self) -> None:
        """Rebuild literal patterns (call after env vars change, e.g. in tests)."""
        self._literal_pairs = _build_literal_patterns()

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from the log record. Always returns True."""
        record.msg = self._redact(str(record.msg))
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._redact(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            else:
                record.args = tuple(self._redact(str(a)) if isinstance(a, str) else a for a in record.args)
        return True

    def _redact(self, text: str) -> str:
        """Replace known secrets and key patterns with redaction marker."""
        for secret, replacement in self._literal_pairs:
            text = text.replace(secret, replacement)
        for pattern in _KEY_PATTERNS:
            text = pattern.sub(_REDACTED, text)
        return text
