"""
Background task management utilities for async operations.

Provides task queue management, monitoring, error tracking, and graceful
shutdown handling for non-blocking database operations.
"""

import asyncio
import logging
from collections.abc import Awaitable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a background task."""

    PENDING = "pending"  # Task created but not started
    RUNNING = "running"  # Task currently executing
    COMPLETED = "completed"  # Task completed successfully
    FAILED = "failed"  # Task failed with error
    CANCELLED = "cancelled"  # Task was cancelled


@dataclass
class BackgroundTask:
    """
    Represents a background task with metadata.

    Tracks task execution status, timing, and error information
    for monitoring and debugging.
    """

    task_id: str
    name: str
    created_at: datetime
    status: TaskStatus = TaskStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    result: Any = None
    _task: asyncio.Task[Any] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Ensure created_at uses UTC timezone."""
        from finwiz.utils.datetime_utils import ensure_utc_aware

        object.__setattr__(self, "created_at", ensure_utc_aware(self.created_at))

    @property
    def duration(self) -> float | None:
        """Get task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_done(self) -> bool:
        """Check if task is in terminal state."""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)


class BackgroundTaskManager:
    """
    Manages background tasks with monitoring and graceful shutdown.

    Provides:
    - Task queue management
    - Task monitoring and status tracking
    - Error tracking and logging
    - Graceful shutdown with pending task handling
    - Task statistics and metrics

    """

    def __init__(self, max_concurrent_tasks: int = 10) -> None:
        """
        Initialize background task manager.

        Args:
            max_concurrent_tasks: Maximum number of concurrent tasks (default: 10)

        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: dict[str, BackgroundTask] = {}
        self._task_counter = 0
        self._shutdown_event = asyncio.Event()
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

        logger.info(f"BackgroundTaskManager initialized (max_concurrent: {max_concurrent_tasks})")

    def create_task(
        self,
        coro: Awaitable[Any],
        name: str | None = None,
    ) -> str:
        """
        Create and schedule a background task.

        Args:
            coro: Coroutine to execute
            name: Optional task name for identification

        Returns:
            Task ID for tracking

        """
        # Generate task ID
        self._task_counter += 1
        task_id = f"task_{self._task_counter}"

        # Generate task name
        if name is None:
            name = f"background_task_{self._task_counter}"

        # Create task metadata
        bg_task = BackgroundTask(
            task_id=task_id,
            name=name,
            created_at=datetime.now(UTC),
        )

        # Wrap coroutine with monitoring
        wrapped_coro = self._wrap_task(bg_task, coro)

        # Create asyncio task
        task = asyncio.create_task(wrapped_coro)
        bg_task._task = task

        # Store task
        self.tasks[task_id] = bg_task

        logger.debug(f"Created background task: {task_id} ({name})")

        return task_id

    async def _wrap_task(
        self,
        bg_task: BackgroundTask,
        coro: Awaitable[Any],
    ) -> None:
        """
        Wrap task execution with monitoring and error handling.

        Args:
            bg_task: BackgroundTask metadata
            coro: Coroutine to execute

        """
        # Acquire semaphore to limit concurrency
        async with self._semaphore:
            # Check if shutdown requested
            if self._shutdown_event.is_set():
                bg_task.status = TaskStatus.CANCELLED
                logger.warning(f"Task {bg_task.task_id} cancelled due to shutdown")
                return

            # Update status to running
            bg_task.status = TaskStatus.RUNNING
            bg_task.started_at = datetime.now(UTC)

            logger.debug(f"Starting task: {bg_task.task_id} ({bg_task.name})")

            try:
                # Execute coroutine
                result = await coro

                # Update status to completed
                bg_task.status = TaskStatus.COMPLETED
                bg_task.completed_at = datetime.now(UTC)
                bg_task.result = result

                logger.debug(f"Task completed: {bg_task.task_id} ({bg_task.name}) in {bg_task.duration:.2f}s")

            except asyncio.CancelledError:
                # Task was cancelled
                bg_task.status = TaskStatus.CANCELLED
                bg_task.completed_at = datetime.now(UTC)

                logger.warning(f"Task cancelled: {bg_task.task_id} ({bg_task.name})")
                raise

            except Exception as e:
                # Task failed with error
                bg_task.status = TaskStatus.FAILED
                bg_task.completed_at = datetime.now(UTC)
                bg_task.error = str(e)

                logger.error(
                    f"Task failed: {bg_task.task_id} ({bg_task.name}) - {e}",
                    exc_info=True,
                )

    def get_task(self, task_id: str) -> BackgroundTask | None:
        """
        Get task by ID.

        Args:
            task_id: Task identifier

        Returns:
            BackgroundTask if found, None otherwise

        """
        return self.tasks.get(task_id)

    def get_pending_tasks(self) -> list[BackgroundTask]:
        """Get all pending tasks."""
        return [task for task in self.tasks.values() if not task.is_done]

    def get_completed_tasks(self) -> list[BackgroundTask]:
        """Get all completed tasks."""
        return [task for task in self.tasks.values() if task.status == TaskStatus.COMPLETED]

    def get_failed_tasks(self) -> list[BackgroundTask]:
        """Get all failed tasks."""
        return [task for task in self.tasks.values() if task.status == TaskStatus.FAILED]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get task statistics.

        Returns:
            Dictionary with task counts, success rate, and timing metrics

        """
        total = len(self.tasks)
        pending = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        running = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        completed = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        failed = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        cancelled = len([t for t in self.tasks.values() if t.status == TaskStatus.CANCELLED])

        # Calculate success rate
        finished = completed + failed
        success_rate = (completed / finished * 100) if finished > 0 else 0.0

        # Calculate average duration for completed tasks
        completed_tasks = self.get_completed_tasks()
        durations = [t.duration for t in completed_tasks if t.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total_tasks": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "success_rate": success_rate,
            "average_duration": avg_duration,
        }

    async def shutdown(self, timeout: float = 30.0) -> None:
        """
        Gracefully shutdown task manager.

        Waits for pending tasks to complete or cancels them after timeout.

        Args:
            timeout: Maximum time to wait for tasks (default: 30.0 seconds)

        """
        logger.info("Initiating graceful shutdown of background task manager")

        # Set shutdown event to prevent new tasks
        self._shutdown_event.set()

        # Get pending tasks
        pending_tasks = self.get_pending_tasks()

        if not pending_tasks:
            logger.info("No pending tasks, shutdown complete")
            return

        logger.info(f"Waiting for {len(pending_tasks)} pending tasks (timeout: {timeout}s)")

        # Wait for tasks with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(
                    *[t._task for t in pending_tasks if t._task],
                    return_exceptions=True,
                ),
                timeout=timeout,
            )
            logger.info("All pending tasks completed")

        except TimeoutError:
            # Timeout reached, cancel remaining tasks
            still_pending = self.get_pending_tasks()
            logger.warning(f"Timeout reached, cancelling {len(still_pending)} remaining tasks")

            for task in still_pending:
                if task._task and not task._task.done():
                    task._task.cancel()

            # Wait briefly for cancellations
            await asyncio.sleep(0.1)

        # Log final statistics
        stats = self.get_statistics()
        logger.info(f"Shutdown complete. Final stats: {stats}")

    def clear_completed_tasks(self, keep_recent: int = 100) -> int:
        """
        Clear completed tasks from memory.

        Keeps only the most recent completed tasks to prevent memory growth.

        Args:
            keep_recent: Number of recent completed tasks to keep (default: 100)

        Returns:
            Number of tasks cleared

        """
        completed = self.get_completed_tasks()

        if len(completed) <= keep_recent:
            return 0

        # Sort by completion time (most recent first)
        completed.sort(key=lambda t: t.completed_at or datetime.min, reverse=True)

        # Remove old completed tasks
        to_remove = completed[keep_recent:]
        for task in to_remove:
            del self.tasks[task.task_id]

        logger.debug(f"Cleared {len(to_remove)} old completed tasks")

        return len(to_remove)


# Global task manager instance
_global_task_manager: BackgroundTaskManager | None = None


def get_task_manager() -> BackgroundTaskManager:
    """
    Get global task manager instance.

    Creates instance on first call (singleton pattern).

    Returns:
        Global BackgroundTaskManager instance

    """
    global _global_task_manager

    if _global_task_manager is None:
        _global_task_manager = BackgroundTaskManager()

    return _global_task_manager


def create_background_task(
    coro: Awaitable[Any],
    name: str | None = None,
) -> str:
    """
    Create a background task using the global task manager.

    Convenience function for creating background tasks without
    managing a BackgroundTaskManager instance.

    Args:
        coro: Coroutine to execute
        name: Optional task name for identification

    Returns:
        Task ID for tracking

    """
    manager = get_task_manager()
    return manager.create_task(coro, name=name)


async def shutdown_task_manager(timeout: float = 30.0) -> None:
    """
    Shutdown global task manager.

    Args:
        timeout: Maximum time to wait for tasks (default: 30.0 seconds)

    """
    global _global_task_manager

    if _global_task_manager is not None:
        await _global_task_manager.shutdown(timeout=timeout)
        _global_task_manager = None
