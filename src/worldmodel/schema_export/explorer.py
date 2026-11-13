"""The standalone HTML schema explorer (LABS-1.024, E-6): one file, the export embedded as JSON, no external
libraries, fonts or network access (a Content-Security-Policy forbids any request)."""

import json
from pathlib import Path

TEMPLATE = Path(__file__).with_name("explorer.html")
PLACEHOLDER = "/*__EXPORT_JSON__*/"


def embedded_json(doc):
    """The export as compact JSON that is safe inside a <script> element: every '<' is escaped, so no text in the
    data can close the element or open a comment."""
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def render_explorer(doc):
    template = TEMPLATE.read_text()
    if template.count(PLACEHOLDER) != 1:
        raise ValueError("the explorer template must contain the data placeholder exactly once")
    return template.replace(PLACEHOLDER, embedded_json(doc))


def extract_json(html):
    """The export embedded in a rendered explorer page (for checks that the page shows exactly the export)."""
    start = html.index('<script type="application/json" id="export-data">') + len('<script type="application/json" id="export-data">')
    end = html.index("</script>", start)
    return json.loads(html[start:end])
