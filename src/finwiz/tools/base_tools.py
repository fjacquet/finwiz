"""
Base classes for FinWiz tools with async support.

This module provides base classes that handle common patterns for async tools,
particularly the event loop handling required for tools that need to run async
operations in both sync and async contexts.
"""

import asyncio
from abc import abstractmethod
from typing import Any

from crewai.tools import BaseTool


class AsyncFeedbackTool(BaseTool):
    """
    Base class for async feedback tools.

    This class provides a standard pattern for tools that need to run async
    operations. It handles event loop detection and applies nest_asyncio when
    needed to support running async code in contexts where an event loop is
    already running (e.g., Jupyter notebooks, some async frameworks).

    Subclasses must implement the `_arun()` method with their async logic.
    The `_run()` method is provided and handles the sync-to-async bridge.

    Example:
        ```python
        class MyAsyncTool(AsyncFeedbackTool):
            name: str = "my_async_tool"
            description: str = "Does something async"

            async def _arun(self, **kwargs: Any) -> dict[str, Any]:
                # Implement async logic here
                result = await some_async_operation()
                return {"success": True, "result": result}
        ```

    """

    def _run(self, **kwargs: Any) -> dict[str, Any]:
        """
        Run the tool synchronously by bridging to async implementation.

        This method detects whether an event loop is already running and
        handles the async execution appropriately:
        - If no loop is running: Uses asyncio.run()
        - If loop is running: Applies nest_asyncio and uses asyncio.run()

        Args:
            **kwargs: Tool-specific arguments passed to _arun()

        Returns:
            dict[str, Any]: Result from the async implementation

        Note:
            This method should not be overridden by subclasses. Instead,
            implement the async logic in _arun().

        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(self._arun(**kwargs))
        else:
            # Event loop already running, use nest_asyncio
            import nest_asyncio

            nest_asyncio.apply()
            return asyncio.run(self._arun(**kwargs))

    @abstractmethod
    async def _arun(self, **kwargs: Any) -> dict[str, Any]:
        """
        Async implementation of the tool logic.

        Subclasses must implement this method with their async operations.

        Args:
            **kwargs: Tool-specific arguments

        Returns:
            dict[str, Any]: Tool execution result with at minimum:
                - success (bool): Whether the operation succeeded
                - message (str): Human-readable result message
                - error (str, optional): Error message if success is False

        Raises:
            NotImplementedError: If subclass doesn't implement this method

        """
        raise NotImplementedError("Subclasses must implement _arun()")
