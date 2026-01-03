"""
Session management system for persistent financial planning.

This module provides the SessionManager class for loading, parsing, and managing
financial planning sessions from HTML reports.
"""

# Import all classes and functions from the split modules for backward compatibility
from finwiz.sessions.persistence import SessionParsingError, SessionPersistence
from finwiz.sessions.state import SessionManager
from finwiz.sessions.validation import SessionValidator

# Re-export all classes for backward compatibility
__all__ = [
    "SessionManager",
    "SessionParsingError",
    "SessionPersistence",
    "SessionValidator",
]
