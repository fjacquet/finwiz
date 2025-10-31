"""
Data quality validation system for FinWiz quantitative analysis.

This module provides comprehensive data validation capabilities including:
- Data completeness, accuracy, and consistency checks
- OHLCV relationship validation
- Statistical outlier detection
- Data quality scoring and reporting
"""

from datetime import datetime

import pandas as pd
from pydantic import BaseModel, Field

from finwiz.quantitative.config import QuantConfig, get_quant_config
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


class DataQualityIssue(BaseModel):
    """Represents a data quality issue found during validation."""

    issue_type: str = Field(..., description="Type of data quality issue")
    severity: str = Field(..., description="Severity level: low, medium, high, critical")
    description: str = Field(..., description="Detailed description of the issue")
    affected_columns: list[str] = Field(default_factory=list, description="Columns affected by the issue")
    affected_rows: int = Field(default=0, description="Number of rows affected")
    suggested_action: str = Field(..., description="Suggested remediation action")


class DataQualityReport(BaseModel):
    """Comprehensive data quality validation report."""

    symbol: str = Field(..., description="Stock symbol that was validated")
    start_date: datetime = Field(..., description="Start date of data range")
    end_date: datetime = Field(..., description="End date of data range")
    total_rows: int = Field(..., description="Total number of data rows")
    validation_timestamp: datetime = Field(default_factory=datetime.now, description="When validation was performed")

    is_valid: bool = Field(..., description="Overall data quality status")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score from 0.0 to 1.0")

    issues: list[DataQualityIssue] = Field(default_factory=list, description="List of identified issues")

    # Data completeness metrics
    completeness_score: float = Field(..., ge=0.0, le=1.0, description="Data completeness score")
    missing_data_pct: float = Field(..., ge=0.0, le=1.0, description="Percentage of missing data")

    # Data consistency metrics
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="Data consistency score")
    outlier_count: int = Field(default=0, description="Number of statistical outliers detected")

    # Data accuracy metrics
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Data accuracy score")
    suspicious_values_count: int = Field(default=0, description="Number of suspicious values detected")

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}


