from __future__ import annotations

import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

from utils import normalize_url


CRAWL_PATHS = ["", "/contact", "/about", "/team", "/locations"]
USER_AGENT = (
    "LocalProspectFinder/0.1 "
    "(conservative website opportunity analyzer; contact: configure-in-readme)"
)


@dataclass
class CrawlResult:
    website: str
    pages: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def crawl_website(
    website_url: str,
    timeout_seconds: float,
    crawl_delay_seconds: float,
    max_pages_per_site: int,
) -> CrawlResult:
    normalized_url = normalize_url(website_url)
    result = CrawlResult(website=normalized_url)

    if not normalized_url:
        return result

    try:
        import requests
    except ImportError:
        result.errors.append("Missing dependency: requests. Run `pip install -r requirements.txt`.")
        return result

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})

    urls = _candidate_urls(normalized_url, max_pages_per_site)
    for index, url in enumerate(urls):
        if index > 0 and crawl_delay_seconds > 0:
            time.sleep(crawl_delay_seconds)

        try:
            response = session.get(url, timeout=timeout_seconds, allow_redirects=True)
        except requests.exceptions.SSLError as exc:
            result.errors.append(f"SSL error for {url}: {exc}")
            continue
        except requests.RequestException as exc:
            result.errors.append(f"Request failed for {url}: {exc}")
            continue

        content_type = response.headers.get("content-type", "").lower()
        if response.status_code >= 400:
            result.errors.append(f"HTTP {response.status_code} for {url}")
            continue
        if content_type and "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            result.errors.append(f"Skipped non-HTML response for {url}")
            continue

        result.pages.append(
            {
                "url": response.url,
                "requested_url": url,
                "status_code": response.status_code,
                "html": response.text,
            }
        )

    return result


def _candidate_urls(base_url: str, max_pages_per_site: int) -> list[str]:
    base = normalize_url(base_url)
    urls: list[str] = []

    for path in CRAWL_PATHS[: max(0, max_pages_per_site)]:
        if path:
            urls.append(urljoin(f"{base}/", path.lstrip("/")))
        else:
            urls.append(base)

    return urls
