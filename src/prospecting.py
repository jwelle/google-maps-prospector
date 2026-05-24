from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from config import Config
from csv_exporter import rows_to_csv_text, write_csv
from email_extractor import collect_emails
from opportunity_analyzer import analyze_website
from places_client import PlacesClient
from utils import dedupe_businesses, default_output_path, normalize_url
from website_crawler import crawl_website


ProgressCallback = Callable[[dict], None]


@dataclass
class ProspectingResult:
    rows: list[dict]
    output_path: str
    csv_text: str


def run_prospecting_workflow(
    keyword: str,
    location: str,
    max_results: int,
    output_path: str | None,
    skip_places: bool,
    config: Config,
    progress_callback: ProgressCallback | None = None,
    write_output: bool = True,
) -> ProspectingResult:
    keyword = keyword.strip()
    location = location.strip()

    if not keyword or not location:
        raise ValueError("Keyword and location must not be empty.")
    if max_results < 1:
        raise ValueError("Max results must be at least 1.")

    resolved_output_path = output_path or default_output_path(keyword, location)
    places = load_places(keyword, location, max_results, skip_places, config)
    places = dedupe_businesses(places)[:max_results]

    _emit(
        progress_callback,
        {
            "event": "places_loaded",
            "message": f"Found {len(places)} places",
            "total": len(places),
        },
    )

    rows: list[dict] = []
    for index, place in enumerate(places, start=1):
        business_name = place.get("business_name") or "Unknown business"
        website = normalize_url(place.get("website", ""))

        _emit(
            progress_callback,
            {
                "event": "business_started",
                "index": index,
                "total": len(places),
                "business_name": business_name,
                "website": website,
                "message": f"[{index}/{len(places)}] Checking {business_name}",
            },
        )

        crawl_result = crawl_website(
            website,
            timeout_seconds=config.request_timeout_seconds,
            crawl_delay_seconds=config.crawl_delay_seconds,
            max_pages_per_site=config.max_pages_per_site,
        )
        email_result = collect_emails(crawl_result.pages)
        analysis = analyze_website(website, crawl_result.pages, email_result["emails"])

        row = {
            **place,
            "website": website,
            **email_result,
            **analysis,
        }
        rows.append(row)

        _emit(
            progress_callback,
            {
                "event": "business_finished",
                "index": index,
                "total": len(places),
                "business_name": business_name,
                "website": website,
                "emails_found": len(email_result["emails"]),
                "score": analysis["opportunity_score"],
                "crawl_errors": crawl_result.errors,
                "row": row,
                "message": f"Finished {business_name}",
            },
        )

    csv_text = rows_to_csv_text(rows)
    if write_output:
        write_csv(rows, resolved_output_path)

    _emit(
        progress_callback,
        {
            "event": "saved",
            "message": f"Saved CSV to {resolved_output_path}",
            "output_path": resolved_output_path,
            "rows": len(rows),
        },
    )

    return ProspectingResult(rows=rows, output_path=resolved_output_path, csv_text=csv_text)


def load_places(keyword: str, location: str, max_results: int, skip_places: bool, config: Config) -> list[dict]:
    if skip_places:
        return sample_places()[:max_results]

    client = PlacesClient(config.google_maps_api_key, config.request_timeout_seconds)
    return client.search_text(keyword, location, max_results)


def sample_places() -> list[dict]:
    return [
        {
            "place_id": "sample-example-design",
            "business_name": "Example Design Studio",
            "address": "123 Example St, Austin, TX",
            "phone": "(512) 555-0100",
            "website": "https://example.com",
            "rating": 4.6,
            "review_count": 42,
            "google_maps_url": "",
            "business_status": "OPERATIONAL",
        },
        {
            "place_id": "sample-no-website",
            "business_name": "Sample No Website LLC",
            "address": "456 Placeholder Ave, Austin, TX",
            "phone": "(512) 555-0199",
            "website": "",
            "rating": "",
            "review_count": "",
            "google_maps_url": "",
            "business_status": "OPERATIONAL",
        },
    ]


def _emit(progress_callback: ProgressCallback | None, event: dict) -> None:
    if progress_callback is not None:
        progress_callback(event)
