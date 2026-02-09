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
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      line-height: 1.6;
      color: #333;
      margin: 0;
      padding: 20px;
      background: #f8f9fa;
    }
    header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      border-radius: 12px;
      margin-bottom: 30px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    h1 { margin: 0 0 10px 0; font-size: 2.2em; }
    h2 { color: #2c3e50; margin: 30px 0 15px 0; border-bottom: 2px solid #3498db; padding-bottom: 8px; }
    h3 { color: #34495e; margin: 20px 0 10px 0; }
    .section {
      background: white;
      border-radius: 8px;
      padding: 25px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .muted { color: #7f8c8d; font-size: 0.9em; }
    .small { font-size: 0.85em; }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 15px 0;
      background: white;
    }
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #ecf0f1;
    }
    th {
      background: #3498db;
      color: white;
      font-weight: 600;
    }
    .grade-a-plus { color: #27ae60; font-weight: bold; }
    .grade-a { color: #2ecc71; font-weight: bold; }
    .grade-b { color: #f39c12; font-weight: bold; }
    .grade-c { color: #e67e22; font-weight: bold; }
    .grade-d { color: #e74c3c; font-weight: bold; }
    .grade-f { color: #c0392b; font-weight: bold; }
    .ticker-link {
      color: #3498db;
      text-decoration: none;
      border-bottom: 1px dashed #3498db;
      transition: all 0.2s ease;
    }
    .ticker-link:hover {
      color: #2980b9;
      border-bottom-style: solid;
      background-color: rgba(52, 152, 219, 0.1);
    }
    .ticker-link:visited {
      color: #8e44ad;
      border-bottom-color: #8e44ad;
    }
    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.8em;
      font-weight: bold;
      margin: 2px;
    }
    .badge-buy { background: #d5f4e6; color: #27ae60; }
    .badge-hold { background: #fef9e7; color: #f39c12; }
    .badge-sell { background: #fadbd8; color: #e74c3c; }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin: 20px 0;
    }
    .stat-card {
      background: #ecf0f1;
      padding: 15px;
      border-radius: 8px;
      text-align: center;
    }
    .stat-number {
      font-size: 2em;
      font-weight: bold;
      color: #2c3e50;
    }
    .highlight {
      background: #fff3cd;
      border: 1px solid #ffeaa7;
      border-radius: 6px;
      padding: 15px;
      margin: 15px 0;
    }
    .success {
      background: #d4edda;
      border: 1px solid #c3e6cb;
      color: #155724;
    }
    .warning {
      background: #fff3cd;
      border: 1px solid #ffeaa7;
      color: #856404;
    }
    .danger {
      background: #f8d7da;
      border: 1px solid #f5c6cb;
      color: #721c24;
    }
    footer {
      margin-top: 40px;
      padding: 20px;
      text-align: center;
      color: #7f8c8d;
      border-top: 1px solid #ecf0f1;
    }
    @media (max-width: 768px) {
      body { padding: 10px; }
      header { padding: 20px; }
      h1 { font-size: 1.8em; }
      .stats-grid { grid-template-columns: 1fr; }
    }

    /* Dark Mode Support */
    @media (prefers-color-scheme: dark) {
      body {
        background: #1a1a1a;
        color: #e0e0e0;
      }
      h2 {
        color: #a8c0db;
        border-bottom-color: #5a7fa0;
      }
      h3 {
        color: #b8c9da;
      }
      .section {
        background: #2d2d2d;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      }
      table {
        background: #2d2d2d;
      }
      th {
        background: #3a5a7a;
      }
      th, td {
        border-bottom-color: #404040;
      }
      .stat-card {
        background: #383838;
      }
      .stat-number {
        color: #a8c0db;
      }
      .muted {
        color: #999;
      }
      .highlight {
        background: #3d3520;
        border-color: #5a4d28;
      }
      .success {
        background: #1e3a28;
        border-color: #2d5a3d;
        color: #8bc98d;
      }
      .warning {
        background: #3d3520;
        border-color: #5a4d28;
        color: #f1c40f;
      }
      .danger {
        background: #3a1f1f;
        border-color: #5a3030;
        color: #e79b9b;
      }
      footer {
        color: #999;
        border-top-color: #404040;
      }
      .ticker-link {
        color: #5dade2;
        border-bottom-color: #5dade2;
      }
      .ticker-link:hover {
        color: #85c1e9;
        background-color: rgba(93, 173, 226, 0.15);
      }
      .ticker-link:visited {
        color: #bb8fce;
        border-bottom-color: #bb8fce;
      }
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
    .macro-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
    .macro-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; text-align: center; }
    .macro-card h4 { margin: 0 0 8px 0; color: #475569; font-size: 0.9em; }
    .macro-value { font-size: 1.5em; font-weight: 700; margin: 5px 0; }

    /* Economic calendar table (Phase 16) */
    .calendar-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
    .calendar-table th { background: #f1f5f9; padding: 10px; text-align: left; border-bottom: 2px solid #cbd5e1; color: #334155; }
    .calendar-table td { padding: 8px 10px; border-bottom: 1px solid #e2e8f0; }
    .calendar-table tr:hover { background: #f8fafc; }

    @media (max-width: 768px) {
      .macro-grid { grid-template-columns: 1fr; }
    }

    @media (prefers-color-scheme: dark) {
      .macro-card { background: #383838; border-color: #404040; }
      .macro-card h4 { color: #b8c9da; }
      .calendar-table th { background: #3a5a7a; color: #e0e0e0; border-bottom-color: #5a7fa0; }
      .calendar-table td { border-bottom-color: #404040; }
      .calendar-table tr:hover { background: #333; }
      .fear-greed-marker { background: #e0e0e0; }
    }
        """
