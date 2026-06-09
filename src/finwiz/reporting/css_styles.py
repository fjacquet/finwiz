"""
CSS styles for Python report generation.

This module contains all CSS styling for HTML reports, extracted
from the monolithic PythonReportGenerator for maintainability.
"""


def get_report_css() -> str:
    """
    Get CSS styles for the report.

    Returns:
        Complete CSS stylesheet as a string for financial reports
        with light mode, dark mode, responsive design, and
        grade/badge styling.
    """
    return """
    :root {
      --bg: #f5f7fa;
      --card: #ffffff;
      --ink: #1e293b;
      --ink-soft: #475569;
      --muted: #64748b;
      --line: #e9eef4;
      --line-soft: #eef2f7;
      --accent: #059669;
      --accent-strong: #047857;
      --accent-soft: #ecfdf5;
      --shadow: 0 1px 2px rgba(15,23,42,0.04), 0 8px 24px rgba(15,23,42,0.06);
      --radius: 14px;
    }
    * { box-sizing: border-box; }
    body {
      font-family: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.6;
      color: var(--ink);
      margin: 0;
      padding: 28px;
      max-width: 1180px;
      margin-left: auto;
      margin-right: auto;
      background: var(--bg);
      -webkit-font-smoothing: antialiased;
    }
    header {
      background: var(--card);
      color: var(--ink);
      padding: 32px 34px;
      border-radius: var(--radius);
      margin-bottom: 26px;
      box-shadow: var(--shadow);
      border-left: 4px solid var(--accent);
    }
    h1 { margin: 0 0 8px 0; font-size: 1.9rem; font-weight: 700; letter-spacing: -0.02em; }
    h2 {
      color: var(--ink);
      margin: 0 0 18px 0;
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--line);
    }
    h3 { color: var(--ink-soft); margin: 22px 0 10px 0; font-size: 1.02rem; font-weight: 600; }
    h4 { color: var(--ink-soft); font-size: 0.9rem; font-weight: 600; }
    .section {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 26px 28px;
      margin-bottom: 22px;
      box-shadow: var(--shadow);
    }
    .muted { color: var(--muted); font-size: 0.9em; }
    .small { font-size: 0.85em; }
    .num { text-align: right; font-variant-numeric: tabular-nums; }

    table {
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0;
      background: transparent;
      font-size: 0.92rem;
    }
    th, td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--line-soft);
      vertical-align: top;
    }
    th {
      background: #f8fafc;
      color: var(--muted);
      font-weight: 600;
      font-size: 0.72rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      border-bottom: 1px solid var(--line);
    }
    tbody tr { transition: background 0.15s ease; }
    tbody tr:hover { background: var(--accent-soft); }
    td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }

    .grade-a-plus { color: var(--accent-strong); font-weight: 700; }
    .grade-a { color: var(--accent); font-weight: 700; }
    .grade-b { color: #ca8a04; font-weight: 700; }
    .grade-c { color: #d97706; font-weight: 700; }
    .grade-d { color: #dc2626; font-weight: 700; }
    .grade-f { color: #b91c1c; font-weight: 700; }
    .grade-na { color: var(--muted); font-weight: 600; }

    .ticker-link {
      color: var(--accent-strong);
      text-decoration: none;
      border-bottom: 1px dashed #34d39966;
      transition: all 0.18s ease;
      font-weight: 600;
    }
    .ticker-link:hover {
      color: var(--accent);
      border-bottom-style: solid;
      background-color: var(--accent-soft);
    }
    .ticker-link:visited { color: var(--accent-strong); border-bottom-color: #34d39966; }

    .badge {
      display: inline-block;
      padding: 3px 11px;
      border-radius: 999px;
      font-size: 0.72rem;
      font-weight: 600;
      letter-spacing: 0.02em;
      margin: 2px;
      background: #f1f5f9;
      color: var(--ink-soft);
    }
    .badge-buy { background: var(--accent-soft); color: var(--accent-strong); }
    .badge-hold { background: #fef9c3; color: #a16207; }
    .badge-sell { background: #fee2e2; color: #b91c1c; }
    .badge-amber {
      display: inline-block; margin-left: 6px; padding: 2px 9px;
      border-radius: 999px; font-size: 0.7rem; font-weight: 600;
      background: #fef3c7; color: #b45309;
    }

    .stats-grid, .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 14px;
      margin: 20px 0;
    }
    .stat-card, .metric-card {
      background: #f8fafc;
      border: 1px solid var(--line);
      padding: 18px;
      border-radius: 12px;
      text-align: center;
    }
    .metric-card { text-align: left; }
    .stat-number, .metric-value {
      font-size: 1.9rem;
      font-weight: 700;
      color: var(--ink);
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.02em;
      margin: 0;
    }

    /* Value hero (total portfolio value) */
    .value-hero {
      background: linear-gradient(135deg, var(--accent-soft) 0%, #f0fdf9 100%);
      border: 1px solid #a7f3d0;
      border-radius: 14px;
      padding: 26px 28px;
      margin: 6px 0 8px;
    }
    .hero-meta { color: var(--accent-strong); font-size: 0.86rem; font-weight: 600; letter-spacing: 0.01em; }
    .hero-value {
      font-size: 2.8rem;
      font-weight: 800;
      color: var(--accent-strong);
      font-variant-numeric: tabular-nums;
      letter-spacing: -0.03em;
      line-height: 1.1;
      margin: 4px 0 6px;
    }
    .hero-value.muted { color: var(--muted); }
    .alloc-note { color: var(--ink-soft); font-size: 0.92rem; margin: 8px 0 0; }
    .alloc-note code {
      background: #ffffff; border: 1px solid #a7f3d0; border-radius: 5px;
      padding: 1px 6px; font-size: 0.86em; color: var(--accent-strong);
    }

    /* Allocation breakdown rows */
    .alloc-list { display: flex; flex-direction: column; gap: 6px; }
    .alloc-row {
      display: grid;
      grid-template-columns: minmax(160px, 1.4fr) 2fr auto auto;
      align-items: center;
      gap: 16px;
      padding: 8px 4px;
      border-bottom: 1px solid var(--line-soft);
    }
    .alloc-row:last-child { border-bottom: none; }
    .alloc-pct { min-width: 56px; font-weight: 600; }
    .alloc-value { min-width: 88px; color: var(--ink-soft); }

    /* Rounded weight bars */
    .weight-bar {
      position: relative;
      height: 8px;
      width: 100%;
      background: var(--line-soft);
      border-radius: 999px;
      overflow: hidden;
    }
    .weight-bar-sm { height: 6px; max-width: 120px; }
    .weight-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--accent) 0%, var(--accent-strong) 100%);
      border-radius: 999px;
      min-width: 2px;
    }

    .highlight {
      background: #f8fafc;
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 18px 20px;
      margin: 16px 0;
    }
    .success {
      background: var(--accent-soft);
      border: 1px solid #a7f3d0;
      color: var(--accent-strong);
    }
    .warning {
      background: #fffbeb;
      border: 1px solid #fde68a;
      color: #92400e;
    }
    .danger {
      background: #fef2f2;
      border: 1px solid #fecaca;
      color: #991b1b;
    }
    footer {
      margin-top: 40px;
      padding: 24px;
      text-align: center;
      color: var(--muted);
      border-top: 1px solid var(--line);
    }
    @media (max-width: 768px) {
      body { padding: 12px; }
      header { padding: 22px; }
      h1 { font-size: 1.5rem; }
      .stats-grid, .metrics-grid { grid-template-columns: 1fr; }
      .hero-value { font-size: 2.1rem; }
      .alloc-row { grid-template-columns: 1fr auto; row-gap: 6px; }
      .alloc-row .weight-bar { grid-column: 1 / -1; order: 3; }
      table { font-size: 0.84rem; }
      th, td { padding: 9px 8px; }
    }

    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0b1120;
        --card: #111827;
        --ink: #e5e7eb;
        --ink-soft: #cbd5e1;
        --muted: #94a3b8;
        --line: #1f2937;
        --line-soft: #1e293b;
        --accent: #34d399;
        --accent-strong: #6ee7b7;
        --accent-soft: #0f2a22;
        --shadow: 0 1px 2px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.5);
      }
      header { border-left-color: var(--accent); }
      th { background: #0f172a; color: var(--muted); }
      tbody tr:hover { background: #132a23; }
      .stat-card, .metric-card, .highlight { background: #0f172a; }
      .badge { background: #1f2937; color: var(--ink-soft); }
      .badge-buy { background: var(--accent-soft); color: var(--accent-strong); }
      .badge-hold { background: #3a2f0b; color: #fbbf24; }
      .badge-sell { background: #3a1414; color: #fca5a5; }
      .value-hero {
        background: linear-gradient(135deg, #0f2a22 0%, #0d1f1a 100%);
        border-color: #14532d;
      }
      .hero-value, .hero-meta { color: var(--accent-strong); }
      .alloc-note code { background: #0f172a; border-color: #14532d; color: var(--accent-strong); }
      .weight-bar { background: #1e293b; }
      .success { background: var(--accent-soft); border-color: #14532d; color: var(--accent-strong); }
      .warning { background: #3a2f0b; border-color: #5a4d10; color: #fcd34d; }
      .danger { background: #3a1414; border-color: #5a2020; color: #fca5a5; }
      footer { border-top-color: var(--line); }
      .ticker-link { color: var(--accent-strong); border-bottom-color: #34d39966; }
      .ticker-link:hover { color: var(--accent); background-color: var(--accent-soft); }
    }

    /* Traffic-light indicators (Phase 16) */
    .traffic-light { display: inline-block; width: 14px; height: 14px; border-radius: 50%; margin-right: 8px; vertical-align: middle; }
    .traffic-light-green { background-color: #22c55e; }
    .traffic-light-yellow { background-color: #eab308; }
    .traffic-light-red { background-color: #ef4444; }

    /* Fear & Greed gauge (Phase 16) */
    .fear-greed-gauge { position: relative; height: 30px; border-radius: 15px; background: linear-gradient(to right, #dc2626, #ef4444, #eab308, #22c55e, #16a34a); margin: 10px 0; }
    .fear-greed-marker { position: absolute; top: -5px; width: 4px; height: 40px; background: #1e293b; border-radius: 2px; transform: translateX(-50%); }
    .fear-greed-label { text-align: center; font-weight: 600; font-size: 1.1em; margin-top: 5px; }
    .fear-greed-value { text-align: center; font-size: 2em; font-weight: 700; margin-bottom: 5px; }

    /* Macro dashboard grid (Phase 16) */
    .macro-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px; }
    .macro-card { background: #f8fafc; border: 1px solid var(--line); border-radius: 12px; padding: 16px; text-align: center; }
    .macro-card h4 { margin: 0 0 8px 0; color: var(--muted); font-size: 0.9em; }
    .macro-value { font-size: 1.5em; font-weight: 700; margin: 5px 0; color: var(--ink); font-variant-numeric: tabular-nums; }

    /* Economic calendar table (Phase 16) */
    .calendar-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    .calendar-table th { background: #f8fafc; padding: 11px 14px; text-align: left; border-bottom: 1px solid var(--line); color: var(--muted); text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.06em; }
    .calendar-table td { padding: 10px 14px; border-bottom: 1px solid var(--line-soft); }
    .calendar-table tr:hover { background: var(--accent-soft); }

    @media (max-width: 768px) {
      .macro-grid { grid-template-columns: 1fr; }
    }

    @media (prefers-color-scheme: dark) {
      .macro-card { background: #0f172a; border-color: var(--line); }
      .macro-card h4 { color: var(--muted); }
      .calendar-table th { background: #0f172a; color: var(--muted); border-bottom-color: var(--line); }
      .calendar-table td { border-bottom-color: var(--line-soft); }
      .calendar-table tr:hover { background: #132a23; }
      .fear-greed-marker { background: var(--ink); }
    }
        """
