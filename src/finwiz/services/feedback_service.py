"""
A+ Investment Feedback and Learning Service.

This service implements the feedback loop system for A+ investment recommendations,
collecting user feedback, tracking performance outcomes, and using machine learning
to continuously improve the discovery criteria.

DEPRECATED: This module has been refactored into a modular package.
Use: from finwiz.services.feedback import FeedbackLearningService, get_feedback_service
"""

# Re-export the new modular implementation for backward compatibility
from finwiz.services.feedback import FeedbackLearningService, get_feedback_service

__all__ = ["FeedbackLearningService", "get_feedback_service"]
