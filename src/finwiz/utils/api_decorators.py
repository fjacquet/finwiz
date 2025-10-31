"""
Decorators and utilities for API rate limiting and error handling.

This module provides decorators to easily add rate limiting, retry logic,
and error handling to existing API tools without modifying their core logic.
"""

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar

from finwiz.tools.logger import get_logger
from finwiz.utils.rate_limiter import APIProvider, with_rate_limit

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def rate_limited(provider: APIProvider, endpoint: str = "", timeout: float = 30.0) -> Callable[[F], F]:
    """
    Add rate limiting to API functions.

    Args:
        provider: API provider for rate limiting
        endpoint: Specific endpoint being called
        timeout: Request timeout in seconds

    Returns:
        Decorated function with rate limiting

    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            return await with_rate_limit(provider, func, *args, endpoint=endpoint, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, run in event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(with_rate_limit(provider, func, *args, endpoint=endpoint, **kwargs))

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def api_error_handler(default_return: Any = None, log_errors: bool = True, reraise: bool = False) -> Callable[[F], F]:
    """
    Add consistent error handling to API functions.

    Args:
        default_return: Value to return on error (if not reraising)
        log_errors: Whether to log errors
        reraise: Whether to reraise exceptions after logging

    Returns:
        Decorated function with error handling

    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")

                if reraise:
                    raise

                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {e}")

                if reraise:
                    raise

                return default_return

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def timeout_handler(timeout_seconds: float = 30.0) -> Callable[[F], F]:
    """
    Add timeout handling to functions.

    Args:
        timeout_seconds: Timeout in seconds

    Returns:
        Decorated function with timeout handling

    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except TimeoutError:
                logger.warning(f"Timeout in {func.__name__} after {timeout_seconds}s")
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, we can't easily add timeout without threading
            # Just call the function normally and let underlying libraries handle timeouts
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def api_tool(provider: APIProvider, endpoint: str = "", timeout: float = 30.0, default_return: Any = None, log_errors: bool = True) -> Callable[[F], F]:
    """
    Comprehensive decorator combining rate limiting, error handling, and timeout.

    Args:
        provider: API provider for rate limiting
        endpoint: Specific endpoint being called
        timeout: Request timeout in seconds
        default_return: Value to return on error
        log_errors: Whether to log errors

    Returns:
        Decorated function with comprehensive API handling

    """

    def decorator(func: F) -> F:
        # Apply decorators in order: timeout -> error handling -> rate limiting
        decorated = func
        decorated = timeout_handler(timeout)(decorated)
        decorated = api_error_handler(default_return, log_errors, reraise=True)(decorated)
        decorated = rate_limited(provider, endpoint, timeout)(decorated)
        return decorated

    return decorator


class APICallContext:
    """Context manager for API calls with automatic rate limiting and error handling."""

    def __init__(self, provider: APIProvider, endpoint: str = "", timeout: float = 30.0, log_calls: bool = True) -> None:
        """Initialize API call context manager."""
        self.provider = provider
        self.endpoint = endpoint
        self.timeout = timeout
        self.log_calls = log_calls
        self.start_time: float | None = None

    async def __aenter__(self) -> "APICallContext":
        """Enter the context and acquire rate limit permission."""
        import time

        from finwiz.utils.rate_limiter import get_rate_limiter

        limiter = get_rate_limiter()
        await limiter.wait_for_availability(self.provider, self.endpoint)

        self.start_time = time.time()
        if self.log_calls:
            logger.debug(f"Starting API call to {self.provider} {self.endpoint}")

        return self

    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        """Exit the context and log call completion."""
        if self.start_time and self.log_calls:
            import time

            duration = time.time() - self.start_time

            if exc_type:
                logger.warning(f"API call to {self.provider} {self.endpoint} failed after {duration:.2f}s: {exc_val}")
            else:
                logger.debug(f"API call to {self.provider} {self.endpoint} completed in {duration:.2f}s")

        return False  # Don't suppress exceptions


# Utility functions for common API patterns


async def safe_api_call(provider: APIProvider, func: Callable, *args: Any, endpoint: str = "", default_return: Any = None, **kwargs: Any) -> Any:
    """
    Make a safe API call with rate limiting and error handling.

    Args:
        provider: API provider for rate limiting
        func: Function to call
        *args: Positional arguments for the function
        endpoint: Specific endpoint
        default_return: Value to return on error
        **kwargs: Keyword arguments for the function

    Returns:
        Function result or default_return on error

    """
    try:
        return await with_rate_limit(provider, func, *args, endpoint=endpoint, **kwargs)
    except Exception as e:
        logger.error(f"API call failed for {provider} {endpoint}: {e}")
        return default_return


def get_api_stats() -> dict:
    """Get statistics for all API providers."""
    from finwiz.utils.rate_limiter import get_rate_limiter

    limiter = get_rate_limiter()
    stats = {}

    for provider in APIProvider:
        stats[provider.value] = limiter.get_stats(provider)

    return stats
