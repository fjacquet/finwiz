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
    }
        """