class DataQualityValidator:
    """
    Validates data completeness, accuracy, and consistency for financial time series data.

    Performs comprehensive validation including:
    - Missing data detection
    - Outlier identification
    - Price consistency checks
    - Volume validation
    - Date sequence validation
    """

    def __init__(self, config: QuantConfig | None = None) -> None:
        """
        Initialize data quality validator.

        Args:
            config: Quantitative analysis configuration

        """
        self.config = config or get_quant_config()
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def validate_data_quality(self, data: pd.DataFrame, symbol: str, start_date: datetime, end_date: datetime) -> DataQualityReport:
        """
        Perform comprehensive data quality validation.

        Args:
            data: OHLCV data DataFrame
            symbol: Stock symbol
            start_date: Expected start date
            end_date: Expected end date

        Returns:
            Comprehensive data quality report

        """
        self.logger.info(f"Validating data quality for {symbol} from {start_date} to {end_date}")

        issues = []

        # Basic data structure validation
        structure_issues = self._validate_data_structure(data, symbol)
        issues.extend(structure_issues)

        # Data completeness validation
        completeness_issues, completeness_score, missing_pct = self._validate_completeness(data, symbol, start_date, end_date)
        issues.extend(completeness_issues)

        # Data consistency validation
        consistency_issues, consistency_score, outlier_count = self._validate_consistency(data, symbol)
        issues.extend(consistency_issues)

        # Data accuracy validation
        accuracy_issues, accuracy_score, suspicious_count = self._validate_accuracy(data, symbol)
        issues.extend(accuracy_issues)

        # Calculate overall quality score
        quality_score = self._calculate_overall_quality_score(completeness_score, consistency_score, accuracy_score, len(issues))

        # Determine if data is valid
        is_valid = self._determine_validity(quality_score, issues)

        return DataQualityReport(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            total_rows=len(data),
            is_valid=is_valid,
            quality_score=quality_score,
            issues=issues,
            completeness_score=completeness_score,
            missing_data_pct=missing_pct,
            consistency_score=consistency_score,
            outlier_count=outlier_count,
            accuracy_score=accuracy_score,
            suspicious_values_count=suspicious_count,
        )

    def _validate_data_structure(self, data: pd.DataFrame, symbol: str) -> list[DataQualityIssue]:
        """Validate basic data structure and required columns."""
        issues = []

        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            issues.append(
                DataQualityIssue(
                    issue_type="missing_columns",
                    severity="critical",
                    description=f"Required columns are missing: {missing_columns}",
                    affected_columns=missing_columns,
                    suggested_action="Ensure data source provides all required OHLCV columns",
                )
            )

        if data.empty:
            issues.append(
                DataQualityIssue(
                    issue_type="empty_dataset",
                    severity="critical",
                    description="Dataset is empty",
                    affected_rows=0,
                    suggested_action="Check data source and date range parameters",
                )
            )

        if len(data) < self.config.min_data_points:
            issues.append(
                DataQualityIssue(
                    issue_type="insufficient_data",
                    severity="high",
                    description=f"Dataset has only {len(data)} rows, minimum required: {self.config.min_data_points}",
                    affected_rows=len(data),
                    suggested_action="Extend date range or use different data source",
                )
            )

        return issues

    def _validate_completeness(self, data: pd.DataFrame, symbol: str, start_date: datetime, end_date: datetime) -> tuple[list[DataQualityIssue], float, float]:
        """Validate data completeness and missing values."""
        issues = []

        # Check for missing values
        missing_data = data.isnull().sum()
        total_cells = len(data) * len(data.columns)
        missing_cells = missing_data.sum()
        missing_pct = missing_cells / total_cells if total_cells > 0 else 0

        if missing_pct > 0.05:  # More than 5% missing data
            severity = "critical" if missing_pct > 0.2 else "high" if missing_pct > 0.1 else "medium"
            issues.append(
                DataQualityIssue(
                    issue_type="missing_data",
                    severity=severity,
                    description=f"{missing_pct:.2%} of data is missing",
                    affected_columns=[col for col in missing_data.index if missing_data[col] > 0],
                    affected_rows=int(missing_cells),
                    suggested_action="Fill missing values or use alternative data source",
                )
            )

        # Check for date gaps (trading days)
        if not data.empty and hasattr(data.index, "to_pydatetime"):
            date_gaps = self._detect_date_gaps(data.index.to_pydatetime())
            if date_gaps > 0:
                issues.append(
                    DataQualityIssue(
                        issue_type="date_gaps",
                        severity="medium",
                        description=f"Found {date_gaps} significant date gaps in the data",
                        affected_rows=date_gaps,
                        suggested_action="Verify if gaps correspond to market holidays or data source issues",
                    )
                )

        # Calculate completeness score
        completeness_score = max(0.0, 1.0 - (missing_pct * 2))  # Penalize missing data heavily

        return issues, completeness_score, missing_pct

    def _validate_consistency(self, data: pd.DataFrame, symbol: str) -> tuple[list[DataQualityIssue], float, int]:
        """Validate data consistency and detect outliers."""
        issues = []
        outlier_count = 0

        if data.empty or "Open" not in data.columns:
            return issues, 1.0, 0

        # Check OHLC relationships
        ohlc_violations = self._check_ohlc_relationships(data)
        if ohlc_violations > 0:
            issues.append(
                DataQualityIssue(
                    issue_type="ohlc_violations",
                    severity="high",
                    description=f"Found {ohlc_violations} OHLC relationship violations (High < Low, etc.)",
                    affected_columns=["Open", "High", "Low", "Close"],
                    affected_rows=ohlc_violations,
                    suggested_action="Review and correct invalid OHLC relationships",
                )
            )

        # Detect price outliers using statistical methods
        price_outliers = self._detect_price_outliers(data)
        outlier_count += price_outliers
        if price_outliers > 0:
            issues.append(
                DataQualityIssue(
                    issue_type="price_outliers",
                    severity="medium",
                    description=f"Detected {price_outliers} statistical price outliers",
                    affected_columns=["Open", "High", "Low", "Close"],
                    affected_rows=price_outliers,
                    suggested_action="Review outliers for data errors or significant market events",
                )
            )

        # Detect volume outliers
        if "Volume" in data.columns:
            volume_outliers = self._detect_volume_outliers(data)
            outlier_count += volume_outliers
            if volume_outliers > 0:
                issues.append(
                    DataQualityIssue(
                        issue_type="volume_outliers",
                        severity="low",
                        description=f"Detected {volume_outliers} volume outliers",
                        affected_columns=["Volume"],
                        affected_rows=volume_outliers,
                        suggested_action="Review volume spikes for market events or data errors",
                    )
                )

        # Calculate consistency score
        total_rows = len(data)
        consistency_score = max(0.0, 1.0 - (outlier_count / total_rows)) if total_rows > 0 else 1.0

        return issues, consistency_score, outlier_count

    def _validate_accuracy(self, data: pd.DataFrame, symbol: str) -> tuple[list[DataQualityIssue], float, int]:
        """Validate data accuracy and detect suspicious values."""
        issues = []
        suspicious_count = 0

        if data.empty:
            return issues, 1.0, 0

        # Check for zero or negative prices
        price_columns = ["Open", "High", "Low", "Close"]
        for col in price_columns:
            if col in data.columns:
                invalid_prices = (data[col] <= 0).sum()
                if invalid_prices > 0:
                    suspicious_count += invalid_prices
                    issues.append(
                        DataQualityIssue(
                            issue_type="invalid_prices",
                            severity="critical",
                            description=f"Found {invalid_prices} zero or negative prices in {col}",
                            affected_columns=[col],
                            affected_rows=invalid_prices,
                            suggested_action="Remove or correct invalid price data",
                        )
                    )

        # Check for unrealistic price movements (>50% daily change)
        if "Close" in data.columns and len(data) > 1:
            daily_returns = data["Close"].pct_change(fill_method=None).abs()
            extreme_moves = (daily_returns > 0.5).sum()
            if extreme_moves > 0:
                suspicious_count += extreme_moves
                severity = "high" if extreme_moves > len(data) * 0.01 else "medium"
                issues.append(
                    DataQualityIssue(
                        issue_type="extreme_price_moves",
                        severity=severity,
                        description=f"Found {extreme_moves} days with >50% price movements",
                        affected_columns=["Close"],
                        affected_rows=extreme_moves,
                        suggested_action="Verify extreme price movements against market events",
                    )
                )

        # Check for duplicate timestamps
        if hasattr(data.index, "duplicated"):
            duplicate_dates = data.index.duplicated().sum()
            if duplicate_dates > 0:
                suspicious_count += duplicate_dates
                issues.append(
                    DataQualityIssue(
                        issue_type="duplicate_dates",
                        severity="high",
                        description=f"Found {duplicate_dates} duplicate timestamps",
                        affected_rows=duplicate_dates,
                        suggested_action="Remove duplicate entries or aggregate data appropriately",
                    )
                )

        # Calculate accuracy score
        total_rows = len(data)
        accuracy_score = max(0.0, 1.0 - (suspicious_count / total_rows)) if total_rows > 0 else 1.0

        return issues, accuracy_score, suspicious_count

    def _check_ohlc_relationships(self, data: pd.DataFrame) -> int:
        """Check for violations in OHLC relationships."""
        violations = 0

        required_cols = ["Open", "High", "Low", "Close"]
        if not all(col in data.columns for col in required_cols):
            return 0

        # High should be >= Open, Close, Low
        violations += (data["High"] < data["Open"]).sum()
        violations += (data["High"] < data["Close"]).sum()
        violations += (data["High"] < data["Low"]).sum()

        # Low should be <= Open, Close, High
        violations += (data["Low"] > data["Open"]).sum()
        violations += (data["Low"] > data["Close"]).sum()
        violations += (data["Low"] > data["High"]).sum()

        return violations

    def _detect_price_outliers(self, data: pd.DataFrame) -> int:
        """Detect price outliers using statistical methods."""
        outliers = 0

        price_columns = ["Open", "High", "Low", "Close"]
        for col in price_columns:
            if col in data.columns and len(data) > 10:
                # Use IQR method for outlier detection
                Q1 = data[col].quantile(0.25)
                Q3 = data[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers += ((data[col] < lower_bound) | (data[col] > upper_bound)).sum()

        return outliers

    def _detect_volume_outliers(self, data: pd.DataFrame) -> int:
        """Detect volume outliers using statistical methods."""
        if "Volume" not in data.columns or len(data) < 10:
            return 0

        # Use log transformation for volume due to high variability
        import numpy as np

        log_volume = data["Volume"].replace(0, 1).apply(lambda x: np.log(x) if x > 0 else 0)

        Q1 = log_volume.quantile(0.25)
        Q3 = log_volume.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 2.0 * IQR  # More lenient for volume
        upper_bound = Q3 + 2.0 * IQR

        return ((log_volume < lower_bound) | (log_volume > upper_bound)).sum()

    def _detect_date_gaps(self, dates: list[datetime]) -> int:
        """Detect significant gaps in date sequence."""
        if len(dates) < 2:
            return 0

        gaps = 0
        sorted_dates = sorted(dates)

        for i in range(1, len(sorted_dates)):
            days_diff = (sorted_dates[i] - sorted_dates[i - 1]).days
            # Consider gaps > 7 days as significant (accounting for weekends and holidays)
            if days_diff > 7:
                gaps += 1

        return gaps

    def _calculate_overall_quality_score(self, completeness: float, consistency: float, accuracy: float, issue_count: int) -> float:
        """Calculate overall data quality score."""
        # Weighted average of individual scores
        base_score = completeness * 0.4 + consistency * 0.3 + accuracy * 0.3

        # Penalize based on number of issues
        issue_penalty = min(0.3, issue_count * 0.05)

        return max(0.0, base_score - issue_penalty)

    def _determine_validity(self, quality_score: float, issues: list[DataQualityIssue]) -> bool:
        """Determine if data is valid based on quality score and critical issues."""
        # Check for critical issues
        critical_issues = [issue for issue in issues if issue.severity == "critical"]
        if critical_issues:
            return False

        # Check for high severity issues that should also invalidate data
        high_severity_issues = [issue for issue in issues if issue.severity == "high"]
        if high_severity_issues:
            # Check for specific high severity issues that should invalidate
            blocking_issue_types = ["insufficient_data", "ohlc_violations"]
            for issue in high_severity_issues:
                if issue.issue_type in blocking_issue_types:
                    return False

        # Check quality score threshold
        return quality_score >= 0.7
