"""
Session management system for persistent financial planning.

This module provides the SessionManager class for loading, parsing, and managing
financial planning sessions from HTML reports.
"""

# Import all classes and functions from the split modules for backward compatibility
from finwiz.utils.session_persistence import SessionParsingError, SessionPersistence
from finwiz.utils.session_state import SessionManager
from finwiz.utils.session_validation import SessionValidator

# Re-export all classes for backward compatibility
__all__ = [
    "SessionManager",
    "SessionParsingError",
    "SessionPersistence",
    "SessionValidator",
]
