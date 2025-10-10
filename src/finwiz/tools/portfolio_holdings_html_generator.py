"""
French HTML Report Generator for Portfolio Holdings Analysis.

This module generates comprehensive French HTML reports for portfolio holdings
with price targets, alternatives, position sizing, and A+ improvement roadmap.

Note: Uses f-string HTML generation to match existing codebase patterns.
For future enhancement, consider migrating to BeautifulSoup for better HTML handling.
"""

import logging
from datetime import datetime
from pathlib import Path

from finwiz.schemas.portfolio_review import (
    PortfolioReview,
)

logger = logging.getLogger(__name__)


class PortfolioHoldingsHTMLGenerator:
    """
    Generates French HTML reports for portfolio holdings analysis.

    Follows existing FinWiz HTML generation patterns using f-strings.
    """

    GRADE_COLORS = {
        "A+": "#27ae60",
        "A": "#2ecc71",
        "B+": "#f39c12",
        "B": "#f39c12",
        "C+": "#e67e22",
        "C": "#e67e22",
        "D": "#e74c3c",
        "F": "#c0392b",
    }

    DECISION_EMOJIS = {"KEEP": "✅", "SELL": "❌", "BUY": "🟢"}

    def __init__(self, output_dir: str = "output/portfolio") -> None:
        """Initialize the portfolio holdings HTML generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, portfolio_review: PortfolioReview, title: str = "Analyse de Portefeuille FinWiz") -> str:
        """Generate complete French HTML report for portfolio holdings."""
        logger.info(f"Generating French HTML report with {len(portfolio_review.holdings)} holdings")

        # Generate HTML using f-strings (matching existing codebase pattern)
        html_content = self._build_html_document(title, portfolio_review)

        logger.info("French HTML report generated successfully")
        return html_content

    def save_report(
        self,
        portfolio_review: PortfolioReview,
        filename: str = "portfolio_review_fr.html",
        title: str = "Analyse de Portefeuille FinWiz",
    ) -> Path:
        """Generate and save French HTML report to file."""
        html_content = self.generate_report(portfolio_review, title)
        output_path = self.output_dir / filename

        output_path.write_text(html_content, encoding="utf-8")
        logger.info(f"French HTML report saved to {output_path}")

        return output_path

    def _generate_portfolio_improvement_summary(self, portfolio_review: PortfolioReview) -> str:
        """Generate portfolio improvement summary showing deep vs shallow analysis and grade distribution."""
        # Count deep vs shallow analysis
        deep_count = sum(1 for h in portfolio_review.holdings if h.crew_analysis_used)
        shallow_count = len(portfolio_review.holdings) - deep_count
        
        # Count grade distribution
        grade_counts = {}
        for grade in ["A+", "A", "B", "C", "D", "F"]:
            grade_counts[grade] = sum(1 for h in portfolio_review.holdings if h.grade == grade)
        
        # Count holdings with alternatives
        holdings_with_alternatives = sum(1 for h in portfolio_review.holdings if h.alternatives)
        
        # Calculate potential improvement
        potential_improvement = portfolio_review.portfolio_grade_improvement_potential
        
        # Calculate average risk reduction potential
        avg_risk_reduction = 0.0
        if holdings_with_alternatives > 0:
            risk_reductions = []
            for h in portfolio_review.holdings:
                if h.alternatives:
                    current_risk = h.risk.overall_risk_score
                    for alt in h.alternatives:
                        alt_risk = alt.risk_score if hasattr(alt, 'risk_score') else current_risk
                        risk_reductions.append(max(0, current_risk - alt_risk))
            if risk_reductions:
                avg_risk_reduction = sum(risk_reductions) / len(risk_reductions)
        
        # Build grade distribution bars
        grade_bars = []
        max_count = max(grade_counts.values()) if grade_counts.values() else 1
        for grade in ["A+", "A", "B", "C", "D", "F"]:
            count = grade_counts[grade]
            percentage = (count / len(portfolio_review.holdings) * 100) if portfolio_review.holdings else 0
            color = self.GRADE_COLORS.get(grade, "#95a5a6")
            width = (count / max_count * 100) if max_count > 0 else 0
            grade_bars.append(f"""
                <div style="margin:10px 0">
                    <div style="display:flex;align-items:center;margin-bottom:5px">
                        <span style="width:40px;font-weight:bold">{grade}</span>
                        <div style="flex:1;background:#e0e0e0;height:25px;border-radius:5px;overflow:hidden">
                            <div style="width:{width}%;background:{color};height:100%;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:bold">
                                {count}
                            </div>
                        </div>
                        <span style="width:60px;text-align:right;margin-left:10px">{percentage:.1f}%</span>
                    </div>
                </div>
