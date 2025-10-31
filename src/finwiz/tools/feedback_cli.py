"""
Command Line Interface for A+ Feedback Learning System.

This CLI provides commands for managing the feedback learning system,
analyzing feedback patterns, and monitoring learning effectiveness.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import click

from finwiz.schemas.feedback import (
    FeedbackSentiment,
    LearningConfiguration,
    RecommendationOutcome,
    UserFeedback,
)
from finwiz.schemas.investment_discovery import APlusCriteria
from finwiz.services.feedback_service import get_feedback_service
from finwiz.tools.logger import get_logger

logger = get_logger(__name__)


@click.group()
def feedback_cli() -> None:
    """Manage A+ Investment Feedback Learning System."""
    pass


@feedback_cli.command()
@click.option("--user-id", required=True, help="User identifier")
@click.option("--recommendation-id", required=True, help="Recommendation ID")
@click.option("--symbol", required=True, help="Investment symbol")
@click.option("--asset-type", type=click.Choice(["etf", "stock", "crypto"]), required=True, help="Asset type")
@click.option("--outcome", type=click.Choice(["accepted", "rejected", "partially_accepted", "deferred"]), required=True, help="User outcome")
@click.option(
    "--sentiment",
    type=click.Choice(["very_positive", "positive", "neutral", "negative", "very_negative"]),
    required=True,
    help="User sentiment",
)
@click.option("--confidence", type=int, help="Confidence rating (1-5)")
@click.option("--reasons", multiple=True, help="Reasons for decision")
@click.option("--comments", help="Optional user comments")
def collect_feedback(
    user_id: str,
    recommendation_id: str,
    symbol: str,
    asset_type: str,
    outcome: str,
    sentiment: str,
    confidence: int,
    reasons: tuple[str, ...],
    comments: str,
) -> None:
    """Collect user feedback on A+ recommendations."""

    async def _collect() -> None:
        try:
            feedback_service = get_feedback_service()

            feedback = UserFeedback(
                feedback_id="",
                user_id=user_id,
                recommendation_id=recommendation_id,
                symbol=symbol,
                asset_type=asset_type,
                recommended_grade="A+",
                recommended_score=0.95,
                outcome=RecommendationOutcome(outcome),
                sentiment=FeedbackSentiment(sentiment),
                confidence_rating=confidence or 3,
                reasons=list(reasons),
                user_comments=comments or "",
                feedback_type="recommendation_acceptance",
            )

            feedback_id = await feedback_service.collect_user_feedback(feedback)

            click.echo("✅ Feedback collected successfully!")
            click.echo(f"   Feedback ID: {feedback_id}")
            click.echo(f"   Symbol: {symbol}")
            click.echo(f"   Outcome: {outcome}")
            click.echo(f"   Sentiment: {sentiment}")

        except Exception as e:
            click.echo(f"❌ Failed to collect feedback: {str(e)}", err=True)

    asyncio.run(_collect())


@feedback_cli.command()
@click.option("--days", default=90, help="Number of days to analyze")
@click.option("--output-file", help="Save analysis to JSON file")
def analyze_feedback(days: int, output_file: str) -> None:
    """Analyze feedback patterns and generate insights."""

    async def _analyze() -> None:
        try:
            feedback_service = get_feedback_service()

            click.echo(f"🔍 Analyzing feedback patterns for the last {days} days...")

            feedback_summary = await feedback_service.analyze_feedback_patterns(days_back=days)

            # Display summary
            click.echo("\n📊 Feedback Analysis Summary")
            click.echo(f"   Period: {days} days")
            click.echo(f"   Total feedback items: {feedback_summary.total_feedback_items}")
            click.echo(f"   Unique users: {feedback_summary.unique_users}")
            click.echo(f"   Unique recommendations: {feedback_summary.unique_recommendations}")
            click.echo(f"   Sample size adequate: {'✅' if feedback_summary.sample_size_adequacy else '❌'}")

            # Acceptance rates
            click.echo("\n📈 Acceptance Rates by Asset Type:")
            for asset_type, rate in feedback_summary.acceptance_by_asset_type.items():
                click.echo(f"   {asset_type.upper()}: {rate:.1%}")

            # Performance metrics
            if feedback_summary.performance_by_asset_type:
                click.echo("\n🎯 Performance by Asset Type:")
                for asset_type, metrics in feedback_summary.performance_by_asset_type.items():
                    click.echo(f"   {asset_type.upper()}:")
                    click.echo(f"     Average return: {metrics.get('avg_return', 0):.1%}")
                    click.echo(f"     Average alpha: {metrics.get('avg_alpha', 0):.1%}")
                    click.echo(f"     Outperformance rate: {metrics.get('outperformance_rate', 0):.1%}")

            # Key insights
            if feedback_summary.key_insights:
                click.echo("\n💡 Key Insights:")
                for insight in feedback_summary.key_insights:
                    click.echo(f"   • {insight}")

            # Recommendations
            if feedback_summary.recommended_adjustments:
                click.echo("\n🔧 Recommended Adjustments:")
                for adjustment in feedback_summary.recommended_adjustments:
                    click.echo(f"   • {adjustment}")

            # Quality metrics
            click.echo("\n📋 Data Quality:")
            click.echo(f"   Data quality score: {feedback_summary.data_quality_score:.1%}")
            click.echo(f"   Confidence in insights: {feedback_summary.confidence_in_insights:.1%}")

            # Save to file if requested
            if output_file:
                output_path = Path(output_file)
                output_path.write_text(feedback_summary.model_dump_json(indent=2))
                click.echo(f"\n💾 Analysis saved to: {output_path}")

        except Exception as e:
            click.echo(f"❌ Failed to analyze feedback: {str(e)}", err=True)

    asyncio.run(_analyze())


@feedback_cli.command()
@click.option("--days", default=30, help="Number of days to analyze")
def learning_metrics(days: int) -> None:
    """Get comprehensive learning system metrics."""

    async def _metrics() -> None:
        try:
            feedback_service = get_feedback_service()

            click.echo(f"📊 Generating learning metrics for the last {days} days...")

            metrics = await feedback_service.get_learning_metrics(days_back=days)

            # Display metrics
            click.echo("\n🎯 Learning System Performance")
            start_date = metrics.evaluation_period_start.strftime("%Y-%m-%d")
            end_date = metrics.evaluation_period_end.strftime("%Y-%m-%d")
            click.echo(f"   Period: {start_date} to {end_date}")

            # Recommendation metrics
            click.echo("\n📈 Recommendation Metrics:")
            click.echo(f"   Total recommendations: {metrics.total_recommendations}")
            click.echo(f"   Acceptance rate: {metrics.acceptance_rate:.1%}")
            click.echo(f"   Rejection rate: {metrics.rejection_rate:.1%}")

            # Performance metrics
            click.echo("\n🎯 Performance Metrics:")
            click.echo(f"   Recommendations with outcomes: {metrics.recommendations_with_outcomes}")
            click.echo(f"   Outperformance rate: {metrics.outperformance_rate:.1%}")
            click.echo(f"   Grade maintenance rate: {metrics.grade_maintenance_rate:.1%}")

            # Learning effectiveness
            click.echo("\n🧠 Learning Effectiveness:")
            click.echo(f"   Criteria adjustments made: {metrics.criteria_adjustments_made}")
            click.echo(f"   Improvement in acceptance: {metrics.improvement_in_acceptance:+.1%}")
            click.echo(f"   Improvement in performance: {metrics.improvement_in_performance:+.1%}")

            # User satisfaction
            click.echo("\n😊 User Satisfaction:")
            click.echo(f"   Average confidence rating: {metrics.average_confidence_rating:.1f}/5.0")
            click.echo(f"   Positive sentiment rate: {metrics.positive_sentiment_rate:.1%}")

            # Asset-specific metrics
            for asset_type, asset_metrics in [
                ("ETF", metrics.etf_metrics),
                ("Stock", metrics.stock_metrics),
                ("Crypto", metrics.crypto_metrics),
            ]:
                if asset_metrics:
                    click.echo(f"\n📊 {asset_type} Metrics:")
                    for metric_name, value in asset_metrics.items():
                        if isinstance(value, float):
                            if "rate" in metric_name or "acceptance" in metric_name:
                                click.echo(f"   {metric_name.replace('_', ' ').title()}: {value:.1%}")
                            else:
                                click.echo(f"   {metric_name.replace('_', ' ').title()}: {value:.3f}")
                        else:
                            click.echo(f"   {metric_name.replace('_', ' ').title()}: {value}")

        except Exception as e:
            click.echo(f"❌ Failed to get learning metrics: {str(e)}", err=True)

    asyncio.run(_metrics())


@feedback_cli.command()
@click.option("--criteria-file", required=True, help="JSON file with current A+ criteria")
@click.option("--force", is_flag=True, help="Force adjustment regardless of timing")
@click.option("--dry-run", is_flag=True, help="Show what would be adjusted without making changes")
def optimize_criteria(criteria_file: str, force: bool, dry_run: bool) -> None:
    """Optimize A+ criteria based on feedback learning."""

    async def _optimize() -> None:
        try:
            feedback_service = get_feedback_service()

            # Load current criteria
            criteria_path = Path(criteria_file)
            if not criteria_path.exists():
                click.echo(f"❌ Criteria file not found: {criteria_file}", err=True)
                return

            criteria_data = json.loads(criteria_path.read_text())
            current_criteria = APlusCriteria.model_validate(criteria_data)

            click.echo("🔧 Optimizing A+ criteria based on feedback learning...")
            click.echo(f"   Current criteria loaded from: {criteria_file}")
            click.echo(f"   Force adjustment: {'Yes' if force else 'No'}")
            click.echo(f"   Dry run: {'Yes' if dry_run else 'No'}")

            if not dry_run:
                # Perform actual optimization
                adjustment = await feedback_service.adjust_criteria_based_on_learning(current_criteria=current_criteria, force_adjustment=force)

                if adjustment:
                    click.echo("\n✅ Criteria adjustment made!")
                    click.echo(f"   Adjustment ID: {adjustment.adjustment_id}")
                    click.echo(f"   Reason: {adjustment.adjustment_reason}")
                    click.echo(f"   Confidence level: {adjustment.confidence_level:.1%}")
                    click.echo(f"   Expected improvement: {adjustment.expected_improvement:.1%}")
                    click.echo(f"   Backtesting validation: {'✅' if adjustment.backtesting_validation else '❌'}")

                    # Show key changes
                    click.echo("\n📋 Key Changes:")
                    old_criteria = adjustment.criteria_before
                    new_criteria = adjustment.criteria_after

                    # ETF changes
                    if new_criteria.etf_max_expense_ratio != old_criteria.etf_max_expense_ratio:
                        old_ratio = old_criteria.etf_max_expense_ratio
                        new_ratio = new_criteria.etf_max_expense_ratio
                        click.echo(f"   ETF max expense ratio: {old_ratio:.3f} → {new_ratio:.3f}")

                    # Stock changes
                    if new_criteria.stock_min_roe != old_criteria.stock_min_roe:
                        click.echo(f"   Stock min ROE: {old_criteria.stock_min_roe:.1%} → {new_criteria.stock_min_roe:.1%}")

                    # Crypto changes
                    if new_criteria.crypto_min_market_cap != old_criteria.crypto_min_market_cap:
                        old_cap = old_criteria.crypto_min_market_cap / 1e9
                        new_cap = new_criteria.crypto_min_market_cap / 1e9
                        click.echo(f"   Crypto min market cap: ${old_cap:.1f}B → ${new_cap:.1f}B")

                    # Save new criteria
                    new_criteria_file = criteria_path.parent / f"optimized_criteria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    new_criteria_file.write_text(new_criteria.model_dump_json(indent=2))
                    click.echo(f"\n💾 New criteria saved to: {new_criteria_file}")

                else:
                    click.echo("\n ℹ️ No criteria adjustment needed at this time")
                    click.echo("   Possible reasons:")
                    click.echo("   • Insufficient feedback data")
                    click.echo("   • Recent adjustment already made")
                    click.echo("   • Current criteria performing well")

            else:
                # Dry run - analyze what would be changed
                click.echo("\n🔍 Dry Run Analysis:")

                # Get recent feedback analysis
                feedback_summary = await feedback_service.analyze_feedback_patterns(days_back=90)

                click.echo(f"   Feedback samples: {feedback_summary.total_feedback_items}")
                click.echo(f"   Sample size adequate: {'Yes' if feedback_summary.sample_size_adequacy else 'No'}")

                if feedback_summary.recommended_adjustments:
                    click.echo("   Recommended adjustments:")
                    for adjustment in feedback_summary.recommended_adjustments:
                        click.echo(f"     • {adjustment}")
                else:
                    click.echo("   No specific adjustments recommended")

        except Exception as e:
            click.echo(f"❌ Failed to optimize criteria: {str(e)}", err=True)

    asyncio.run(_optimize())


@feedback_cli.command()
@click.option("--adjustment-id", required=True, help="ID of adjustment to rollback")
@click.option("--reason", required=True, help="Reason for rollback")
def rollback_adjustment(adjustment_id: str, reason: str) -> None:
    """Rollback a criteria adjustment."""

    async def _rollback() -> None:
        try:
            feedback_service = get_feedback_service()

            click.echo("🔄 Rolling back criteria adjustment...")
            click.echo(f"   Adjustment ID: {adjustment_id}")
            click.echo(f"   Reason: {reason}")

            success = await feedback_service.rollback_criteria_adjustment(adjustment_id, reason)

            if success:
                click.echo("\n✅ Criteria adjustment rolled back successfully!")
                click.echo("   Previous criteria have been restored")
                click.echo(f"   Rollback reason: {reason}")
            else:
                click.echo("\n❌ Failed to rollback criteria adjustment")
                click.echo("   Possible reasons:")
                click.echo("   • Adjustment ID not found")
                click.echo("   • Adjustment cannot be rolled back")
                click.echo("   • System error")

        except Exception as e:
            click.echo(f"❌ Failed to rollback adjustment: {str(e)}", err=True)

    asyncio.run(_rollback())


@feedback_cli.command()
@click.option("--config-file", help="Configuration file for learning system")
def show_config(config_file: str) -> None:
    """Show current learning system configuration."""
    try:
        if config_file and Path(config_file).exists():
            config_data = json.loads(Path(config_file).read_text())
            config = LearningConfiguration.model_validate(config_data)
        else:
            config = LearningConfiguration()  # Default configuration

        click.echo("⚙️ Learning System Configuration")

        # Learning parameters
        click.echo("\n🧠 Learning Parameters:")
        click.echo(f"   Min feedback samples: {config.min_feedback_samples}")
        click.echo(f"   Learning rate: {config.learning_rate}")
        click.echo(f"   Confidence threshold: {config.confidence_threshold}")

        # Adjustment limits
        click.echo("\n🔧 Adjustment Limits:")
        click.echo(f"   Max criteria change: {config.max_criteria_change:.1%}")
        click.echo(f"   Adjustment frequency: {config.adjustment_frequency_days} days")

        # Validation requirements
        click.echo("\n✅ Validation Requirements:")
        click.echo(f"   Require backtesting: {'Yes' if config.require_backtesting else 'No'}")
        click.echo(f"   Min backtest years: {config.min_backtest_years}")

        # Rollback conditions
        click.echo("\n🔄 Rollback Conditions:")
        click.echo(f"   Auto rollback enabled: {'Yes' if config.auto_rollback_enabled else 'No'}")
        click.echo(f"   Performance threshold: {config.rollback_performance_threshold:.1%}")
        click.echo(f"   Acceptance threshold: {config.rollback_acceptance_threshold:.1%}")

        # Asset-specific settings
        click.echo("\n📊 Asset-Specific Settings:")
        click.echo(f"   Asset-specific learning: {'Yes' if config.asset_specific_learning else 'No'}")
        click.echo(f"   Weight by performance: {'Yes' if config.weight_by_asset_performance else 'No'}")

    except Exception as e:
        click.echo(f"❌ Failed to show configuration: {str(e)}", err=True)


if __name__ == "__main__":
    feedback_cli()
