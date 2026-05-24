import re


EMAIL_PATTERN = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
INVALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js")


def extract_emails_from_html(html: str) -> list[str]:
    if not html:
        return []

    emails: list[str] = []
    seen: set[str] = set()

    for match in EMAIL_PATTERN.findall(html):
        email = clean_email(match)
        if not email or email in seen:
            continue
        if email.endswith(INVALID_EXTENSIONS):
            continue
        seen.add(email)
        emails.append(email)

    return emails


def clean_email(email: str) -> str:
    return email.strip().strip(".,;:!?)]}'\"").lower()


def collect_emails(pages: list[dict]) -> dict:
    all_emails: list[str] = []
    seen: set[str] = set()
    first_email = ""
    first_source_page = ""

    for page in pages:
        page_emails = extract_emails_from_html(page.get("html", ""))
        for email in page_emails:
            if email in seen:
                continue

            seen.add(email)
            all_emails.append(email)

            if not first_email:
                first_email = email
                first_source_page = page.get("url", "")

    return {
        "emails": all_emails,
        "first_email": first_email,
        "email_source_page": first_source_page,
    }
