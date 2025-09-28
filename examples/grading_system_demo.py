"""
Demonstration of the new grading system for FinWiz portfolio analysis.

This script shows how composite scores are converted to letter grades
and displays sample portfolio analysis with the new grading system.
"""

from finwiz.utils.grading_system import (
    format_grade_display,
    get_portfolio_grade_summary,
    score_to_grade,
)


def demo_individual_grades() -> None:
    """Demonstrate individual grade conversions."""
    print("🎓 Système de Notes Scolaires FinWiz")
    print("=" * 50)

    # Sample scores representing different investment qualities
    sample_scores = [
        (0.98, "ETF Core Premium (VWRA)"),
        (0.88, "Action Blue-Chip (MSFT)"),
        (0.82, "ETF Sectoriel (QQQ)"),
        (0.77, "Action Croissance (NVDA)"),
        (0.72, "Action Cyclique (TSM)"),
        (0.67, "ETF Émergents (IEMG)"),
        (0.55, "Action Spéculative"),
        (0.00, "Ticker Invalide"),
    ]

    for score, description in sample_scores:
        grade_info = score_to_grade(score)
        print(f"\n{description}")
        print(f"  Score: {score:.2f} → {grade_info.emoji} Note {grade_info.grade} ({grade_info.percentage:.0f}%)")
        print(f"  Description: {grade_info.description}")
        print(f"  Action: {grade_info.action}")


def demo_portfolio_summary() -> None:
    """Demonstrate portfolio-wide grade analysis."""
    print("\n\n📊 Analyse du Portefeuille Complet")
    print("=" * 50)

    # Simulate a realistic portfolio with various scores
    portfolio_scores = [
        # ETFs (mostly good grades)
        0.85,
        0.82,
        0.80,
        0.78,
        0.75,
        0.73,
        0.70,
        # Individual stocks (mixed grades)
        0.88,
        0.85,
        0.77,
        0.75,
        0.72,
        0.68,
        0.65,
        # Some problematic positions
        0.55,
        0.00,
        0.00,
    ]

    summary = get_portfolio_grade_summary(portfolio_scores)

    print(f"Nombre total de positions: {summary['total_positions']}")
    print(f"Note moyenne du portefeuille: {summary['average_grade']} ({summary['average_percentage']:.0f}%)")
    print(f"Description: {summary['grade_info'].description}")
    print(f"Action recommandée: {summary['grade_info'].action}")

    print("\nRépartition des notes:")
    for grade, data in summary["distribution"].items():
        print(f"  {grade}: {data['count']} positions ({data['percentage']:.0f}%)")


def demo_actionable_recommendations() -> None:
    """Show actionable recommendations based on grades."""
    print("\n\n💡 Recommandations Actionnables")
    print("=" * 50)

    # Sample portfolio positions with their scores
    positions = [
        ("VWRA.L", "Vanguard FTSE All-World", 0.85),
        ("MSFT", "Microsoft Corporation", 0.77),
        ("NVDA", "NVIDIA Corporation", 0.75),
        ("TSM", "Taiwan Semiconductor", 0.68),
        ("INVALID.XX", "Position Invalide", 0.00),
    ]

    print("Actions par catégorie de note:\n")

    # Group by grade
    grade_groups = {}
    for ticker, name, score in positions:
        grade_info = score_to_grade(score)
        if grade_info.grade not in grade_groups:
            grade_groups[grade_info.grade] = []
        grade_groups[grade_info.grade].append((ticker, name, score, grade_info))

    for grade in ["A+", "A", "B+", "B", "C+", "C", "D", "F"]:
        if grade in grade_groups:
            positions_in_grade = grade_groups[grade]
            grade_info = positions_in_grade[0][3]  # Get grade info from first position

            print(f"{grade_info.emoji} Note {grade} - {grade_info.description}")
            print(f"   Action: {grade_info.action}")
            print("   Positions:")

            for ticker, name, score, _ in positions_in_grade:
                print(f"     • {ticker} - {name} ({score:.2f})")
            print()


def demo_html_display() -> None:
    """Show how grades appear in HTML reports."""
    print("\n\n🌐 Affichage HTML des Notes")
    print("=" * 50)

    sample_score = 0.77
    grade_info = score_to_grade(sample_score)

    print("Format d'affichage:")
    print(f"  Texte simple: {format_grade_display(sample_score)}")
    print(f"  Sans pourcentage: {format_grade_display(sample_score, include_percentage=False)}")

    print(f"\nClasse CSS: {grade_info.css_class}")
    print(f"Emoji: {grade_info.emoji}")


if __name__ == "__main__":
    demo_individual_grades()
    demo_portfolio_summary()
    demo_actionable_recommendations()
    demo_html_display()

    print("\n\n✅ Démonstration terminée!")
    print("Le système de notes scolaires est maintenant intégré dans FinWiz.")
    print("Les prochains rapports utiliseront ce format plus intuitif.")
