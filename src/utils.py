import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "search"


def today_iso() -> str:
    return date.today().isoformat()


def default_output_path(keyword: str, location: str) -> str:
    filename = f"{slugify(keyword)}_{slugify(location)}_{today_iso()}.csv"
    return str(Path("output") / filename)


def normalize_url(url: str) -> str:
    if not url:
        return ""

    normalized = url.strip()
    if not normalized:
        return ""

    if not re.match(r"^https?://", normalized, flags=re.IGNORECASE):
        normalized = f"https://{normalized}"

    return normalized.rstrip("/")


def get_domain(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(normalize_url(url))
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def dedupe_businesses(places: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique_places: list[dict] = []

    for place in places:
        place_id = (place.get("place_id") or "").strip().lower()
        website_domain = get_domain(place.get("website", ""))
        name_address = "|".join(
            [
                (place.get("business_name") or "").strip().lower(),
                (place.get("address") or "").strip().lower(),
            ]
        )

        if place_id:
            key = f"id:{place_id}"
        elif website_domain:
            key = f"domain:{website_domain}"
        else:
            key = f"name_address:{name_address}"

        if key in seen:
            continue

        seen.add(key)
        unique_places.append(place)

    return unique_places