""")
        
        return f"""
        <div class="improvement-summary">
            <h2>📊 Résumé d'Amélioration du Portefeuille</h2>
            
            <div class="metric-grid">
                <div class="metric-item">
                    <h4>🔍 Analyse Approfondie</h4>
                    <div class="value">{deep_count}</div>
                    <div style="font-size:0.9em;opacity:0.9">sur {len(portfolio_review.holdings)} positions</div>
                </div>
                
                <div class="metric-item">
                    <h4>⚡ Validation Rapide</h4>
                    <div class="value">{shallow_count}</div>
                    <div style="font-size:0.9em;opacity:0.9">positions</div>
                </div>
                
                <div class="metric-item">
                    <h4>💎 Alternatives A+</h4>
                    <div class="value">{holdings_with_alternatives}</div>
                    <div style="font-size:0.9em;opacity:0.9">positions avec alternatives</div>
                </div>
                
                <div class="metric-item">
                    <h4>📈 Amélioration Potentielle</h4>
                    <div class="value">+{potential_improvement:.2f}</div>
                    <div style="font-size:0.9em;opacity:0.9">amélioration de note</div>
                </div>
                
                <div class="metric-item">
                    <h4>🛡️ Réduction du Risque</h4>
                    <div class="value">{avg_risk_reduction:.2f}</div>
                    <div style="font-size:0.9em;opacity:0.9">réduction moyenne estimée</div>
                </div>
            </div>
            
            <div style="margin-top:30px">
                <h3 style="color:#fff;margin-bottom:15px">Distribution des Notes</h3>
                {"".join(grade_bars)}
            </div>
        </div>
