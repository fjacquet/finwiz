"""
LiteLLM callback for monitoring prompt sizes.

This module provides a callback that logs the size of prompts being sent to LLMs,
helping diagnose token overflow issues.
"""

import contextvars
from typing import Any

import litellm
from litellm.integrations.custom_logger import CustomLogger

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Crew attribution context — set before crew.kickoff(), cleared after
_current_crew_name: contextvars.ContextVar[str] = contextvars.ContextVar("_current_crew_name", default="unknown")


def set_crew_context(crew_name: str) -> None:
    """Set the current crew name for LLM call attribution."""
    _current_crew_name.set(crew_name)


def clear_crew_context() -> None:
    """Clear crew attribution context."""
    _current_crew_name.set("unknown")


class TokenMonitorCallback(CustomLogger):
    """
    LiteLLM callback to monitor token usage and prompt sizes.

    Logs the size of messages being sent to help diagnose token overflow.
    """

    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.total_cost: float = 0.0
        self.crew_costs: dict[str, float] = {}
        self.crew_tokens: dict[str, dict[str, int]] = {}
        self.crew_calls: dict[str, int] = {}

    def log_success_event(self, kwargs: dict, response_obj: Any, start_time: float, end_time: float) -> None:
        """Called after successful LLM call. Tracks cost and crew attribution."""
        self.call_count += 1
        usage = getattr(response_obj, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

        # Calculate cost
        cost = 0.0
        try:
            cost = litellm.completion_cost(completion_response=response_obj)
        except Exception:
            pass  # Cost calculation not available for all models

        # Crew attribution via contextvars
        crew_name = _current_crew_name.get("unknown")
        self.total_cost += cost
        self.crew_costs[crew_name] = self.crew_costs.get(crew_name, 0.0) + cost
        self.crew_calls[crew_name] = self.crew_calls.get(crew_name, 0) + 1
        if crew_name not in self.crew_tokens:
            self.crew_tokens[crew_name] = {"prompt": 0, "completion": 0}
        self.crew_tokens[crew_name]["prompt"] += prompt_tokens
        self.crew_tokens[crew_name]["completion"] += completion_tokens

        model = kwargs.get("model", "unknown")
        logger.info(f"LLM call #{self.call_count} ({crew_name}): {model} cost=${cost:.4f} ({prompt_tokens}+{completion_tokens} tokens)")

    def get_cost_summary(self) -> dict[str, Any]:
        """Get aggregated cost summary for all crews."""
        per_crew: dict[str, dict[str, Any]] = {}
        for crew_name in set(list(self.crew_costs.keys()) + list(self.crew_tokens.keys())):
            tokens = self.crew_tokens.get(crew_name, {"prompt": 0, "completion": 0})
            per_crew[crew_name] = {
                "cost": self.crew_costs.get(crew_name, 0.0),
                "calls": self.crew_calls.get(crew_name, 0),
                "tokens": tokens,
            }
        return {
            "total_cost": self.total_cost,
            "call_count": self.call_count,
            "per_crew": per_crew,
        }

    def log_cost_summary(self) -> None:
        """Log a formatted LLM cost summary."""
        summary = self.get_cost_summary()
        if summary["call_count"] == 0:
            logger.info("LLM Cost Summary: No LLM calls made")
            return

        lines = ["LLM Cost Summary:"]
        for crew_name, data in summary["per_crew"].items():
            total_tokens = data["tokens"]["prompt"] + data["tokens"]["completion"]
            lines.append(f"  {crew_name}: ${data['cost']:.4f} ({data['calls']} calls, {total_tokens} tokens)")
        lines.append(f"  TOTAL: ${summary['total_cost']:.4f} ({summary['call_count']} calls)")
        logger.info("\n".join(lines))


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


def get_token_monitor() -> TokenMonitorCallback | None:
    """Get the global token monitor instance (or None if not enabled)."""
    return _token_monitor
