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
        .roadmap-section{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);"""
        """color:#fff;padding:30px;border-radius:10px;margin:30px 0}
        .roadmap-section h2{color:#fff;border-bottom-color:rgba(255,255,255,0.3)}
        .roadmap-phase{background:rgba(255,255,255,0.1);padding:20px;border-radius:8px;margin:15px 0;border-left:4px solid #fff}
        .roadmap-phase h3{color:#fff;margin-top:0}
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
        {self._generate_holdings_table(portfolio_review)}
        {self._generate_price_targets_section(portfolio_review)}
        {self._generate_alternatives_section(portfolio_review)}
        {self._generate_aplus_roadmap(portfolio_review)}
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
        """Generate holdings table."""
        rows = []
        for idx, holding in enumerate(portfolio_review.holdings, 1):
            color = self.GRADE_COLORS.get(holding.grade, "#95a5a6")
            emoji = self.DECISION_EMOJIS.get(holding.decision, "")
            css_class = f"decision-{holding.decision.lower()}"

            rows.append(f"""
            <tr>
                <td>{idx}</td>
                <td><strong>{holding.ticker}</strong><br><small>{holding.name}</small></td>
                <td><span class="grade-badge" style="background-color:{color}">{holding.grade}</span></td>
                <td>{holding.composite_score:.2f}</td>
                <td><span class="{css_class}">{emoji} {holding.decision}</span></td>
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
                    <th>Score</th>
                    <th>Décision</th>
                    <th>Devise</th>
                </tr>
            </thead>
            <tbody>
                {"".join(rows)}
            </tbody>
        </table>
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
        """Generate alternatives section for holdings with alternatives."""
        holdings_with_alternatives = [h for h in portfolio_review.holdings if h.alternatives]

        if not holdings_with_alternatives:
            return ""

        alt_sections = []
        for holding in holdings_with_alternatives:
            alt_rows = []
            for alt in holding.alternatives:
                color = self.GRADE_COLORS.get(alt.grade, "#95a5a6")
                alt_rows.append(f"""
                <tr>
                    <td><strong>{alt.ticker}</strong><br><small>{alt.name}</small></td>
                    <td><span class="grade-badge" style="background-color:{color}">{alt.grade}</span></td>
                    <td>{alt.composite_score:.2f}</td>
                    <td>{alt.transition_strategy}</td>
                </tr>
""")

            alt_sections.append(f"""
            <h3>Alternatives pour {holding.ticker}</h3>
            <table class="holdings-table">
                <thead>
                    <tr>
                        <th>Alternative</th>
                        <th>Note</th>
                        <th>Score</th>
                        <th>Stratégie de transition</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(alt_rows)}
                </tbody>
            </table>
""")

        return f"""
        <h2>🔄 Alternatives Recommandées</h2>
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
