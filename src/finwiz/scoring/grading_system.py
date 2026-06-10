"""
Grading system utilities for FinWiz portfolio analysis.

This module provides functions to convert composite scores to intuitive
letter grades (A+ to F) and generate actionable recommendations.
"""

from dataclasses import dataclass
from typing import Any, Literal

# Type definitions for grades
Grade = Literal["A+", "A", "B+", "B", "C+", "C", "D", "F"]


@dataclass
class GradeInfo:
    """Information about a letter grade."""

    grade: Grade
    percentage: float
    description: str
    action: str
    emoji: str
    css_class: str


def score_to_grade(composite_score: float) -> GradeInfo:
    """
    Convert composite score (0.0-1.0) to letter grade with actionable information.

    Args:
        composite_score: Float between 0.0 and 1.0

    Returns:
        GradeInfo object with grade, description, and recommended action

    """
    percentage = composite_score * 100

    if percentage >= 95:
        return GradeInfo(
            grade="A+",
            percentage=percentage,
            description="Excellent - Champion du portefeuille",
            action="Augmentez l'allocation si possible",
            emoji="🏆",
            css_class="grade-a-plus",
        )
    elif percentage >= 85:
        return GradeInfo(
            grade="A",
            percentage=percentage,
            description="Très bon - Investissement de qualité",
            action="Maintenez et continuez le DCA",
            emoji="⭐",
            css_class="grade-a",
        )
    elif percentage >= 80:
        return GradeInfo(
            grade="B+",
            percentage=percentage,
            description="Bon+ - Solide avec potentiel",
            action="Conservez et surveillez les opportunités",
            emoji="📈",
            css_class="grade-b-plus",
        )
    elif percentage >= 75:
        return GradeInfo(
            grade="B",
            percentage=percentage,
            description="Bon - Satisfaisant à conserver",
            action="Maintenez, continuez le DCA",
            emoji="✅",
            css_class="grade-b",
        )
    elif percentage >= 70:
        return GradeInfo(
            grade="C+",
            percentage=percentage,
            description="Passable+ - Acceptable avec surveillance",
            action="Conservez mais surveillez de près",
            emoji="⚠️",
            css_class="grade-c-plus",
        )
    elif percentage >= 65:
        return GradeInfo(
            grade="C",
            percentage=percentage,
            description="Passable - Minimum acceptable",
            action="Maintenez mais ne renforcez pas",
            emoji="🔍",
            css_class="grade-c",
        )
    elif percentage >= 50:
        return GradeInfo(
            grade="D",
            percentage=percentage,
            description="Insuffisant - À améliorer rapidement",
            action="Réduisez progressivement la position",
            emoji="⚡",
            css_class="grade-d",
        )
    else:
        return GradeInfo(
            grade="F",
            percentage=percentage,
            description="Échec - Élimination immédiate",
            action="Vendez immédiatement",
            emoji="❌",
            css_class="grade-f",
        )


def format_grade_display(composite_score: float, include_percentage: bool = True) -> str:
    """
    Format grade for display in reports.

    Args:
        composite_score: Float between 0.0 and 1.0
        include_percentage: Whether to include percentage in display

    Returns:
        Formatted string for display

    """
    grade_info = score_to_grade(composite_score)

    if include_percentage:
        return f"{grade_info.emoji} {grade_info.grade} ({grade_info.percentage:.0f}%)"
    else:
        return f"{grade_info.emoji} {grade_info.grade}"


def count_grade_distribution(
    results: dict[str, dict[str, Any]],
    grade_key: str = "grade",
    default_grade: str = "F",
) -> dict[str, int]:
    """
    Count grade distribution from analysis results.

    Args:
        results: Dict mapping ticker to result dict containing grade
        grade_key: Key to extract grade from each result
        default_grade: Default grade if key missing

    Returns:
        Dict mapping grade to count (e.g., {"A+": 2, "A": 5, ...})

    """
    grade_counts: dict[str, int] = {
        "A+": 0,
        "A": 0,
        "B+": 0,
        "B": 0,
        "C+": 0,
        "C": 0,
        "D": 0,
        "F": 0,
    }

    for result in results.values():
        grade = result.get(grade_key, default_grade)
        if grade in grade_counts:
            grade_counts[grade] += 1

    return grade_counts
