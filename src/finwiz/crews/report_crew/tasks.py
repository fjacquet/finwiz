"""
Task definitions for the Report Crew.

This module defines all tasks used in the Report Crew with their configurations.
"""

import logging
from typing import Any

from crewai import Task
from crewai.project import task

from finwiz.utils.task_decorators import async_task, sync_task

logger = logging.getLogger(__name__)


class ReportCrewTasks:
    """Defines all tasks for the Report Crew."""

    def __init__(self, tasks_config: dict[str, Any]) -> None:
        """Initialize tasks with configuration."""
        self.tasks_config = tasks_config

    @async_task
    @task
    def comprehensive_financial_integration_task(self) -> Task:
        """Integrate Stock/ETF/Crypto analyses into a unified narrative."""
        return Task(
            config=self.tasks_config["comprehensive_financial_integration_task"],
            verbose=True,
        )

    @async_task
    @task
    def optimal_portfolio_allocation_task(self) -> Task:
        """Derive optimal asset allocation based on goals and constraints."""
        return Task(
            config=self.tasks_config["optimal_portfolio_allocation_task"],
            verbose=True,
        )

    @async_task
    @task
    def risk_assessment_mitigation_task(self) -> Task:
        """Assess key risks and propose mitigation strategies."""
        return Task(
            config=self.tasks_config["risk_assessment_mitigation_task"],
            verbose=True,
        )

    @sync_task
    @task
    def comprehensive_investment_report_task(self) -> Task:
        """Compile the comprehensive HTML investment report."""
        return Task(
            config=self.tasks_config["comprehensive_investment_report_task"],
            verbose=True,
        )

    def get_all_tasks(self) -> list[Task]:
        """Get all tasks as a list."""
        return [
            self.comprehensive_financial_integration_task(),
            self.optimal_portfolio_allocation_task(),
            self.risk_assessment_mitigation_task(),
            self.comprehensive_investment_report_task(),
        ]
