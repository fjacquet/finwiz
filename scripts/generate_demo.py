#!/usr/bin/env python3
"""
Generate demo HTML file to showcase template features.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jinja2 import Environment, FileSystemLoader


def generate_demo():
    """Generate demo HTML file."""
    templates_dir = Path(__file__).parent.parent / "src" / "finwiz" / "templates"

    env = Environment(  # nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2
        loader=FileSystemLoader(str(templates_dir)), autoescape=True, trim_blocks=True, lstrip_blocks=True
    )

    template = env.get_template("demo.html")

    context = {"title": "FinWiz Template Demo", "timestamp": datetime.now(), "language": "en"}

    html_content = template.render(**context)  # nosemgrep: python.flask.security.xss.audit.direct-use-of-jinja2.direct-use-of-jinja2

    output_path = Path("demo.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Demo generated: {output_path}")
    print(f"🌐 Open in browser: file://{output_path.absolute()}")


if __name__ == "__main__":
    generate_demo()
