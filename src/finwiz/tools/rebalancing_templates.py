"""
Template management for rebalancing reports.

This module contains CSS styles, JavaScript code, and HTML templates
for portfolio rebalancing reports.
"""

import logging

logger = logging.getLogger(__name__)


class RebalancingTemplates:
    """Template and styling management for rebalancing reports."""

    @staticmethod
    def get_rebalancing_css() -> str:
        """
        Get CSS styles for rebalancing reports.

        Returns:
            CSS styles as string

        """
        return """
        <style>
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
        </style>
        """

    @staticmethod
    def get_rebalancing_javascript() -> str:
        """
        Get JavaScript code for rebalancing reports.

        Returns:
            JavaScript code as string

        """
        return """
        <script>
        function executeTradeDialog(symbol, action, quantity, price) {
            const message = `Execute ${action} order for ${quantity} shares of ${symbol} at ${price.toFixed(2)}?`;

            if (confirm(message)) {
                // In a real implementation, this would integrate with a broker API
                alert(`Trade order submitted for ${symbol}. This is a demo - no actual trade was executed.`);

                // Disable the button to prevent duplicate orders
                event.target.disabled = true;
                event.target.textContent = 'Submitted';
                event.target.style.backgroundColor = '#95a5a6';
            }
        }

        // Add click handlers for scenario comparison
        document.addEventListener('DOMContentLoaded', function() {
            const scenarioCards = document.querySelectorAll('.scenario-card');
            scenarioCards.forEach(card => {
                card.addEventListener('click', function() {
                    // Toggle selection
                    this.classList.toggle('selected');

                    // Update styling
                    if (this.classList.contains('selected')) {
                        this.style.borderLeft = '4px solid #3498db';
                        this.style.backgroundColor = '#f8f9fa';
                    } else {
                        this.style.borderLeft = 'none';
                        this.style.backgroundColor = 'white';
                    }
                });
            });

            // Add trade row highlighting
            const tradeRows = document.querySelectorAll('.trade-row');
            tradeRows.forEach(row => {
                row.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#e3f2fd';
                });
                
                row.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = '';
                });
            });

            // Add portfolio table sorting (basic implementation)
            const tables = document.querySelectorAll('.portfolio-table, .trades-table, .comparison-table');
            tables.forEach(table => {
                const headers = table.querySelectorAll('th');
                headers.forEach((header, index) => {
                    header.style.cursor = 'pointer';
                    header.addEventListener('click', function() {
                        sortTable(table, index);
                    });
                });
            });
        });

        function sortTable(table, columnIndex) {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Determine sort direction
            const isAscending = table.dataset.sortDirection !== 'asc';
            table.dataset.sortDirection = isAscending ? 'asc' : 'desc';
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.cells[columnIndex].textContent.trim();
                const bValue = b.cells[columnIndex].textContent.trim();
                
                // Try to parse as numbers
                const aNum = parseFloat(aValue.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bValue.replace(/[^0-9.-]/g, ''));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAscending ? aNum - bNum : bNum - aNum;
                } else {
                    return isAscending ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
                }
            });
            
            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
            
            // Update header indicators
            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                header.classList.remove('sort-asc', 'sort-desc');
                if (index === columnIndex) {
                    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
                }
            });
        }

        // Utility function for formatting numbers
        function formatCurrency(amount) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD'
            }).format(amount);
        }

        function formatPercentage(value) {
            return new Intl.NumberFormat('en-US', {
                style: 'percent',
                minimumFractionDigits: 1,
                maximumFractionDigits: 1
            }).format(value / 100);
        }
        </script>
        """

    @staticmethod
    def get_pdf_export_note() -> str:
        """
        Get PDF export note for HTML reports.

        Returns:
            HTML comment with PDF export instructions

        """
        return """
        <!-- PDF Export Note -->
        <!-- This HTML report can be converted to PDF using tools like: -->
        <!-- - weasyprint: pip install weasyprint -->
        <!-- - pdfkit: pip install pdfkit (requires wkhtmltopdf) -->
        <!-- - playwright: pip install playwright -->
        <!-- Example: weasyprint report.html report.pdf -->
        """

    @staticmethod
    def add_interactive_elements(html_content: str) -> str:
        """
        Add interactive CSS and JavaScript to HTML content.

        Args:
            html_content: Original HTML content

        Returns:
            HTML content with interactive elements added

        """
        css = RebalancingTemplates.get_rebalancing_css()
        js = RebalancingTemplates.get_rebalancing_javascript()

        # Insert the enhanced CSS and JavaScript before the closing </head> tag
        head_close_index = html_content.find("</head>")
        if head_close_index != -1:
            html_content = html_content[:head_close_index] + css + js + html_content[head_close_index:]

        return html_content

    @staticmethod
    def prepare_pdf_export(html_content: str) -> str:
        """
        Prepare HTML content for PDF export.

        Args:
            html_content: Original HTML content

        Returns:
            HTML content prepared for PDF conversion

        """
        pdf_note = RebalancingTemplates.get_pdf_export_note()
        return html_content.replace("</head>", f"{pdf_note}</head>")
