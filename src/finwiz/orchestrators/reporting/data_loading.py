"""Deep-analysis loading, transformation, and portfolio-merge mixin."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from finwiz.schemas.portfolio_review import PortfolioReview
from finwiz.scoring.grading_system import count_grade_distribution

if TYPE_CHECKING:
    from finwiz.flow_state import FinwizState


class ReportDataLoadingMixin:
    """Reads deep-analysis JSON from disk and merges it into the portfolio review."""

    # Provided by ReportingOrchestrator.__init__
    state: FinwizState
    logger: Any

    def _get_portfolio_review_from_state(self) -> dict[str, Any] | None:
        """Get portfolio review data from state."""
        if hasattr(self.state, "portfolio_review") and self.state.portfolio_review:
            return self.state.portfolio_review
        return None

    def _convert_to_portfolio_review(
        self,
        portfolio_review_data: dict[str, Any] | PortfolioReview,
    ) -> PortfolioReview:
        """Convert portfolio review data to PortfolioReview object."""
        if isinstance(portfolio_review_data, PortfolioReview):
            return portfolio_review_data

        # Handle nested structure
        if isinstance(portfolio_review_data, dict):
            if "portfolio_review" in portfolio_review_data:
                return PortfolioReview.model_validate(portfolio_review_data["portfolio_review"])
            return PortfolioReview.model_validate(portfolio_review_data)

        raise ValueError(f"Invalid portfolio review data type: {type(portfolio_review_data)}")

    def _read_deep_analysis_from_files(self) -> dict[str, Any] | None:
        """Read deep analysis results from JSON files on disk."""
        try:
            self.logger.info("Reading deep analysis results from JSON files...")

            raw_deep_analysis = {}
            session_id = self.state.session_id or "default"

            # Read JSON files from disk for each asset class
            # Deep analysis saves to output/enriched/{asset_class}/, cache/portfolio_analysis/{asset_class}/, and output/deep_analysis_{asset_class}/ directories
            for asset_class in ["stock", "etf", "crypto"]:
                # Try multiple directory structures (enriched first, then cache, then legacy output directories)
                for base_dir in [f"output/enriched/{asset_class}", f"cache/portfolio_analysis/{asset_class}", f"output/deep_analysis_{asset_class}", f"output/{asset_class}"]:
                    asset_dir = Path(base_dir)
                    if asset_dir.exists():
                        # Match files with various patterns: session_id, timestamp, enriched, or date patterns
                        for json_file in (
                            list(asset_dir.glob(f"*_{session_id}.json"))
                            + list(asset_dir.glob("*_enriched.json"))
                            + list(asset_dir.glob("*_output_*.json"))
                            + list(asset_dir.glob("*_20*.json"))
                        ):
                            try:
                                data = self._read_json_file(str(json_file))

                                # Handle different data structures:
                                # 1. Cache format: {"ticker": "X", "analysis": {...}}
                                # 2. CrewAI format: {"pydantic": {...}}
                                # 3. Enriched format: {"ticker": "X", "final_score": ..., "quantitative": {...}}
                                # 4. Direct format: {"ticker": "X", "composite_score": ...}
                                if "analysis" in data and isinstance(data["analysis"], dict):
                                    # Cache format - extract analysis data
                                    analysis_data = data["analysis"]
                                    # Ensure ticker is in analysis_data
                                    if "ticker" not in analysis_data and "ticker" in data:
                                        analysis_data["ticker"] = data["ticker"]
                                elif "pydantic" in data and isinstance(data["pydantic"], dict):
                                    # CrewAI format
                                    analysis_data = data["pydantic"]
                                else:
                                    # Direct or enriched format
                                    analysis_data = data

                                # Normalize field names for enriched format
                                # Map final_score -> composite_score, final_grade -> grade, final_recommendation -> recommendation
                                if "final_score" in analysis_data and "composite_score" not in analysis_data:
                                    analysis_data["composite_score"] = analysis_data["final_score"]
                                if "final_grade" in analysis_data and "grade" not in analysis_data:
                                    analysis_data["grade"] = analysis_data["final_grade"]
                                if "final_recommendation" in analysis_data and "recommendation" not in analysis_data:
                                    analysis_data["recommendation"] = analysis_data["final_recommendation"]

                                # Extract from nested quantitative if needed
                                if "quantitative" in analysis_data and isinstance(analysis_data["quantitative"], dict):
                                    quant = analysis_data["quantitative"]
                                    if "composite_score" not in analysis_data and "composite_score" in quant:
                                        analysis_data["composite_score"] = quant["composite_score"]
                                    if "grade" not in analysis_data and "grade" in quant:
                                        analysis_data["grade"] = quant["grade"]
                                    if "recommendation" not in analysis_data and "preliminary_recommendation" in quant:
                                        analysis_data["recommendation"] = quant["preliminary_recommendation"]

                                ticker = analysis_data.get("ticker")
                                if ticker and ticker not in raw_deep_analysis:  # Avoid duplicates
                                    raw_deep_analysis[ticker] = analysis_data
                                    self.logger.debug(
                                        f"Loaded {ticker} from {json_file}: Score={analysis_data.get('composite_score', 0):.3f}, Grade={analysis_data.get('grade', 'N/A')}"
                                    )
                            except Exception as e:
                                self.logger.warning(f"Failed to load {json_file}: {e}")

            if not raw_deep_analysis:
                self.logger.warning("No deep analysis results found in JSON files")
                return None

            self.logger.info(f"Loaded {len(raw_deep_analysis)} deep analysis results")

            # Transform to expected format
            return self._transform_deep_analysis_results(raw_deep_analysis)

        except Exception as e:
            self.logger.error(f"Failed to read deep analysis from files: {e}")
            return None

    def _transform_deep_analysis_results(
        self,
        raw_deep_analysis: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Transform raw deep analysis results to expected format."""
        successful_count = len(raw_deep_analysis)
        total_holdings = self.state.total_holdings or successful_count
        failed_count = total_holdings - successful_count

        # Calculate average composite score
        scores = [r.get("composite_score", 0.0) for r in raw_deep_analysis.values()]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        return {
            "successful_analyses": successful_count,
            "failed_analyses": failed_count,
            "total_holdings": total_holdings,
            "performance_metrics": {
                "average_composite_score": avg_score,
                "grade_distribution": count_grade_distribution(raw_deep_analysis),
                "analysis_method": "python_scorer",
            },
            "results_by_ticker": {
                ticker: {
                    "ticker": result.get("ticker"),
                    "grade": result.get("grade"),
                    "composite_score": result.get("composite_score", 0.0),
                    "recommendation": result.get("recommendation", "HOLD"),
                    "asset_class": result.get("asset_class"),
                    # Include detailed scores for individual HTML reports
                    "fundamental_score": result.get("fundamental_score", 0.0),
                    "technical_score": result.get("technical_score", 0.0),
                    "risk_score": result.get("risk_score", 0.0),
                    "fundamental_details": result.get("fundamental_details", {}),
                    "technical_details": result.get("technical_details", {}),
                    "risk_details": result.get("risk_details", {}),
                    # Include nested containers for qualitative data (SEC insights, AI analysis)
                    "quantitative": result.get("quantitative", {}),
                    "qualitative": result.get("qualitative", {}),
                    # Include other enriched fields for individual reports
                    "company_name": result.get("company_name", result.get("ticker")),
                    "analysis_date": result.get("analysis_date"),
                }
                for ticker, result in raw_deep_analysis.items()
            },
        }

    def _merge_deep_analysis_into_portfolio(
        self,
        portfolio_review: PortfolioReview,
        deep_analysis_results: dict[str, Any],
    ) -> None:
        """Merge deep analysis results into portfolio review holdings."""
        if "results_by_ticker" not in deep_analysis_results:
            return

        self.logger.info("Merging deep analysis results into portfolio review...")
        merged_count = 0

        for holding in portfolio_review.holdings:
            ticker = holding.ticker
            if ticker in deep_analysis_results["results_by_ticker"]:
                deep_result = deep_analysis_results["results_by_ticker"][ticker]

                # Update holding with deep analysis results
                holding.composite_score = deep_result["composite_score"]
                holding.grade = deep_result["grade"]
                holding.decision = deep_result["recommendation"]
                holding.recommended_action = f"{deep_result['recommendation']} - Analyse approfondie Python"

                # Update rationale with real analysis
                holding.rationale_bullets = [
                    f"📊 Score composite: {deep_result['composite_score']:.3f}",
                    f"🎯 Note: {deep_result['grade']}",
                    f"💡 Recommandation: {deep_result['recommendation']}",
                    "✅ Analyse approfondie Python (déterministe)",
                    f"📈 Classe d'actif: {deep_result['asset_class']}",
                ]
                # Mirror merge.py: mark the holding as analyzed so coverage
                # accounting and the renderer's pending-detection both see
                # the same truth (grade != "N/A").
                holding.crew_analysis_used = "DeepAnalysisOrchestrator"

                merged_count += 1
            else:
                # Mirror merge.py: holdings without a deep-analysis result get
                # explicit "N/A" so the renderer shows "Analyse en attente"
                # instead of leaking decisions.py placeholder D as a real verdict.
                # (PR #21 P1 fix — coverage banner depends on grade != "N/A")
                holding.grade = "N/A"
                # Mirror merge.py: reset the placeholder composite_score=0.6
                # from decisions.py so downstream consumers (sorts, exports,
                # analytics) never see a fabricated 0.6 as a real signal.
                holding.composite_score = 0.0
                holding.grade_description = "Analyse approfondie non disponible"
                holding.recommended_action = "Analyse en attente — ne pas décider sur ce holding"
                holding.rationale_bullets = [
                    "Analyse approfondie non disponible pour ce holding lors de cette exécution.",
                    "Aucun verdict d'investissement n'est rendu — relancer l'analyse pour obtenir un grade.",
                ]
                holding.data_freshness = "stale"

        self.logger.info(f"Merged {merged_count} deep analysis results into portfolio review")

    def _read_json_file(self, file_path: str) -> dict[str, Any]:
        """Read and parse JSON file."""
        with open(file_path, encoding="utf-8") as f:
            result: dict[str, Any] = json.load(f)
            return result

    def _extract_portfolio_review(
        self,
        consolidated_data: dict[str, Any],
    ) -> PortfolioReview:
        """Extract portfolio review from consolidated data."""
        # Implementation depends on consolidated data structure
        # For now, get from state
        portfolio_review_data = self._get_portfolio_review_from_state()
        if not portfolio_review_data:
            raise ValueError("No portfolio review in consolidated data")

        return self._convert_to_portfolio_review(portfolio_review_data)

    def _extract_deep_analysis(
        self,
        consolidated_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Extract deep analysis results from consolidated data."""
        # Check if deep analysis is in consolidated data
        if "deep_analysis" in consolidated_data:
            result: dict[str, Any] | None = consolidated_data["deep_analysis"]
            return result

        # Otherwise read from files
        return self._read_deep_analysis_from_files()

    def _save_merged_portfolio_review(self, portfolio_review: PortfolioReview) -> None:
        """Save the merged portfolio review back to disk."""
        try:
            self.logger.info("Saving merged portfolio review with deep analysis scores...")

            # Save to the standard portfolio review location
            output_path = Path("output/portfolio/portfolio_review.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Use Pydantic's JSON serialization
            portfolio_json = portfolio_review.model_dump_json(indent=2)
            output_path.write_text(portfolio_json, encoding="utf-8")

            self.logger.info(f"✅ Saved merged portfolio review to {output_path}")

            # Log score summary for verification
            scores = [h.composite_score for h in portfolio_review.holdings]
            avg_score = sum(scores) / len(scores) if scores else 0
            self.logger.info(f"📊 Merged portfolio stats: {len(scores)} holdings, avg score: {avg_score:.3f}")

        except Exception as e:
            self.logger.error(f"Failed to save merged portfolio review: {e}", exc_info=True)
