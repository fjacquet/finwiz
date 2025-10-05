"""
Pytest plugin to block unittest.mock imports.

This ensures that no test accidentally uses unittest.mock instead of pytest-mock.
"""

import sys
from typing import Any


class UnittestMockBlocker:
    """Block unittest.mock imports and provide helpful error messages."""

    def find_module(self, fullname: str, path: Any = None) -> "UnittestMockBlocker | None":
        """Find module hook to intercept unittest.mock imports."""
        if fullname == "unittest.mock":
            return self
        return None

    def load_module(self, fullname: str) -> None:
        """Raise error when unittest.mock is imported."""
        raise ImportError(
            "\n\n"
            "❌ unittest.mock is BANNED in this project!\n"
            "\n"
            "✅ Use pytest-mock instead:\n"
            "   def test_example(mocker):\n"
            "       mock_obj = mocker.patch('module.function')\n"
            "       mock_obj.return_value = 'test'\n"
            "\n"
            "Common replacements:\n"
            "   - from unittest.mock import Mock → mocker.Mock()\n"
            "   - from unittest.mock import MagicMock → mocker.MagicMock()\n"
            "   - from unittest.mock import AsyncMock → mocker.AsyncMock()\n"
            "   - from unittest.mock import patch → mocker.patch()\n"
            "   - @patch('module.func') → mocker.patch('module.func')\n"
            "\n"
        )


# Install the import blocker
sys.meta_path.insert(0, UnittestMockBlocker())