"""

    def _generate_data_completeness_section(self, portfolio_review: PortfolioReview) -> str:
        """Generate data completeness section showing which crews ran and data sources."""
        # Count by crew type
        crew_counts = {
            "StockCrew": 0,
            "EtfCrew": 0,
            "CryptoCrew": 0,
            "None": 0
        }
        
        for holding in portfolio_review.holdings:
            if holding.crew_analysis_used:
                crew_name = holding.crew_analysis_used.replace("_", " ").title().replace(" ", "")
                if crew_name in crew_counts:
                    crew_counts[crew_name] += 1
            else:
                crew_counts["None"] += 1
        
        # Count data freshness
        freshness_counts = {"fresh": 0, "recent": 0, "stale": 0}
        for holding in portfolio_review.holdings:
            freshness_counts[holding.data_freshness] += 1
        
        # Build crew status list
        crew_status = []
        for crew_name, count in crew_counts.items():
            if crew_name != "None" and count > 0:
                crew_status.append(f"<li>✅ <strong>{crew_name}</strong>: {count} positions analysées</li>")
        
        if crew_counts["None"] > 0:
            crew_status.append(f"<li>⚡ <strong>Validation Rapide</strong>: {crew_counts['None']} positions</li>")
        
        # Build freshness status
        freshness_status = []
        if freshness_counts["fresh"] > 0:
            freshness_status.append(f"<li>🟢 <strong>Données fraîches</strong>: {freshness_counts['fresh']} positions</li>")
        if freshness_counts["recent"] > 0:
            freshness_status.append(f"<li>🟡 <strong>Données récentes</strong>: {freshness_counts['recent']} positions</li>")
        if freshness_counts["stale"] > 0:
            freshness_status.append(f"<li>🔴 <strong>Données anciennes</strong>: {freshness_counts['stale']} positions</li>")
        
        return f"""
        <div class="data-completeness">
            <h3>📋 Complétude des Données</h3>
            
            <div style="margin:15px 0">
                <h4 style="color:#2c3e50;margin-bottom:10px">Équipes d'Analyse Utilisées</h4>
                <ul>
                    {"".join(crew_status)}
                </ul>
            </div>
            
            <div style="margin:15px 0">
                <h4 style="color:#2c3e50;margin-bottom:10px">Fraîcheur des Données</h4>
                <ul>
                    {"".join(freshness_status)}
                </ul>
            </div>
            
            <div style="margin:15px 0">
                <h4 style="color:#2c3e50;margin-bottom:10px">Sources de Données</h4>
                <ul>
                    <li>📊 Analyse quantitative (métriques financières, indicateurs techniques)</li>
                    <li>📈 Analyse fondamentale (rapports SEC, états financiers)</li>
                    <li>💹 Analyse de sentiment (actualités, tendances du marché)</li>
                    <li>🎯 Système de notation A+ (découverte d'opportunités)</li>
                </ul>
            </div>
        </div>
"""

    def _build_html_document(self, title: str, portfolio_review: PortfolioReview) -> str:
        """Build complete HTML document."""
        css = """
        body{font-family:'Segoe UI',sans-serif;background:#f5f5f5;padding:20px;margin:0}
        .container{max-width:1400px;margin:0 auto;background:#fff;padding:30px;border-radius:10px;"""
        """box-shadow:0 2px 10px rgba(0,0,0,0.1)}
        h1{color:#2c3e50;text-align:center;font-size:2.5em;margin-bottom:10px}
        h2{color:#34495e;margin-top:40px;margin-bottom:20px;padding-bottom:10px;border-bottom:3px solid #3498db}
        h3{color:#2c3e50;margin-top:25px;margin-bottom:15px}
        .header-info{text-align:center;color:#7f8c8d;margin-bottom:30px}
        .dashboard{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:40px}
        .metric-card{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;"""
        """padding:25px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1);transition:transform 0.3s}
        .metric-card:hover{transform:translateY(-5px)}
        .metric-card h3{color:#fff;margin:0 0 10px 0;font-size:1.1em;opacity:0.9}
        .metric-value{font-size:2.5em;font-weight:bold;margin:10px 0}
        .metric-label{font-size:0.9em;opacity:0.8}
        .holdings-table{width:100%;border-collapse:collapse;margin:20px 0;background:#fff;box-shadow:0 2px 4px rgba(0,0,0,0.05)}
        .holdings-table thead{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff}
        .holdings-table th{padding:15px;text-align:left;font-weight:600}
        .holdings-table td{padding:12px 15px;border-bottom:1px solid #ecf0f1}
        .holdings-table tbody tr:hover{background-color:#f8f9fa}
        .grade-badge{display:inline-block;padding:5px 12px;border-radius:20px;font-weight:bold;color:#fff}
        .decision-keep{background-color:#d5f4e6;color:#27ae60;padding:5px 12px;border-radius:5px;font-weight:600}
        .decision-sell{background-color:#fadbd8;color:#e74c3c;padding:5px 12px;border-radius:5px;font-weight:600}
        .deep-analysis{background-color:#e8f5e9;color:#2e7d32;padding:5px 10px;border-radius:5px;font-weight:600;font-size:0.9em}
        .quick-validation{background-color:#fff3e0;color:#ef6c00;padding:5px 10px;border-radius:5px;font-weight:600;font-size:0.9em}
        .roadmap-section{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);"""
        """color:#fff;padding:30px;border-radius:10px;margin:30px 0}
        .roadmap-section h2{color:#fff;border-bottom-color:rgba(255,255,255,0.3)}
        .roadmap-phase{background:rgba(255,255,255,0.1);padding:20px;border-radius:8px;margin:15px 0;border-left:4px solid #fff}
        .roadmap-phase h3{color:#fff;margin-top:0}
        .data-completeness{background:#f8f9fa;padding:20px;border-radius:8px;margin:20px 0;border-left:4px solid #3498db}
        .data-completeness h3{margin-top:0;color:#2c3e50}
        .data-completeness ul{margin:10px 0;padding-left:20px}
        .data-completeness li{margin:5px 0;color:#34495e}
        .improvement-summary{background:linear-gradient(135deg,#11998e 0%,#38ef7d 100%);color:#fff;"""
        """padding:25px;border-radius:10px;margin:30px 0}
        .improvement-summary h2{color:#fff;border-bottom-color:rgba(255,255,255,0.3)}
        .improvement-summary .metric-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-top:20px}
        .improvement-summary .metric-item{background:rgba(255,255,255,0.15);padding:15px;border-radius:8px}
        .improvement-summary .metric-item h4{margin:0 0 10px 0;font-size:0.9em;opacity:0.9}
        .improvement-summary .metric-item .value{font-size:2em;font-weight:bold}
        .alternatives-expandable{background:#f8f9fa;padding:15px;border-radius:8px;margin:10px 0;border-left:4px solid #9b59b6}
        .alternatives-expandable h4{margin:0 0 10px 0;color:#2c3e50;cursor:pointer}
        .alternatives-expandable h4:hover{color:#9b59b6}
        .alternatives-content{margin-top:10px}
        .alternative-item{background:#fff;padding:12px;margin:8px 0;border-radius:5px;border:1px solid #e0e0e0}
        .alternative-item .improvement{color:#27ae60;font-weight:600;font-size:1.1em}
        .footer{margin-top:50px;padding-top:20px;border-top:2px solid #ecf0f1;text-align:center;color:#95a5a6;font-size:0.9em}
        @media print{body{background:#fff;padding:0}.container{box-shadow:none}}
        @media (max-width: 768px){.dashboard{grid-template-columns:1fr}h1{font-size:1.8em}}
        """

        return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        {self._generate_header(title, portfolio_review)}
        {self._generate_dashboard(portfolio_review)}
        {self._generate_portfolio_improvement_summary(portfolio_review)}
        {self._generate_holdings_table(portfolio_review)}
        {self._generate_price_targets_section(portfolio_review)}
        {self._generate_alternatives_section(portfolio_review)}
        {self._generate_aplus_roadmap(portfolio_review)}
        {self._generate_data_completeness_section(portfolio_review)}
        {self._generate_footer()}
    </div>
</body>
</html>"""

    def _generate_header(self, title: str, portfolio_review: PortfolioReview) -> str:
        """Generate report header."""
        current_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
        return f"""
        <h1>📊 {title}</h1>
        <div class="header-info">
            <p><strong>Date du rapport:</strong> {current_date}</p>
            <p><strong>Devise de base:</strong> {portfolio_review.base_currency}</p>
            <p><strong>Nombre de positions:</strong> {len(portfolio_review.holdings)}</p>
        </div>
"""

    def _generate_dashboard(self, portfolio_review: PortfolioReview) -> str:
        """Generate portfolio dashboard with key metrics."""
        total = len(portfolio_review.holdings)
        aplus = portfolio_review.current_a_plus_holdings_count
        potential = portfolio_review.potential_a_plus_holdings_count
        keep = sum(1 for h in portfolio_review.holdings if h.decision == "KEEP")
        sell = sum(1 for h in portfolio_review.holdings if h.decision == "SELL")
        avg = sum(h.composite_score for h in portfolio_review.holdings) / total if total > 0 else 0

        return f"""
        <h2>📈 Tableau de Bord du Portefeuille</h2>
        <div class="dashboard">
            <div class="metric-card">
                <h3>💼 Total des Positions</h3>
                <div class="metric-value">{total}</div>
                <div class="metric-label">positions analysées</div>
            </div>
            <div class="metric-card">
                <h3>💎 Positions A+</h3>
                <div class="metric-value">{aplus}</div>
                <div class="metric-label">actuelles / {potential} potentielles</div>
            </div>
            <div class="metric-card">
                <h3>💰 Score Moyen</h3>
                <div class="metric-value">{avg:.2f}</div>
                <div class="metric-label">sur 1.00</div>
            </div>
            <div class="metric-card">
                <h3>✅ Décisions</h3>
                <div class="metric-value">{keep} / {sell}</div>
                <div class="metric-label">conserver / vendre</div>
            </div>
        </div>
"""

    def _generate_holdings_table(self, portfolio_review: PortfolioReview) -> str:
        """Generate holdings table with deep analysis indicators and detailed metrics."""
        rows = []
        for idx, holding in enumerate(portfolio_review.holdings, 1):
            color = self.GRADE_COLORS.get(holding.grade, "#95a5a6")
            emoji = self.DECISION_EMOJIS.get(holding.decision, "")
            css_class = f"decision-{holding.decision.lower()}"

            # Determine analysis depth indicator
            if holding.crew_analysis_used:
                analysis_indicator = "🔍 Deep Analysis"
                analysis_class = "deep-analysis"
                crew_name = holding.crew_analysis_used.replace("_", " ").title()
            else:
                analysis_indicator = "⚡ Quick Validation"
                analysis_class = "quick-validation"
                crew_name = "N/A"

            # Format analysis date
            analysis_date_str = holding.analysis_date.strftime("%d/%m/%Y") if holding.analysis_date else "N/A"

            # Data freshness indicator
            freshness_emoji = {"fresh": "🟢", "recent": "🟡", "stale": "🔴"}.get(holding.data_freshness, "⚪")
            freshness_label = {"fresh": "Frais", "recent": "Récent", "stale": "Ancien"}.get(holding.data_freshness, "Inconnu")

            # Risk score display
            risk_score = holding.risk.score
            risk_color = "#27ae60" if risk_score <= 2 else "#f39c12" if risk_score <= 3.5 else "#e74c3c"

            rows.append(f"""
            <tr>
                <td>{idx}</td>
                <td><strong>{holding.ticker}</strong><br><small>{holding.name}</small></td>
                <td><span class="grade-badge" style="background-color:{color}">{holding.grade}</span><br>
                    <small style="color:#666">{holding.grade_description}</small></td>
                <td><strong>{holding.composite_score:.2f}</strong><br>
                    <small style="color:{risk_color}">🛡️ Risque: {risk_score:.1f}/5</small></td>
                <td><span class="{css_class}">{emoji} {holding.decision}</span><br>
                    <small style="color:#666">{holding.recommended_action}</small></td>
                <td><span class="{analysis_class}">{analysis_indicator}</span><br>
                    <small>{crew_name}</small></td>
                <td>{freshness_emoji} {freshness_label}<br><small>{analysis_date_str}</small></td>
                <td>{holding.currency}</td>
            </tr>
""")

        return f"""
        <h2>📋 Analyse Détaillée des Positions</h2>
        <table class="holdings-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Titre</th>
                    <th>Note</th>
                    <th>Score Composite</th>
                    <th>Décision</th>
                    <th>Type d'Analyse</th>
                    <th>Fraîcheur</th>
                    <th>Devise</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
        <div style="margin-top:10px;padding:15px;background:#f8f9fa;border-radius:5px">
            <p style="margin:0;color:#666;font-size:0.9em">
                <strong>Légende:</strong> 
                🔍 = Analyse approfondie par équipe spécialisée | 
                ⚡ = Validation rapide | 
                🟢 = Données fraîches (< 24h) | 
                🟡 = Données récentes (< 7j) | 
                🔴 = Données anciennes (> 7j)
            </p>
        </div>
"""

    def _generate_aplus_roadmap(self, portfolio_review: PortfolioReview) -> str:
        """Generate A+ improvement roadmap section."""
        aplus = portfolio_review.a_plus_opportunities

        if aplus.total_opportunities_found == 0:
            return """
        <div class="roadmap-section">
            <h2>💎 Feuille de Route d'Amélioration A+</h2>
            <p>Aucune opportunité d'amélioration A+ identifiée pour le moment.</p>
            <p>Votre portefeuille est déjà bien optimisé! 🎉</p>
        </div>
"""

        return f"""
        <div class="roadmap-section">
            <h2>💎 Feuille de Route d'Amélioration A+</h2>
            <div class="roadmap-phase">
                <h3>📊 Vue d'Ensemble</h3>
                <ul>
                    <li><strong>{aplus.total_opportunities_found}</strong> opportunités A+ identifiées</li>
                    <li><strong>{aplus.high_priority_opportunities}</strong> opportunités haute priorité</li>
                    <li>Amélioration potentielle: <strong>+{aplus.expected_portfolio_grade_improvement:.2f}</strong></li>
                </ul>
            </div>
        </div>
"""

    def _generate_footer(self) -> str:
        """Generate report footer."""
        return """
        <div class="footer">
            <p><strong>Avertissement:</strong> Ce rapport est généré par FinWiz AI et est à des fins d'information uniquement.</p>
            <p>Veuillez consulter un conseiller financier qualifié avant de prendre des décisions d'investissement.</p>
            <p>© 2025 FinWiz - Système d'Analyse de Portefeuille</p>
        </div>
"""

    def _generate_price_targets_section(self, portfolio_review: PortfolioReview) -> str:
        """Generate price targets section for holdings with targets."""
        holdings_with_targets = [h for h in portfolio_review.holdings if h.price_targets]

        if not holdings_with_targets:
            return ""

        target_rows = []
        for holding in holdings_with_targets:
            targets = holding.price_targets
            fair_value = f"{targets.fair_value_estimate:.2f}" if targets.fair_value_estimate else "N/A"
            buy_target = f"{targets.buy_target_primary:.2f}" if targets.buy_target_primary else "N/A"
            sell_target = f"{targets.sell_target_primary:.2f}" if targets.sell_target_primary else "N/A"
            stop_loss = f"{targets.stop_loss_level:.2f}" if targets.stop_loss_level else "N/A"

            target_rows.append(f"""
            <tr>
                <td><strong>{holding.ticker}</strong></td>
                <td>{targets.current_price:.2f} {targets.currency}</td>
                <td>{fair_value}</td>
                <td>{buy_target}</td>
                <td>{sell_target}</td>
                <td>{stop_loss}</td>
            </tr>
""")

        return f"""
        <h2>🎯 Objectifs de Prix</h2>
        <table class="holdings-table">
            <thead>
                <tr>
                    <th>Titre</th>
                    <th>Prix actuel</th>
                    <th>Valeur juste</th>
                    <th>Achat</th>
                    <th>Vente</th>
                    <th>Stop-loss</th>
                </tr>
            </thead>
            <tbody>
                {"".join(target_rows)}
            </tbody>
        </table>
"""

    def _generate_alternatives_section(self, portfolio_review: PortfolioReview) -> str:
        """Generate alternatives section for holdings with alternatives showing grade improvements."""
        holdings_with_alternatives = [h for h in portfolio_review.holdings if h.alternatives]

        if not holdings_with_alternatives:
            return ""

        alt_sections = []
        for holding in holdings_with_alternatives:
            holding_color = self.GRADE_COLORS.get(holding.grade, "#95a5a6")
            
            alt_items = []
            for alt in holding.alternatives:
                alt_color = self.GRADE_COLORS.get(alt.grade, "#95a5a6")
                score_improvement = alt.composite_score - holding.composite_score
                improvement_text = f"{holding.grade} → {alt.grade}, +{score_improvement:.2f} amélioration du score"
                
                # Extract rationale (first 200 chars)
                rationale_preview = alt.rationale[:200] + "..." if len(alt.rationale) > 200 else alt.rationale
                
                alt_items.append(f"""
                <div class="alternative-item">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                        <div>
                            <strong style="font-size:1.1em">{alt.ticker}</strong> - {alt.name}
                        </div>
                        <span class="grade-badge" style="background-color:{alt_color}">{alt.grade}</span>
                    </div>
                    <div class="improvement">{improvement_text}</div>
                    <div style="margin:10px 0"><strong>Score:</strong> {alt.composite_score:.2f}</div>
                    <div style="margin:10px 0"><strong>Stratégie:</strong> {alt.transition_strategy}</div>
                    <div style="margin:10px 0;color:#555"><strong>Justification:</strong> {rationale_preview}</div>
                </div>
""")

            alt_sections.append(f"""
            <div class="alternatives-expandable">
                <h4>🔄 Alternatives pour {holding.ticker} 
                    <span class="grade-badge" style="background-color:{holding_color};margin-left:10px">{holding.grade}</span>
                    <span style="font-size:0.9em;color:#666;margin-left:10px">({len(holding.alternatives)} alternatives A+)</span>
                </h4>
                <div class="alternatives-content">
                    {"".join(alt_items)}
                </div>
            </div>
""")

        return f"""
        <h2>🔄 Alternatives Recommandées</h2>
        <p style="color:#555;margin-bottom:20px">
            Alternatives A+ identifiées pour les positions sous-performantes (note C ou inférieure).
            Ces recommandations sont basées sur l'analyse approfondie des équipes d'analyse.
        </p>
        {"".join(alt_sections)}
"""


def generate_portfolio_holdings_report(
    portfolio_review: PortfolioReview,
    output_dir: str = "output/portfolio",
    filename: str = "portfolio_review_fr.html",
    title: str = "Analyse de Portefeuille FinWiz",
) -> Path:
    """Generate and save portfolio holdings HTML report."""
    generator = PortfolioHoldingsHTMLGenerator(output_dir=output_dir)
    return generator.save_report(portfolio_review, filename=filename, title=title)
