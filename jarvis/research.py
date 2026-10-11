"""Small, dependency-free web research helper using DuckDuckGo HTML results."""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen


class _ResultParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self._current = None
        self._capture = None
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "")
        if tag == "a" and "result__a" in classes.split():
            href = attrs.get("href", "")
            if href.startswith("//"):
                href = "https:" + href
            parsed_href = urlparse(href)
            if parsed_href.netloc.endswith("duckduckgo.com") and parsed_href.path.startswith("/l/"):
                target = parse_qs(parsed_href.query).get("uddg", [""])[0]
                href = unquote(target)
            if href.startswith("http://") or href.startswith("https://"):
                self._current = {"title": "", "url": href, "snippet": ""}
                self.results.append(self._current)
                self._capture = "title"
                self._buffer = []
        elif self._current and "result__snippet" in classes.split():
            self._capture = "snippet"
            self._buffer = []

    def handle_data(self, data):
        if self._capture:
            self._buffer.append(data)

    def handle_endtag(self, tag):
        if self._capture and tag in {"a", "div"}:
            value = " ".join(" ".join(self._buffer).split())
            if self._current and value:
                self._current[self._capture] = value[:600]
            self._capture = None
            self._buffer = []


def research_web(query, limit=5, timeout=10):
    """Return titles, snippets and source URLs. Never executes fetched content."""
    query = str(query).strip()[:300]
    if not query:
        return []
    limit = max(1, min(int(limit), 8))
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    request = Request(url, headers={"User-Agent": "JARVIS-Assistant/0.4 (user-initiated research)"})
    try:
        with urlopen(request, timeout=timeout) as response:
            html = response.read(1_000_000).decode("utf-8", errors="replace")
    except Exception as exc:
        raise RuntimeError(f"Web research request failed: {exc}") from exc
    parser = _ResultParser()
    parser.feed(html)
    results = []
    seen = set()
    for item in parser.results:
        parsed = urlparse(item["url"])
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or item["url"] in seen:
            continue
        seen.add(item["url"])
        results.append(item)
        if len(results) >= limit:
            break
    return results
