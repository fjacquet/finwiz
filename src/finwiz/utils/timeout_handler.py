"""
Timeout management utilities for async operations.

Provides timeout enforcement for async operations with both strict and graceful variants.
"""

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


async def with_timeout[T](coro: Callable[..., Coroutine[Any, Any, T]], timeout_seconds: int, operation_name: str, **kwargs: Any) -> T:
    """
    Execute coroutine with timeout enforcement.

    Args:
        coro: Async function to execute
        timeout_seconds: Timeout in seconds
        operation_name: Name for logging purposes
        **kwargs: Arguments to pass to coro

    Returns:
        Result from coroutine

    Raises:
        TimeoutError: If timeout is exceeded

    Example:
        result = await with_timeout(
            fetch_data,
            timeout_seconds=30,
            operation_name="Fetch stock data",
            ticker="AAPL"
        )

    """
    try:
        logger.debug(f"Starting {operation_name} with {timeout_seconds}s timeout")
        result = await asyncio.wait_for(coro(**kwargs), timeout=timeout_seconds)
        logger.debug(f"Completed {operation_name} within timeout")
        return result
    except TimeoutError:
        logger.error(f"Timeout: {operation_name} exceeded {timeout_seconds}s timeout")
        raise


async def with_timeout_graceful[T](
    coro: Callable[..., Coroutine[Any, Any, T]],
    timeout_seconds: int,
    operation_name: str,
    fallback_value: Any = None,
    **kwargs: Any,
) -> T | Any:
    """
    Execute coroutine with timeout and graceful fallback.

    Args:
        coro: Async function to execute
        timeout_seconds: Timeout in seconds
        operation_name: Name for logging purposes
        fallback_value: Value to return on timeout (default: None)
        **kwargs: Arguments to pass to coro

    Returns:
        Result from coroutine or fallback_value on timeout

    Example:
        result = await with_timeout_graceful(
            fetch_data,
            timeout_seconds=30,
            operation_name="Fetch stock data",
            fallback_value={},
            ticker="AAPL"
        )

    """
    try:
        return await with_timeout(coro, timeout_seconds, operation_name, **kwargs)
    except TimeoutError:
        logger.warning(f"Timeout: {operation_name} - returning fallback value")
        return fallback_value
