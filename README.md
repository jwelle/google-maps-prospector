# Local Prospect Finder

Local Prospect Finder is a small Python CLI for local business prospect research. It uses the official Google Places API for discovery, then checks each business's own public website for contact emails and basic website opportunity signals.

It is not a Google Maps scraper. It does not scrape Google Maps pages, send email, enrich contacts through third-party datasets, or integrate with LiveSite AI, GoHighLevel, Supabase, billing, or user accounts in this MVP.

## What It Does

- Accepts a keyword and location.
- Queries Google Places Text Search New.
- Collects business name, address, phone, website, rating, review count, Google Maps URL, and status.
- Visits only a conservative set of public website pages: homepage, `/contact`, `/about`, `/team`, and `/locations`.
- Extracts public email addresses where available.
- Detects simple conversion, marketing, and site quality signals.
- Scores the opportunity from 1 to 10 and writes a CSV.

## Setup

Create and activate a Python 3.11+ environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Copy the example environment file:

```bash
copy .env.example .env
```

Edit `.env` and set:

```env
GOOGLE_MAPS_API_KEY=your_google_places_api_key_here
DEFAULT_MAX_RESULTS=100
REQUEST_TIMEOUT_SECONDS=10
CRAWL_DELAY_SECONDS=1
MAX_PAGES_PER_SITE=5
```

Do not commit `.env`.

The app also supports `.env.local` for local-only secrets. If both `.env.local` and `.env` exist, values from `.env.local` are used first.

## Google Places API Key

1. Open Google Cloud Console.
2. Create or choose a project.
3. Enable billing for the project.
4. Enable the Places API.
5. Create an API key.
6. Restrict the key as appropriate for your environment.
7. Add the key to `.env` as `GOOGLE_MAPS_API_KEY`.

## Usage

Run a live search:

```bash
python src/main.py --keyword "web designers" --location "Texas" --max-results 100
```

Set an explicit output file:

```bash
python src/main.py --keyword "roofers" --location "New Jersey" --max-results 250 --output "output/nj_roofers.csv"
```

Run a local test without Google Places:

```bash
python src/main.py --keyword "web designers" --location "Austin TX" --max-results 5 --skip-places
```

## Local Dashboard

Run the Streamlit dashboard:

```bash
streamlit run dashboard.py
```

The dashboard uses the same workflow as the CLI. It can run live Google Places searches, run sample searches without Google Places, show progress, preview results, save the CSV to `output/`, and download the CSV from the browser.

If no `--output` is provided, the tool writes:

```text
output/{keyword_slug}_{location_slug}_{YYYY-MM-DD}.csv
```

## CSV Output

The CSV includes business details, discovered emails, website signals, an opportunity score, a score reason, and a suggested pitch angle.

Key signal columns include:

- `email_found`
- `contact_page_found`
- `phone_found_on_site`
- `form_detected`
- `chatbot_detected`
- `online_booking_detected`
- `wordpress_detected`
- `google_analytics_detected`
- `facebook_pixel_detected`
- `highlevel_detected`
- `hubspot_detected`
- `ssl_enabled`
- `title_tag_present`
- `meta_description_present`
- `possible_outdated_site`

## Compliance Notes

- Use the official Google Places API for place discovery.
- Do not scrape Google Maps pages directly.
- Respect Google Maps Platform and Places API terms.
- Do not store or use Google-provided data in ways prohibited by Google terms.
- Crawl only the business's own public website.
- Keep crawl limits conservative.
- For outbound email, follow applicable email laws such as CAN-SPAM.
- Include opt-out language in outreach.
- Do not use misleading sender names or subject lines.
- This tool is for prospect research and website analysis, not spam.

## MVP Boundaries

This MVP intentionally excludes user login, billing, Supabase, a React frontend, GoHighLevel integration, LiveSite AI integration, AI-generated outreach, automated emailing, and background job queues.
