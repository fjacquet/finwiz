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


# OpenRouter model ids are not in litellm's price table, but the vendor-native
# id usually is (`openrouter/google/gemini-3.7-flash` → `gemini/gemini-3.7-flash`).
# Pricing through the twin is a proxy — OpenRouter's rate is not necessarily the
# vendor's — so a hit through this map is logged as an estimate, once per model.
# Only vendors listed here are tried; an unknown vendor stays honestly unpriced.
_OPENROUTER_NATIVE_PREFIX: dict[str, str] = {"google": "gemini"}


def _price_candidates(model: str) -> list[str]:
    """Return the model ids to try for pricing, most faithful first."""
    candidates = [model]
    parts = model.split("/", 2)
    if len(parts) == 3 and parts[0] == "openrouter" and parts[1] in _OPENROUTER_NATIVE_PREFIX:
        candidates.append(f"{_OPENROUTER_NATIVE_PREFIX[parts[1]]}/{parts[2]}")
    return candidates


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
        # Per-crew flag: False once any kickoff for that crew had tokens we could
        # not price (unknown/unpriced model). Lets the summary show "cost n/a"
        # instead of implying $0 — honesty over a false zero.
        self.crew_cost_known: dict[str, bool] = {}
        # Proxy model ids already announced in the log — one line per model, not per kickoff.
        self._priced_via_proxy: set[str] = set()

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

    def record_usage(self, crew_name: str, token_usage: Any, model: str | None = None) -> None:
        """Record authoritative CrewAI usage metrics for one crew kickoff.

        This is the source of truth for the cost summary. CrewAI populates
        ``CrewOutput.token_usage`` directly, which survives thread boundaries and
        CrewAI's own clobbering of ``litellm.callbacks`` (the reason
        ``log_success_event`` never fires for crews). Cost is an ESTIMATE derived
        from token counts and the crew's model via litellm pricing; when the
        model is unknown/unpriced we count tokens but mark cost unknown rather
        than recording a misleading $0.

        Args:
            crew_name: Crew attribution key (e.g. ``deep_analysis_stock``).
            token_usage: CrewAI ``UsageMetrics`` (``prompt_tokens``,
                ``completion_tokens``, ``successful_requests``).
            model: litellm model id for price lookup (e.g. ``openai/gpt-4o-mini``).
        """
        prompt_tokens = int(getattr(token_usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(token_usage, "completion_tokens", 0) or 0)
        requests = int(getattr(token_usage, "successful_requests", 0) or 0)
        if prompt_tokens == 0 and completion_tokens == 0 and requests == 0:
            return  # nothing measurable (empty/cached-only result) — don't fabricate a call

        calls = requests if requests > 0 else 1

        cost: float | None = None
        if model:
            for candidate in _price_candidates(model):
                try:
                    prompt_cost, completion_cost = litellm.cost_per_token(
                        model=candidate,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                    )
                except Exception as exc:
                    # Expected for an unpriced id: try the next candidate, or stay honestly unknown.
                    logger.debug(f"No litellm price for {candidate}: {exc}")
                    continue
                cost = float(prompt_cost) + float(completion_cost)
                if candidate != model and candidate not in self._priced_via_proxy:
                    self._priced_via_proxy.add(candidate)
                    logger.info(f"Pricing {model} via {candidate}: OpenRouter's rate may differ from the vendor's, so this cost is an estimate")
                break

        self.call_count += calls
        self.crew_calls[crew_name] = self.crew_calls.get(crew_name, 0) + calls
        if crew_name not in self.crew_tokens:
            self.crew_tokens[crew_name] = {"prompt": 0, "completion": 0}
        self.crew_tokens[crew_name]["prompt"] += prompt_tokens
        self.crew_tokens[crew_name]["completion"] += completion_tokens

        # A crew's cost is "known" only if every kickoff for it could be priced.
        self.crew_cost_known[crew_name] = self.crew_cost_known.get(crew_name, True) and (cost is not None)
        if cost is not None:
            self.crew_costs[crew_name] = self.crew_costs.get(crew_name, 0.0) + cost
            self.total_cost += cost

        cost_str = f"${cost:.4f}" if cost is not None else "cost n/a"
        logger.debug(f"Recorded usage ({crew_name}): {calls} calls, {prompt_tokens}+{completion_tokens} tokens, {cost_str}")

    def get_cost_summary(self) -> dict[str, Any]:
        """Get aggregated cost summary for all crews."""
        per_crew: dict[str, dict[str, Any]] = {}
        for crew_name in set(list(self.crew_costs.keys()) + list(self.crew_tokens.keys())):
            tokens = self.crew_tokens.get(crew_name, {"prompt": 0, "completion": 0})
            per_crew[crew_name] = {
                "cost": self.crew_costs.get(crew_name, 0.0),
                "calls": self.crew_calls.get(crew_name, 0),
                "tokens": tokens,
                "cost_known": self.crew_cost_known.get(crew_name, True),
            }
        return {
            "total_cost": self.total_cost,
            "call_count": self.call_count,
            "per_crew": per_crew,
        }

    def log_cost_summary(self) -> None:
        """Log a formatted, honest LLM cost summary.

        Reports only what was actually measured. When nothing was measured it
        says so plainly — it does NOT claim "No LLM calls made" (crews may run
        outside the measured chokepoint, so an unmeasured run is not proof of
        zero usage). Dollar amounts are labelled estimates; crews whose model
        could not be priced show their tokens with "cost n/a" rather than $0.
        """
        summary = self.get_cost_summary()
        if summary["call_count"] == 0:
            logger.info("LLM Cost Summary: no crew LLM usage measured this run")
            return

        lines = ["LLM Cost Summary (estimated from CrewAI usage metrics):"]
        any_unpriced = False
        for crew_name, data in summary["per_crew"].items():
            total_tokens = data["tokens"]["prompt"] + data["tokens"]["completion"]
            if data.get("cost_known", True):
                cost_str = f"${data['cost']:.4f}"
            else:
                cost_str = "cost n/a (unpriced model)"
                any_unpriced = True
            lines.append(f"  {crew_name}: {cost_str} ({data['calls']} calls, {total_tokens} tokens)")
        lines.append(f"  TOTAL: ~${summary['total_cost']:.4f} estimated across {summary['call_count']} calls")
        if any_unpriced:
            lines.append("  (some crews used an unpriced model; their tokens are counted but cost is not)")
        logger.info("\n".join(lines))


# Global callback instance
_token_monitor: TokenMonitorCallback | None = None


def enable_token_monitoring() -> None:
    """Initialize the token monitor singleton.

    Cost/token data is recorded from CrewAI's authoritative
    ``CrewOutput.token_usage`` via :meth:`TokenMonitorCallback.record_usage` at
    the crew-execution chokepoint — NOT from a litellm callback. CrewAI clobbers
    ``litellm.callbacks`` when it lazily builds its own LLM at kickoff, so the
    callback never fired; registering it would also risk double-counting any
    crews where it *does* fire. We therefore only create the singleton here.
    """
    global _token_monitor

    if _token_monitor is not None:
        logger.debug("Token monitoring already enabled")
        return

    _token_monitor = TokenMonitorCallback()
    logger.info("🔍 Token monitoring enabled - recording CrewAI usage metrics per crew")


def get_token_monitor() -> TokenMonitorCallback | None:
    """Get the global token monitor instance (or None if not enabled)."""
    return _token_monitor
