import csv
from io import StringIO
from pathlib import Path


CSV_COLUMNS = [
    "business_name",
    "address",
    "phone",
    "website",
    "rating",
    "review_count",
    "google_maps_url",
    "business_status",
    "emails",
    "first_email",
    "email_source_page",
    "email_found",
    "contact_page_found",
    "phone_found_on_site",
    "form_detected",
    "chatbot_detected",
    "online_booking_detected",
    "lead_form_detected",
    "calendar_link_detected",
    "wordpress_detected",
    "google_analytics_detected",
    "facebook_pixel_detected",
    "highlevel_detected",
    "hubspot_detected",
    "ssl_enabled",
    "title_tag_present",
    "meta_description_present",
    "possible_outdated_site",
    "opportunity_score",
    "opportunity_reason",
    "suggested_pitch_angle",
]


def write_csv(rows: list[dict], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as csv_file:
        csv_file.write(rows_to_csv_text(rows))


def rows_to_csv_text(rows: list[dict]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(_format_row(row))
    return buffer.getvalue()


def format_rows_for_csv(rows: list[dict]) -> list[dict]:
    return [_format_row(row) for row in rows]


def _format_row(row: dict) -> dict:
    formatted = {column: row.get(column, "") for column in CSV_COLUMNS}

    emails = formatted.get("emails")
    if isinstance(emails, list):
        formatted["emails"] = "; ".join(emails)

    for column in CSV_COLUMNS:
        if isinstance(formatted[column], bool):
            formatted[column] = "true" if formatted[column] else "false"

    return formatted
