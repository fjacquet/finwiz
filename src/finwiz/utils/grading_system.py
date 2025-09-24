"""
Grading system utilities for FinWiz portfolio analysis.

This module provides functions to convert composite scores to intuitive
letter grades (A+ to F) and generate actionable recommendations.
"""

from dataclasses import dataclass
from typing import Literal

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
            css_class="grade-a-plus"
        )
    elif percentage >= 85:
        return GradeInfo(
            grade="A",
            percentage=percentage,
            description="Très bon - Investissement de qualité",
            action="Maintenez et continuez le DCA",
            emoji="⭐",
            css_class="grade-a"
        )
    elif percentage >= 80:
        return GradeInfo(
            grade="B+",
            percentage=percentage,
            description="Bon+ - Solide avec potentiel",
            action="Conservez et surveillez les opportunités",
            emoji="📈",
            css_class="grade-b-plus"
        )
    elif percentage >= 75:
        return GradeInfo(
            grade="B",
            percentage=percentage,
            description="Bon - Satisfaisant à conserver",
            action="Maintenez, continuez le DCA",
            emoji="✅",
            css_class="grade-b"
        )
    elif percentage >= 70:
        return GradeInfo(
            grade="C+",
            percentage=percentage,
            description="Passable+ - Acceptable avec surveillance",
            action="Conservez mais surveillez de près",
            emoji="⚠️",
            css_class="grade-c-plus"
        )
    elif percentage >= 65:
        return GradeInfo(
            grade="C",
            percentage=percentage,
            description="Passable - Minimum acceptable",
            action="Maintenez mais ne renforcez pas",
            emoji="🔍",
            css_class="grade-c"
        )
    elif percentage >= 50:
        return GradeInfo(
            grade="D",
            percentage=percentage,
            description="Insuffisant - À améliorer rapidement",
            action="Réduisez progressivement la position",
            emoji="⚡",
            css_class="grade-d"
        )
    else:
        return GradeInfo(
            grade="F",
            percentage=percentage,
            description="Échec - Élimination immédiate",
            action="Vendez immédiatement",
            emoji="❌",
            css_class="grade-f"
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


def get_portfolio_grade_summary(scores: list[float]) -> dict:
    """
    Calculate portfolio-wide grade statistics.
    
    Args:
        scores: List of composite scores for all holdings
        
    Returns:
        Dictionary with grade distribution and portfolio average
    """
    if not scores:
        return {"average_grade": "N/A", "distribution": {}, "total_positions": 0}
    
    grade_counts = {}
    total_score = 0
    
    for score in scores:
        grade_info = score_to_grade(score)
        grade_counts[grade_info.grade] = grade_counts.get(grade_info.grade, 0) + 1
        total_score += score
    
    average_score = total_score / len(scores)
    average_grade_info = score_to_grade(average_score)
    
    # Calculate percentages
    total_positions = len(scores)
    distribution = {
        grade: {"count": count, "percentage": (count / total_positions) * 100}
        for grade, count in grade_counts.items()
    }
    
    return {
        "average_grade": average_grade_info.grade,
        "average_score": average_score,
        "average_percentage": average_score * 100,
        "distribution": distribution,
        "total_positions": total_positions,
        "grade_info": average_grade_info
    }


def get_grade_css_styles() -> str:
    """
    Return CSS styles for grade display.
    
    Returns:
        CSS string for styling grades
    """
    return """
    .grade-a-plus { background: #10b981; color: white; font-weight: bold; }
    .grade-a { background: #059669; color: white; font-weight: bold; }
    .grade-b-plus { background: #0891b2; color: white; }
    .grade-b { background: #0284c7; color: white; }
    .grade-c-plus { background: #eab308; color: white; }
    .grade-c { background: #ca8a04; color: white; }
    .grade-d { background: #ea580c; color: white; }
    .grade-f { background: #dc2626; color: white; font-weight: bold; }
    
    .grade-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.9em;
        margin: 2px;
    }
    
    .grade-summary {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    """