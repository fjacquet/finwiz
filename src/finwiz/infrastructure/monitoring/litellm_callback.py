"""
LiteLLM callback for monitoring prompt sizes.

This module provides a callback that logs the size of prompts being sent to LLMs,
helping diagnose token overflow issues.
"""

from typing import Any

import litellm
from litellm.integrations.custom_logger import CustomLogger

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class TokenMonitorCallback(CustomLogger):
    """
    LiteLLM callback to monitor token usage and prompt sizes.

    Logs the size of messages being sent to help diagnose token overflow.
    """

    def __init__(self):
        super().__init__()
        self.call_count = 0

    def log_pre_api_call(self, model: str, messages: list, kwargs: dict) -> None:
        """Called before each LLM API call."""
        self.call_count += 1

        # Calculate message sizes
        total_chars = 0
        msg_sizes = []

        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            if isinstance(content, str):
                size = len(content)
            elif isinstance(content, list):
                # Handle multi-part messages (vision, etc.)
                size = sum(len(str(part)) for part in content)
            else:
                size = len(str(content))

            total_chars += size
            msg_sizes.append(f"msg[{i}]:{size}")

        estimated_tokens = total_chars // 4

        # Log at different levels based on size
        if estimated_tokens > 100000:
            logger.error(
                f"🚨 TOKEN OVERFLOW ALERT: LLM call #{self.call_count} to {model}\n"
                f"   Total: {total_chars:,} chars (~{estimated_tokens:,} tokens)\n"
                f"   Messages: {len(messages)} ({', '.join(msg_sizes[:5])}{'...' if len(msg_sizes) > 5 else ''})"
            )
            # Log first message preview for debugging
            if messages:
                first_msg = str(messages[0].get("content", ""))[:500]
                logger.error(f"   First message preview: {first_msg}...")
        elif estimated_tokens > 50000:
            logger.warning(f"⚠️ HIGH TOKEN COUNT: LLM call #{self.call_count} to {model}: {total_chars:,} chars (~{estimated_tokens:,} tokens)")
        else:
            logger.debug(f"LLM call #{self.call_count} to {model}: {total_chars:,} chars (~{estimated_tokens:,} tokens)")

    def log_success_event(self, kwargs: dict, response_obj: Any, start_time: float, end_time: float) -> None:
        """Called after successful LLM call."""
        usage = getattr(response_obj, "usage", None)
        if usage:
            logger.info(
                f"✅ LLM call #{self.call_count} completed: prompt_tokens={getattr(usage, 'prompt_tokens', 'N/A')}, completion_tokens={getattr(usage, 'completion_tokens', 'N/A')}"
            )

    def log_failure_event(self, kwargs: dict, response_obj: Any, start_time: float, end_time: float) -> None:
        """Called after failed LLM call."""
        logger.error(f"❌ LLM call #{self.call_count} failed: {response_obj}")


# Global callback instance
_token_monitor: TokenMonitorCallback | None = None


def enable_token_monitoring() -> None:
    """Enable token monitoring for all LiteLLM calls."""
    global _token_monitor

    if _token_monitor is not None:
        logger.debug("Token monitoring already enabled")
        return

    _token_monitor = TokenMonitorCallback()
    litellm.callbacks = [_token_monitor]
    logger.info("🔍 Token monitoring enabled - will log all LLM prompt sizes")


def disable_token_monitoring() -> None:
    """Disable token monitoring."""
    global _token_monitor

    if _token_monitor is None:
        return

    litellm.callbacks = []
    _token_monitor = None
    logger.info("Token monitoring disabled")


def get_call_count() -> int:
    """Get the number of LLM calls made since monitoring was enabled."""
    if _token_monitor is None:
        return 0
    return _token_monitor.call_count
