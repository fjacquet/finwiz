"""
Integration example for session management in FinWiz main application.

This module demonstrates how to integrate the session management system
into the main FinWiz workflow for persistent financial planning.
"""

from typing import Any

from finwiz.schemas.session import FinancialPlan
from finwiz.tools.logger import get_logger
from finwiz.utils.session_manager import SessionManager, SessionParsingError

logger = get_logger(__name__)


def initialize_session(report_path: str = "report/finwiz_family_financial_plan.html") -> FinancialPlan:
    """
    Initialize a financial planning session by loading existing or creating new.

    This function implements the session initialization logic as specified in
    requirement 9.1 and 9.2, handling both existing session loading and new
    session creation with proper error recovery.

    Args:
        report_path: Path to the HTML report file

    Returns:
        FinancialPlan instance (loaded or newly created)

    Raises:
        SessionParsingError: If session initialization fails completely

    """
    session_manager = SessionManager(report_path)

    try:
        # Try to load existing session first
        existing_plan = session_manager.load_existing_session()

        if existing_plan:
            logger.info("Successfully loaded existing financial plan session")
            logger.info(f"Plan ID: {existing_plan.plan_id}")
            logger.info(f"Client: {existing_plan.client_profile.name or 'Not specified'}")
            logger.info(f"Last updated: {existing_plan.last_updated}")
            return existing_plan
        else:
            # No existing session found, create new one
            logger.info("No existing session found, creating new financial plan")
            new_plan = session_manager.create_new_session()
            logger.info(f"Created new financial plan with ID: {new_plan.plan_id}")
            return new_plan

    except SessionParsingError as e:
        logger.error(f"Session loading failed: {str(e)}")
        logger.info("Attempting session recovery...")

        try:
            # Attempt recovery from corruption
            recovered_plan = session_manager.recover_corrupted_session()
            logger.info("Successfully recovered session from corruption")
            return recovered_plan

        except SessionParsingError as recovery_error:
            logger.error(f"Session recovery failed: {str(recovery_error)}")
            logger.info("Creating new session as fallback")

            # Last resort: create completely new session
            return session_manager.create_new_session()


def save_session_with_analysis_results(plan: FinancialPlan, analysis_results: dict, report_path: str = "report/finwiz_family_financial_plan.html") -> None:
    """
    Save session with new analysis results.

    Args:
        plan: FinancialPlan to update and save
        analysis_results: Dictionary containing analysis results from crews
        report_path: Path to save the HTML report

    Raises:
        SessionParsingError: If saving fails

    """
    session_manager = SessionManager(report_path)

    try:
        # Update plan with new analysis results
        if "portfolio_data" in analysis_results:
            plan.current_portfolio_data.update(analysis_results["portfolio_data"])

        if "recommendations" in analysis_results:
            plan.current_recommendations.update(analysis_results["recommendations"])

        # Save with backup
        session_manager.save_financial_plan(plan, backup=True)
        logger.info(f"Successfully saved session to {report_path}")

    except SessionParsingError as e:
        logger.error(f"Failed to save session: {str(e)}")
        raise


def get_session_summary(plan: FinancialPlan) -> dict[str, Any]:
    """
    Get a summary of the current session for logging/debugging.

    Args:
        plan: FinancialPlan to summarize

    Returns:
        Dictionary with session summary information

    """
    return {
        "plan_id": plan.plan_id,
        "created_at": plan.created_at.isoformat(),
        "last_updated": plan.last_updated.isoformat(),
        "client_name": plan.client_profile.name,
        "client_age": plan.client_profile.age,
        "analysis_count": len(plan.analysis_history),
        "has_portfolio_data": bool(plan.current_portfolio_data),
        "has_recommendations": bool(plan.current_recommendations),
        "report_language": plan.report_language,
        "version": plan.version,
    }


# Example usage in main.py integration
def integrate_with_main_flow() -> None:
    """
    Integrate session management with the main FinWiz flow.

    This would be called from the main FinWiz application to add session
    persistence to the existing workflow.
    """
    # Initialize session at the start of the workflow
    financial_plan = initialize_session()

    # Log session summary
    summary = get_session_summary(financial_plan)
    logger.info(f"Session initialized: {summary}")

    # The existing FinWiz flow would run here...
    # After analysis is complete, save the results

    # Example analysis results (this would come from the actual crews)
    mock_analysis_results = {
        "portfolio_data": {"holdings": [{"name": "Apple Inc.", "ticker": "AAPL", "decision": "KEEP"}]},
        "recommendations": {"stocks": ["AAPL - Apple Inc.", "MSFT - Microsoft"], "etfs": ["VTI - Vanguard Total Stock Market"]},
    }

    # Save session with results
    save_session_with_analysis_results(financial_plan, mock_analysis_results)

    return financial_plan
