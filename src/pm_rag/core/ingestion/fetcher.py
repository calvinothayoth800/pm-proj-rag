from typing import Callable, Dict, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from pm_rag.core.sources.catalog import CatalogPath, assert_allowed_url


class FetchError(RuntimeError):
    """Raised when an approved source cannot be fetched cleanly."""


class FetchResult:
    def __init__(self, url: str, status_code: int, body: str, headers: Dict[str, str]) -> None:
        self.url = url
        self.status_code = status_code
        self.body = body
        self.headers = headers


FetchTransport = Callable[[str], FetchResult]


def urllib_transport(url: str) -> FetchResult:
    request = Request(url, headers={"User-Agent": "pm-proj-rag-ingestion/1.0"})
    with urlopen(request, timeout=30) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return FetchResult(
            url=url,
            status_code=response.getcode(),
            body=raw.decode(charset, errors="replace"),
            headers=dict(response.headers.items()),
        )


def fetch_source(url: str, catalog_path: CatalogPath, transport: Optional[FetchTransport] = None) -> FetchResult:
    assert_allowed_url(url, catalog_path)
    active_transport = transport or urllib_transport
    try:
        result = active_transport(url)
    except (OSError, URLError) as exc:
        raise FetchError("fetch failed for {0}: {1}".format(url, exc))

    if result.status_code < 200 or result.status_code >= 300:
        raise FetchError("fetch failed for {0}: HTTP {1}".format(url, result.status_code))

    if not result.body.strip():
        raise FetchError("fetch failed for {0}: empty response body".format(url))

    return result
