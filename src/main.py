from __future__ import annotations

import argparse
import sys

from config import load_config
from places_client import PlacesClientError
from prospecting import load_places, run_prospecting_workflow, sample_places


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find local business prospects, analyze their websites, and export opportunity data to CSV."
    )
    parser.add_argument("--keyword", required=True, help="Business keyword or category, such as 'web designers'.")
    parser.add_argument("--location", required=True, help="Search location, such as 'Austin TX' or 'Texas'.")
    parser.add_argument("--max-results", type=int, default=None, help="Maximum number of businesses to process.")
    parser.add_argument("--output", default=None, help="Optional CSV output path.")
    parser.add_argument(
        "--skip-places",
        action="store_true",
        help="Use sample place records instead of calling Google Places. Useful for local test runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.keyword = args.keyword.strip()
    args.location = args.location.strip()

    if not args.keyword or not args.location:
        print("--keyword and --location must not be empty.", file=sys.stderr)
        return 2

    config = load_config()
    max_results = args.max_results or config.default_max_results

    if max_results < 1:
        print("--max-results must be at least 1.", file=sys.stderr)
        return 2

    try:
        if args.skip_places:
            print(f"Using sample places for: {args.keyword} in {args.location}")
        else:
            print(f"Searching Google Places for: {args.keyword} in {args.location}")

        result = run_prospecting_workflow(
            keyword=args.keyword,
            location=args.location,
            max_results=max_results,
            output_path=args.output,
            skip_places=args.skip_places,
            config=config,
            progress_callback=print_progress,
        )
    except PlacesClientError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Saved CSV to {result.output_path}")
    return 0


def print_progress(event: dict) -> None:
    if event["event"] == "places_loaded":
        print(event["message"])
    elif event["event"] == "business_started":
        print(event["message"])
        print(f"  Website: {event['website'] or 'none'}")
    elif event["event"] == "business_finished":
        print(f"  Emails found: {event['emails_found']}")
        print(f"  Score: {event['score']}")
        if event["crawl_errors"]:
            print(f"  Crawl notes: {len(event['crawl_errors'])} issue(s)")


if __name__ == "__main__":
    raise SystemExit(main())
