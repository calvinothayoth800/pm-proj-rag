from html.parser import HTMLParser
import re
from typing import List, Optional


class ParseError(ValueError):
    """Raised when fetched content cannot produce reliable text."""


BLOCKED_PATTERNS = (
    "captcha",
    "access denied",
    "are you a human",
    "please enable javascript",
    "enable javascript to continue",
)
DROP_TAGS = {"script", "style", "noscript", "svg"}
NOISE_PATTERNS = (
    re.compile(r"^\s*(home|login|signup|sign up|about us|privacy policy|terms|download app)\s*$", re.I),
    re.compile(r"^\s*(advertisement|sponsored)\s*$", re.I),
)


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        HTMLParser.__init__(self)
        self._drop_depth = 0
        self.parts = []  # type: List[str]

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in DROP_TAGS:
            self._drop_depth += 1
        if tag.lower() in {"p", "div", "section", "article", "h1", "h2", "h3", "li", "tr", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in DROP_TAGS and self._drop_depth:
            self._drop_depth -= 1
        if tag.lower() in {"p", "div", "section", "article", "h1", "h2", "h3", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._drop_depth:
            self.parts.append(data)


def normalize_lines(text: str) -> List[str]:
    lines = []
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        if any(pattern.match(line) for pattern in NOISE_PATTERNS):
            continue
        lines.append(line)
    return lines


def parse_html(html: str, min_chars: int = 120) -> str:
    lowered = html.lower()
    if any(pattern in lowered for pattern in BLOCKED_PATTERNS):
        raise ParseError("source appears blocked or requires browser interaction")

    parser = TextExtractor()
    parser.feed(html)
    lines = normalize_lines("\n".join(parser.parts))
    text = "\n".join(lines)

    if len(text) < min_chars:
        raise ParseError("extracted text is too short; page may be client-rendered or malformed")

    return text


def _canonical_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def focus_scheme_text(text: str, scheme_name: str, min_chars: int = 120) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    scheme_label = _canonical_label(scheme_name.replace(" - ", " "))
    start_index = None  # type: Optional[int]
    end_index = None  # type: Optional[int]

    for index, line in enumerate(lines):
        if _canonical_label(line) == scheme_label:
            start_index = index
            break

    if start_index is None:
        for index, line in enumerate(lines):
            if scheme_label in _canonical_label(line):
                start_index = index
                break

    if start_index is None:
        raise ParseError("could not locate configured scheme section in extracted text")

    footer_markers = {
        "Vaishnavi Tech Park",
        "GROWW",
        "PRODUCTS",
        "Share Market",
    }
    for index in range(start_index + 1, len(lines)):
        if lines[index] in footer_markers:
            end_index = index
            break

    focused = "\n".join(lines[start_index:end_index]).strip()
    if len(focused) < min_chars:
        raise ParseError("focused scheme text is too short after noise filtering")
    return focused
