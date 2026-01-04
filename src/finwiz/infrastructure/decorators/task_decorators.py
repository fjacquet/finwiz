"""
Task decorators for explicit async/sync execution configuration.

This module provides decorators to explicitly mark CrewAI tasks as async or sync,
ensuring consistent execution patterns and preventing common configuration errors.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any

from crewai import Task

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


def async_task(func: Callable) -> Callable:
    """
    Mark task for asynchronous execution.

    Automatically sets async_execution=True on the task after creation.
    Use this decorator for tasks that can run in parallel.

    Args:
        func: Task creation function to decorate

    Returns:
        Wrapped function that sets async_execution=True

    Example:
        @async_task
        @task
        def research_task(self) -> Task:
            return Task(config=self.tasks_config['research'])

    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Task:
        task: Task = func(*args, **kwargs)
        task.async_execution = True
        logger.debug(f"Task '{task.description[:50] if task.description else 'unnamed'}...' configured for async execution")
        return task

    # Copy CrewAI attributes from wrapped function to wrapper
    # This is essential for CrewAI's task discovery to work correctly
    if hasattr(func, "is_task"):
        wrapper.is_task = func.is_task  # type: ignore[attr-defined]

    return wrapper


def sync_task(func: Callable) -> Callable:
    """
    Mark task for synchronous execution.

    Explicitly sets async_execution=False on the task after creation.
    Use this decorator for final tasks that must run after all other tasks complete.

    Args:
        func: Task creation function to decorate

    Returns:
        Wrapped function that sets async_execution=False

    Example:
        @sync_task
        @task
        def final_report_task(self) -> Task:
            return Task(config=self.tasks_config['final_report'])

    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Task:
        task: Task = func(*args, **kwargs)
        task.async_execution = False
        logger.debug(f"Task '{task.description[:50] if task.description else 'unnamed'}...' configured for sync execution")
        return task

    # Copy CrewAI attributes from wrapped function to wrapper
    # This is essential for CrewAI's task discovery to work correctly
    if hasattr(func, "is_task"):
        wrapper.is_task = func.is_task  # type: ignore[attr-defined]

    return wrapper
