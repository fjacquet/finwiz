"""Layout and interactive CSS styles for rebalancing reports."""


def get_scenario_styles() -> str:
    """Get scenario card CSS styles."""
    return """
    /* Scenario cards */
    .scenario-card {
        background: white;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .scenario-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }

    .scenario-card h4 {
        margin: 0 0 15px 0;
        color: #2c3e50;
        border: none;
    }

    .scenario-metrics {
        display: flex;
        gap: 20px;
        margin-top: 15px;
        flex-wrap: wrap;
    }

    .scenario-metrics .metric {
        padding: 8px 12px;
        background-color: #f8f9fa;
        border-radius: 4px;
        font-size: 0.9em;
    }
    """


def get_execution_styles() -> str:
    """Get execution summary CSS styles."""
    return """
    /* Execution summary */
    .execution-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin: 15px 0;
    }

    .stat-item {
        display: flex;
        justify-content: space-between;
        padding: 12px;
        background: white;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .stat-label {
        color: #666;
        font-weight: 500;
    }

    .stat-value {
        color: #2c3e50;
        font-weight: bold;
    }

    .next-steps {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }

    .next-steps h4 {
        margin: 0 0 15px 0;
        color: #2c3e50;
        border: none;
    }

    .next-steps ol {
        margin: 0;
        padding-left: 20px;
    }

    .next-steps li {
        margin: 8px 0;
        line-height: 1.4;
    }
    """


def get_interactive_styles() -> str:
    """Get interactive element CSS styles."""
    return """
    /* Interactive elements */
    .execute-btn {
        background: #3498db;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9em;
        transition: background-color 0.3s ease;
    }

    .execute-btn:hover {
        background: #2980b9;
    }

    .execute-btn:disabled {
        background: #95a5a6;
        cursor: not-allowed;
    }
    """


def get_responsive_styles() -> str:
    """Get responsive and print CSS styles."""
    return """
    /* Print-friendly styles */
    @media print {
        .execute-btn {
            display: none;
        }

        .section {
            break-inside: avoid;
        }

        .scenario-card {
            break-inside: avoid;
        }

        .next-steps {
            padding-left: 0;
        }

        .next-steps li::before {
            display: none;
        }
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .summary-metrics {
            grid-template-columns: 1fr;
        }

        .risk-scores {
            flex-direction: column;
            gap: 15px;
        }

        .scenario-metrics {
            flex-direction: column;
            gap: 10px;
        }

        .execution-stats {
            grid-template-columns: 1fr;
        }
    }
    """
