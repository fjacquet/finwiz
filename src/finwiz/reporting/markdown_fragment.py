"""Convert model-authored markdown into safe HTML.

Escape first, then allow a fixed subset. The model is never a source of markup:
Perplexity quotes live web pages into its output, so anything that looks like a
tag is escaped and rendered as visible text, never executed.

Deliberately does NOT ask the model for HTML output — that would be an
injection vector (the model quotes arbitrary web pages verbatim), couples
content to presentation, and is unreliable across providers. This module is
the render boundary instead: markdown-ish text in, a fixed allowlist of HTML
out (``<strong>``, ``<em>``, ``<p>``, one level of ``<ul>``/``<li>`` nesting,
and citation ``<sup><a>`` footnotes).

Known limitation — citations are not wired through today: ``citations`` and
the citation-linking behavior below are fully implemented and covered, but as
of this writing no caller actually supplies a populated list. The direct
Perplexity call this module's output ultimately renders
(``finwiz.analysis.strategic_research`` via
``crewai_custom_tools.perplexity_structured``) asks the Perplexity API for
``return_citations``, but the async wrapper function used there only ever
returns a validated Pydantic schema instance — it reads the response's
``citations`` field and discards it. A different code path in the same
dependency (the CrewAI ``BaseTool`` wrapper) does return citations alongside
structured content, but ``strategic_research.py`` does not call that path.
Threading citations through would mean either patching the external
``crewai-custom-tools`` package (a separate repository, requiring a new
release) or duplicating its HTTP/retry logic in this repo — both are
redesigns of the Perplexity integration and out of scope here. Until that is
done, every ``[n]`` marker in rendered text falls through the same
dangling-marker path and is stripped rather than linked. A marker pointing at
no source is strictly worse than no marker, so markers are always removed
when no matching citation is available — never left as bare, meaningless
digits in the report.
"""

from __future__ import annotations

import re
from html import escape
from urllib.parse import urlparse

_BOLD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", re.DOTALL)
_CITATION = re.compile(r"\[(\d{1,3})\]")


def _is_safe_url(url: str) -> bool:
    """Only http/https citation URLs may become a link.

    A citation URL is model-supplied data (Perplexity's own search results),
    not something this codebase controls. A ``javascript:`` or ``data:`` URL
    must never become an executable href, so anything outside http/https is
    treated the same as a missing citation: the marker is dropped, not linked.
    """
    try:
        return urlparse(url).scheme in ("http", "https")
    except (ValueError, TypeError):
        return False


def _render_inline(segment: str, citations: list[str] | None) -> str:
    """Apply bold/italic, then citation linking, to one already-escaped line.

    Order matters: citation linking inserts real HTML (an ``<a>`` tag) built
    from model-supplied data. Running it *before* the bold/italic regexes
    would let a citation URL that happens to contain ``**`` be reinterpreted
    as a bold delimiter, corrupting the anchor markup. Running it last means
    bold/italic only ever see the escaped markdown text, never HTML this
    function itself inserted.
    """
    out = _BOLD.sub(r"<strong>\1</strong>", segment)
    out = _ITALIC.sub(r"<em>\1</em>", out)

    def _cite(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        sources = citations or []
        if 1 <= idx <= len(sources) and _is_safe_url(sources[idx - 1]):
            href = escape(sources[idx - 1], quote=True)
            return f'<sup><a href="{href}" rel="noopener noreferrer" target="_blank">{idx}</a></sup>'
        return ""  # Dangling or unsafe marker: remove rather than show a reference to nothing.

    return _CITATION.sub(_cite, out)


def render_markdown_fragment(text: str, *, citations: list[str] | None = None) -> str:
    """Render a markdown fragment to HTML using a strict allowlist.

    Supports: ``**bold**``, ``*italic*``, one level of ``- bullet`` nesting
    (an indented ``  - sub-bullet`` becomes a nested ``<ul>`` inside its
    parent ``<li>``; deeper indentation flattens into that same nested
    level rather than dropping content or double-nesting), plain paragraphs,
    and ``[n]`` citation markers resolved against ``citations`` (1-indexed).

    Escapes with ``quote=False``: this text is rendered as HTML text content,
    never inside an attribute, so escaping ``"``/``'`` would only add noise —
    French prose is full of apostrophes. Citation URLs, which *do* land inside
    an ``href="..."`` attribute, are escaped separately with ``quote=True``.
    """
    if not text:
        return ""

    escaped = escape(text, quote=False)

    blocks: list[str] = []
    top_items: list[dict[str, object]] = []  # [{"content": str, "nested": list[str]}]

    def flush_list() -> None:
        nonlocal top_items
        if not top_items:
            return
        rendered_items = []
        for item in top_items:
            li = f"<li>{item['content']}"
            nested = item["nested"]
            if nested:
                li += "<ul>" + "".join(f"<li>{n}</li>" for n in nested) + "</ul>"
            li += "</li>"
            rendered_items.append(li)
        blocks.append("<ul>" + "".join(rendered_items) + "</ul>")
        top_items = []

    for raw_line in escaped.split("\n"):
        if not raw_line.strip():
            continue
        is_indented = raw_line[: len(raw_line) - len(raw_line.lstrip())] != ""
        stripped = raw_line.strip()

        if stripped.startswith("- "):
            content = _render_inline(stripped[2:].strip(), citations)
            if is_indented and top_items:
                top_items[-1]["nested"].append(content)  # type: ignore[union-attr]
            else:
                top_items.append({"content": content, "nested": []})
            continue

        flush_list()
        blocks.append(f"<p>{_render_inline(stripped, citations)}</p>")

    flush_list()
    return "".join(blocks)
