"""Layout and interactive CSS styles for rebalancing reports.

Uses CSS variables from the shared design tokens (_design_tokens.html)
for consistent theming across all reports.
"""


def get_scenario_styles() -> str:
    """Get scenario card CSS styles."""
    return """
    /* Scenario cards */
    .scenario-card {
        background: var(--bg-card);
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: var(--shadow-sm);
        cursor: pointer;
        transition: var(--transition);
    }

    .scenario-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    .scenario-card h4 {
        margin: 0 0 15px 0;
        color: var(--text-primary);
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
        background-color: var(--bg-secondary);
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
        background: var(--bg-card);
        border-radius: 6px;
        box-shadow: var(--shadow-sm);
    }

    .stat-label {
        color: var(--text-muted);
        font-weight: 500;
    }

    .stat-value {
        color: var(--text-primary);
        font-weight: bold;
    }

    .next-steps {
        background: var(--bg-secondary);
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }

    .next-steps h4 {
        margin: 0 0 15px 0;
        color: var(--text-primary);
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
        background: var(--accent);
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.9em;
        transition: var(--transition);
    }

    .execute-btn:hover {
        filter: brightness(0.9);
    }

    .execute-btn:disabled {
        background: var(--text-muted);
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
