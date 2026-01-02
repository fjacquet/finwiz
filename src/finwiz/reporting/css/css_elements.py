"""Element-specific CSS styles for rebalancing reports."""


def get_base_styles() -> str:
    """Get base CSS styles for rebalancing reports."""
    return """
    /* Rebalancing-specific styles */
    .executive-summary {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
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
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
    }

    .status-indicator.no_action {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }

    .summary-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }

    .metric-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .metric-card h4 {
        margin: 0 0 10px 0;
        font-size: 0.9em;
        color: #666;
        border: none;
    }

    .metric-value {
        font-size: 1.5em;
        font-weight: bold;
        color: #2c3e50;
    }

    .metric-value.positive {
        color: #27ae60;
    }

    .metric-value.negative {
        color: #e74c3c;
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
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .portfolio-table th, .trades-table th, .comparison-table th {
        background: #34495e;
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: 600;
    }

    .portfolio-table td, .trades-table td, .comparison-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #eee;
    }

    .portfolio-table tr:hover, .trades-table tr:hover, .comparison-table tr:hover {
        background-color: #f8f9fa;
    }
    """


def get_action_styles() -> str:
    """Get action and status CSS styles."""
    return """
    /* Action styling */
    .action-buy {
        color: #27ae60;
        font-weight: bold;
    }

    .action-sell {
        color: #e74c3c;
        font-weight: bold;
    }

    .action-hold {
        color: #7f8c8d;
    }

    /* Deviation styling */
    .deviation-high {
        color: #e74c3c;
        font-weight: bold;
    }

    .deviation-medium {
        color: #f39c12;
        font-weight: bold;
    }

    .deviation-low {
        color: #27ae60;
    }

    /* Urgency styling */
    .urgency-urgent {
        color: #e74c3c;
        font-weight: bold;
        background-color: #fdf2f2;
    }

    .urgency-high {
        color: #f39c12;
        font-weight: bold;
    }

    .urgency-medium {
        color: #3498db;
    }

    .urgency-low {
        color: #7f8c8d;
    }

    /* Weight change styling */
    .weight-change.positive {
        color: #27ae60;
    }

    .weight-change.negative {
        color: #e74c3c;
    }

    .weight-change.neutral {
        color: #7f8c8d;
    }
    """


def get_trade_styles() -> str:
    """Get trade details CSS styles."""
    return """
    /* Trade details */
    .trade-details {
        background-color: #f8f9fa;
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
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 4px;
    }

    .tax-implications {
        margin-top: 10px;
        padding: 8px;
        background-color: #e7f3ff;
        border-left: 4px solid #007bff;
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
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        flex: 1;
    }

    .risk-score h4 {
        margin: 0 0 10px 0;
        color: #666;
        border: none;
    }

    .score-value {
        font-size: 2em;
        font-weight: bold;
        color: #2c3e50;
    }

    .risk-arrow {
        font-size: 2em;
        color: #3498db;
    }

    .risk-improvement {
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }

    .risk-improvement.improvement {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
    }

    .risk-improvement.deterioration {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
    }

    .risk-improvement.neutral {
        background-color: #e2e3e5;
        border: 1px solid #d6d8db;
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
        background: white;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .cost-item {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #eee;
    }

    .cost-item.total {
        border-top: 2px solid #34495e;
        border-bottom: none;
        margin-top: 10px;
        font-size: 1.1em;
    }

    .cost-label {
        color: #666;
    }

    .cost-value {
        color: #2c3e50;
        font-weight: 600;
    }

    .cost-metrics {
        margin-top: 15px;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 6px;
    }
    """
