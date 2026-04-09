"""Element-specific CSS styles for rebalancing reports.

Uses CSS variables from the shared design tokens (_design_tokens.html)
for consistent theming across all reports.
"""


def get_base_styles() -> str:
    """Get base CSS styles for rebalancing reports."""
    return """
    /* Rebalancing-specific styles */
    .executive-summary {
        background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .status-indicator {
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }

    .status-indicator.rebalance_now {
        background-color: rgba(253, 126, 20, 0.15);
        border: 1px solid var(--warning);
    }

    .status-indicator.no_action {
        background-color: rgba(25, 135, 84, 0.15);
        border: 1px solid var(--success);
    }

    .summary-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }

    .metric-card {
        background: var(--bg-card);
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        box-shadow: var(--shadow-sm);
    }

    .metric-card h4 {
        margin: 0 0 10px 0;
        font-size: 0.9em;
        color: var(--text-muted);
        border: none;
    }

    .metric-value {
        font-size: 1.5em;
        font-weight: bold;
        color: var(--text-primary);
    }

    .metric-value.positive {
        color: var(--success);
    }

    .metric-value.negative {
        color: var(--danger);
    }
    """


def get_table_styles() -> str:
    """Get table CSS styles."""
    return """
    /* Table styles */
    .portfolio-table, .trades-table, .comparison-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        background: var(--bg-card);
        border-radius: 8px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }

    .portfolio-table th, .trades-table th, .comparison-table th {
        background: var(--text-secondary);
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: 600;
    }

    .portfolio-table td, .trades-table td, .comparison-table td {
        padding: 10px 12px;
        border-bottom: 1px solid var(--border-color);
    }

    .portfolio-table tr:hover, .trades-table tr:hover, .comparison-table tr:hover {
        background-color: var(--bg-secondary);
    }
    """


def get_action_styles() -> str:
    """Get action and status CSS styles."""
    return """
    /* Action styling */
    .action-buy {
        color: var(--success);
        font-weight: bold;
    }

    .action-sell {
        color: var(--danger);
        font-weight: bold;
    }

    .action-hold {
        color: var(--text-muted);
    }

    /* Deviation styling */
    .deviation-high {
        color: var(--danger);
        font-weight: bold;
    }

    .deviation-medium {
        color: var(--warning);
        font-weight: bold;
    }

    .deviation-low {
        color: var(--success);
    }

    /* Urgency styling */
    .urgency-urgent {
        color: var(--danger);
        font-weight: bold;
        background-color: rgba(220, 53, 69, 0.05);
    }

    .urgency-high {
        color: var(--warning);
        font-weight: bold;
    }

    .urgency-medium {
        color: var(--accent);
    }

    .urgency-low {
        color: var(--text-muted);
    }

    /* Weight change styling */
    .weight-change.positive {
        color: var(--success);
    }

    .weight-change.negative {
        color: var(--danger);
    }

    .weight-change.neutral {
        color: var(--text-muted);
    }
    """


def get_trade_styles() -> str:
    """Get trade details CSS styles."""
    return """
    /* Trade details */
    .trade-details {
        background-color: var(--bg-secondary);
    }

    .trade-rationale {
        padding: 15px;
        font-size: 0.9em;
        line-height: 1.4;
    }

    .rationale-content {
        max-width: 100%;
    }

    .market-warning {
        margin-top: 10px;
        padding: 8px;
        background-color: rgba(253, 126, 20, 0.15);
        border-left: 4px solid var(--warning);
        border-radius: 4px;
    }

    .tax-implications {
        margin-top: 10px;
        padding: 8px;
        background-color: rgba(13, 110, 253, 0.1);
        border-left: 4px solid var(--accent);
        border-radius: 4px;
    }
    """


def get_risk_styles() -> str:
    """Get risk analysis CSS styles."""
    return """
    /* Risk analysis */
    .risk-scores {
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin: 20px 0;
        gap: 20px;
    }

    .risk-score {
        text-align: center;
        padding: 20px;
        border-radius: 10px;
        background: var(--bg-card);
        box-shadow: var(--shadow-sm);
        flex: 1;
    }

    .risk-score h4 {
        margin: 0 0 10px 0;
        color: var(--text-muted);
        border: none;
    }

    .score-value {
        font-size: 2em;
        font-weight: bold;
        color: var(--text-primary);
    }

    .risk-arrow {
        font-size: 2em;
        color: var(--accent);
    }

    .risk-improvement {
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }

    .risk-improvement.improvement {
        background-color: rgba(25, 135, 84, 0.15);
        border: 1px solid var(--success);
    }

    .risk-improvement.deterioration {
        background-color: rgba(220, 53, 69, 0.1);
        border: 1px solid var(--danger);
    }

    .risk-improvement.neutral {
        background-color: var(--bg-tertiary);
        border: 1px solid var(--border-color);
    }

    .risk-value {
        font-weight: bold;
        font-size: 1.1em;
    }
    """


def get_cost_styles() -> str:
    """Get cost analysis CSS styles."""
    return """
    /* Cost analysis */
    .cost-breakdown {
        background: var(--bg-card);
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: var(--shadow-sm);
    }

    .cost-item {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid var(--border-color);
    }

    .cost-item.total {
        border-top: 2px solid var(--text-secondary);
        border-bottom: none;
        margin-top: 10px;
        font-size: 1.1em;
    }

    .cost-label {
        color: var(--text-muted);
    }

    .cost-value {
        color: var(--text-primary);
        font-weight: 600;
    }

    .cost-metrics {
        margin-top: 15px;
        padding: 15px;
        background-color: var(--bg-secondary);
        border-radius: 6px;
    }
    """
