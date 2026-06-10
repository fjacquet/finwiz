
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
