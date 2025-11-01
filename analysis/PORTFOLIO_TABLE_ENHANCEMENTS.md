# Portfolio Table Enhancements

## Changes Made

### 1. Added "Prix Actuel" (Current Price) Column

**Location**: `src/finwiz/crews/report_crew/config/tasks.yaml`

**What Changed**:
- Added a new column "Prix Actuel" to the portfolio holdings table
- The price is extracted from `inputs.deep_analysis_html_content[ticker]['current_price']`
- If price is not available, displays "N/A" or "Prix non disponible"

**Table Structure** (updated):
```
Ticker / Nom | Classe | Note | Score | Prix Actuel | Recommandation | Rationale | Statut Validation
```

### 2. Made Table Sortable by Any Column

**Implementation**: JavaScript-based interactive sorting

**Features**:
- **Click any column header** to sort by that column
- **Three-state sorting**:
  1. First click: Ascending order (↑)
  2. Second click: Descending order (↓)
  3. Third click: Return to original order
- **Visual indicators**: Arrows (↑↓) show sortable columns, active sort direction highlighted
- **Smart sorting**:
  - Numeric columns (Score, Prix Actuel): Sorted numerically
  - Grade column: Sorted by grade value (A+ > A > A- > B+ > B > B- > C+ > C > C- > D > F)
  - Text columns: Sorted alphabetically (French locale)

**Grade Sort Values**:
```
A+ = 10.0
A  = 9.0
A- = 8.5
B+ = 8.0
B  = 7.0
B- = 6.5
C+ = 6.0
C  = 5.0
C- = 4.5
D  = 3.0
F  = 0.0
```

### 3. HTML Structure Example

```html
<table id="portfolio-table" class="sortable-table">
  <thead>
    <tr>
      <th class="sortable" onclick="sortTable(0)">Ticker / Nom ↑↓</th>
      <th class="sortable" onclick="sortTable(1)">Classe ↑↓</th>
      <th class="sortable" onclick="sortTable(2)">Note ↑↓</th>
      <th class="sortable" onclick="sortTable(3)">Score ↑↓</th>
      <th class="sortable" onclick="sortTable(4)">Prix Actuel ↑↓</th>
      <th class="sortable" onclick="sortTable(5)">Recommandation ↑↓</th>
      <th>Rationale</th>
      <th>Statut</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>AAPL</strong><br><small>Apple Inc.</small></td>
      <td>STOCK</td>
      <td class="grade-a-minus" data-sort-value="8.5"><strong>A-</strong></td>
      <td data-sort-value="0.82">0.820</td>
      <td data-sort-value="150.25">$150.25</td>
      <td><span class="badge badge-hold">CONSERVER</span></td>
      <td><small>Strong fundamentals...</small></td>
      <td>✅ Validé</td>
    </tr>
  </tbody>
</table>
```

### 4. JavaScript Implementation

**Key Functions**:
- `sortTable(columnIndex)`: Main sorting function
- Maintains `sortState` object to track current sort state per column
- Stores `originalOrder` array to restore initial order
- Uses `data-sort-value` attribute for numeric/grade sorting
- Falls back to text content for text-based sorting

**CSS Styling**:
- `.sortable`: Cursor pointer, hover effect
- `.sort-asc::after`: Shows ↑ arrow
- `.sort-desc::after`: Shows ↓ arrow
- Highlighted column when sorted

## How It Works

### For the AI Agent (investment_reporter)

The task configuration now instructs the agent to:

1. **Extract current price** from `inputs.deep_analysis_html_content[ticker]['current_price']`
2. **Add data-sort-value attributes** to cells for proper sorting:
   - Grades: Use numeric values (A+ = 10.0, A = 9.0, etc.)
   - Scores: Use the actual numeric value
   - Prices: Use the numeric price value
3. **Include the JavaScript sorting code** in the HTML output
4. **Include the CSS styling** for sortable tables
5. **Make headers clickable** with `onclick="sortTable(columnIndex)"`

### For Users

Users can now:
- **Click any column header** to sort the portfolio table
- **See visual indicators** (↑↓) showing which columns are sortable
- **Sort by price** to see most/least expensive holdings
- **Sort by grade** to see best/worst performing assets
- **Sort by score** to see highest/lowest composite scores
- **Return to original order** by clicking the same header three times

## Testing

To test the changes:

1. Run the FinWiz flow to generate a new report
2. Open the HTML report in a browser
3. Click on different column headers in the portfolio table
4. Verify:
   - Current price column is displayed
   - Sorting works correctly for all columns
   - Visual indicators (arrows) appear
   - Three-state sorting works (asc → desc → original)

## Files Modified

- `src/finwiz/crews/report_crew/config/tasks.yaml`: Updated task description with new requirements

## Next Steps

The AI agent will automatically implement these changes in the next report generation. No code changes are needed - the task configuration guides the agent to generate the enhanced HTML table.
