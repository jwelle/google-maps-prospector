from __future__ import annotations

import time
from typing import Any


class PlacesClientError(RuntimeError):
    pass


FIELD_MASK = (
    "places.id,"
    "places.displayName,"
    "places.formattedAddress,"
    "places.nationalPhoneNumber,"
    "places.websiteUri,"
    "places.rating,"
    "places.userRatingCount,"
    "places.googleMapsUri,"
    "places.businessStatus"
)


class PlacesClient:
    endpoint = "https://places.googleapis.com/v1/places:searchText"

    def __init__(self, api_key: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def search_text(self, keyword: str, location: str, max_results: int) -> list[dict]:
        if not self.api_key:
            raise PlacesClientError(
                "Missing GOOGLE_MAPS_API_KEY. Create a .env file from .env.example before live searches."
            )

        try:
            import requests
        except ImportError as exc:
            raise PlacesClientError(
                "Missing dependency: requests. Run `pip install -r requirements.txt`."
            ) from exc

        text_query = f"{keyword} in {location}"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        }

        places: list[dict] = []
        page_token = ""

        while len(places) < max_results:
            body: dict[str, Any] = {
                "textQuery": text_query,
                "pageSize": min(20, max_results - len(places)),
            }
            if page_token:
                body["pageToken"] = page_token

            try:
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=body,
                    timeout=self.timeout_seconds,
                )
            except requests.RequestException as exc:
                raise PlacesClientError(f"Google Places request failed: {exc}") from exc

            if response.status_code in {401, 403}:
                raise PlacesClientError(_format_google_error(response))
            if response.status_code == 429:
                raise PlacesClientError("Google Places quota or rate limit was reached.")
            if response.status_code >= 400:
                raise PlacesClientError(
                    _format_google_error(response)
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise PlacesClientError("Google Places returned malformed JSON.") from exc

            raw_places = payload.get("places", [])
            if not isinstance(raw_places, list):
                raise PlacesClientError("Google Places response did not include a valid places list.")

            for raw_place in raw_places:
                places.append(_normalize_place(raw_place))
                if len(places) >= max_results:
                    break

            page_token = payload.get("nextPageToken") or ""
            if not page_token:
                break

            time.sleep(0.25)

        return places


def _normalize_place(place: dict[str, Any]) -> dict:
    display_name = place.get("displayName") or {}
    if isinstance(display_name, dict):
        business_name = display_name.get("text", "")
    else:
        business_name = str(display_name)

    return {
        "place_id": place.get("id", ""),
        "business_name": business_name,
        "address": place.get("formattedAddress", ""),
        "phone": place.get("nationalPhoneNumber", ""),
        "website": place.get("websiteUri", ""),
        "rating": place.get("rating", ""),
        "review_count": place.get("userRatingCount", ""),
        "google_maps_url": place.get("googleMapsUri", ""),
        "business_status": place.get("businessStatus", ""),
    }


def _format_google_error(response: Any) -> str:
    fallback = f"Google Places returned HTTP {response.status_code}: {response.text[:500]}"
    try:
        payload = response.json()
    except ValueError:
        return fallback

    error = payload.get("error")
    if not isinstance(error, dict):
        return fallback

    message = error.get("message") or fallback
    status = error.get("status") or ""
    reasons: list[str] = []
    for detail in error.get("details", []):
        if not isinstance(detail, dict):
            continue
        reason = detail.get("reason")
        metadata = detail.get("metadata", {})
        service = metadata.get("service") if isinstance(metadata, dict) else ""
        service_title = metadata.get("serviceTitle") if isinstance(metadata, dict) else ""
        if reason:
            reason_text = reason
            if service_title or service:
                reason_text += f" ({service_title or service})"
            reasons.append(reason_text)

    detail_text = f" Reason: {', '.join(reasons)}." if reasons else ""
    status_text = f" Status: {status}." if status else ""
    return f"Google Places rejected the request.{status_text}{detail_text} {message}"
