from __future__ import annotations

import re


def analyze_website(website_url: str, pages: list[dict], emails: list[str]) -> dict:
    combined_html = "\n".join(page.get("html", "") for page in pages)
    combined_lower = combined_html.lower()
    page_urls = [page.get("url", "") for page in pages] + [page.get("requested_url", "") for page in pages]

    email_found = bool(emails)
    contact_page_found = any("/contact" in url.lower() for url in page_urls)
    phone_found_on_site = bool(re.search(r"(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}", combined_html))
    form_detected = "<form" in combined_lower
    chatbot_detected = _contains_any(
        combined_lower,
        ["intercom", "drift", "tawk", "crisp", "livechat", "chat widget", "chatbot"],
    )
    online_booking_detected = _contains_any(
        combined_lower,
        ["calendly", "book now", "schedule now", "appointment", "online booking", "acuityscheduling"],
    )
    lead_form_detected = form_detected and _contains_any(
        combined_lower,
        ["contact", "quote", "estimate", "lead", "submit", "request", "consultation"],
    )
    calendar_link_detected = _contains_any(
        combined_lower,
        ["calendly.com", "calendar.google.com", "appointments", "schedule a call"],
    )
    wordpress_detected = _contains_any(combined_lower, ["wp-content", "wp-json", "wordpress"])
    google_analytics_detected = _contains_any(
        combined_lower,
        ["gtag", "google-analytics", "googletagmanager", "google analytics"],
    ) or bool(re.search(r"\bG-[A-Z0-9]{6,}\b", combined_html))
    facebook_pixel_detected = _contains_any(combined_lower, ["fbq(", "facebook.com/tr"])
    highlevel_detected = _contains_any(
        combined_lower,
        ["leadconnector", "msgsndr", "gohighlevel", "highlevel"],
    )
    hubspot_detected = _contains_any(combined_lower, ["hs-scripts", "hubspot", "hsforms"])
    ssl_enabled = website_url.lower().startswith("https://")
    title_tag_present = bool(re.search(r"<title[^>]*>.*?</title>", combined_html, re.IGNORECASE | re.DOTALL))
    meta_description_present = bool(
        re.search(
            r"<meta[^>]+name=[\"']description[\"'][^>]*content=[\"'][^\"']+",
            combined_html,
            re.IGNORECASE,
        )
    )
    table_heavy = combined_lower.count("<table") >= 3
    old_copyright = bool(re.search(r"copyright\s*(?:&copy;|\(c\))?\s*20(1[0-9]|20)", combined_lower))
    possible_outdated_site = (
        not ssl_enabled or not title_tag_present or not meta_description_present or table_heavy or old_copyright
    )

    signals = {
        "email_found": email_found,
        "contact_page_found": contact_page_found,
        "phone_found_on_site": phone_found_on_site,
        "form_detected": form_detected,
        "chatbot_detected": chatbot_detected,
        "online_booking_detected": online_booking_detected,
        "lead_form_detected": lead_form_detected,
        "calendar_link_detected": calendar_link_detected,
        "wordpress_detected": wordpress_detected,
        "google_analytics_detected": google_analytics_detected,
        "facebook_pixel_detected": facebook_pixel_detected,
        "highlevel_detected": highlevel_detected,
        "hubspot_detected": hubspot_detected,
        "ssl_enabled": ssl_enabled,
        "title_tag_present": title_tag_present,
        "meta_description_present": meta_description_present,
        "possible_outdated_site": possible_outdated_site,
    }

    scoring = score_opportunity(signals)
    return {**signals, **scoring}


def score_opportunity(signals: dict) -> dict:
    score = 5

    if not signals["chatbot_detected"]:
        score += 2
    if not signals["lead_form_detected"]:
        score += 2
    if not signals["online_booking_detected"]:
        score += 1
    if not signals["google_analytics_detected"]:
        score += 1
    if not signals["facebook_pixel_detected"]:
        score += 1
    if signals["possible_outdated_site"]:
        score += 1
    if not signals["meta_description_present"]:
        score += 1
    if signals["email_found"]:
        score += 1

    strong_conversion_tools = (
        signals["chatbot_detected"]
        and (signals["lead_form_detected"] or signals["form_detected"])
        and (signals["online_booking_detected"] or signals["calendar_link_detected"])
    )
    if strong_conversion_tools:
        score -= 2
    if signals["hubspot_detected"]:
        score -= 1
    if signals["highlevel_detected"]:
        score -= 1
    if signals["chatbot_detected"]:
        score -= 1
    if signals["online_booking_detected"]:
        score -= 1

    score = max(1, min(10, score))

    return {
        "opportunity_score": score,
        "opportunity_reason": build_reason(signals),
        "suggested_pitch_angle": build_pitch_angle(signals),
    }


def build_reason(signals: dict) -> str:
    reasons: list[str] = []

    if not signals["chatbot_detected"]:
        reasons.append("no chatbot detected")
    if not signals["lead_form_detected"]:
        reasons.append("no obvious lead form found")
    if not signals["online_booking_detected"]:
        reasons.append("no online booking detected")
    if not signals["google_analytics_detected"] and not signals["facebook_pixel_detected"]:
        reasons.append("limited conversion tracking detected")
    if signals["possible_outdated_site"]:
        reasons.append("the site appears outdated or incomplete")
    if signals["email_found"]:
        reasons.append("a public contact email was found")

    if not reasons:
        return "The site already shows several conversion and marketing tools, so the immediate opportunity may be smaller."

    return _sentence_from_parts(reasons)


def build_pitch_angle(signals: dict) -> str:
    if signals["highlevel_detected"] or signals["hubspot_detected"]:
        return (
            "Your site already has some marketing infrastructure. I can show you where the visitor-to-lead path "
            "may still be leaking opportunities."
        )
    if not signals["chatbot_detected"] and not signals["lead_form_detected"]:
        return (
            "Your site has the basics, but I did not see an instant lead capture or automated follow-up path. "
            "I can show you a simple way to turn more website visitors into booked conversations."
        )
    if signals["possible_outdated_site"]:
        return (
            "Your website may be missing a few modern trust and conversion signals. I can show you quick upgrades "
            "that make it easier for visitors to contact you."
        )
    return (
        "Your website is already doing some things well. I can help identify the next small improvement that turns "
        "more visitors into leads."
    )


def _contains_any(value: str, needles: list[str]) -> bool:
    return any(needle in value for needle in needles)


def _sentence_from_parts(parts: list[str]) -> str:
    if len(parts) == 1:
        return parts[0].capitalize() + "."
    return ", ".join(parts[:-1]).capitalize() + f", and {parts[-1]}."
