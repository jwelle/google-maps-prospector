from __future__ import annotations

import sys
from base64 import b64encode
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import load_config
from csv_exporter import format_rows_for_csv, rows_to_csv_text
from places_client import PlacesClientError
from prospecting import run_prospecting_workflow


st.set_page_config(page_title="Local Prospect Finder", layout="wide")


def main() -> None:
    st.title("Local Prospect Finder")

    config = load_config()
    default_max_results = max(1, min(config.default_max_results, 250))

    with st.sidebar:
        st.header("Search")
        with st.form("prospect_search"):
            keyword = st.text_input("Keyword", value="web designers")
            location = st.text_input("Location", value="Austin TX")
            max_results = st.number_input("Max results", min_value=1, max_value=250, value=default_max_results, step=1)
            output_path = st.text_input("Output CSV", value="")
            skip_places = st.checkbox("Use sample places", value=False)
            submitted = st.form_submit_button("Run search", type="primary")

        st.divider()
        st.caption("Google Places key loaded" if config.google_maps_api_key else "Google Places key not loaded")

    if "last_result" not in st.session_state:
        st.session_state.last_result = None

    if submitted:
        run_dashboard_search(
            keyword=keyword,
            location=location,
            max_results=int(max_results),
            output_path=output_path.strip() or None,
            skip_places=skip_places,
            config=config,
        )

    render_result()


def run_dashboard_search(keyword: str, location: str, max_results: int, output_path: str | None, skip_places: bool, config) -> None:
    progress_bar = st.progress(0)
    status = st.empty()
    log_area = st.empty()
    log_lines: list[str] = []

    def on_progress(event: dict) -> None:
        if event["event"] == "places_loaded":
            status.info(event["message"])
            log_lines.append(event["message"])
        elif event["event"] == "business_started":
            total = max(event["total"], 1)
            progress_bar.progress((event["index"] - 1) / total)
            status.info(event["message"])
            log_lines.append(f"{event['message']} | {event['website'] or 'no website'}")
        elif event["event"] == "business_finished":
            total = max(event["total"], 1)
            progress_bar.progress(event["index"] / total)
            log_lines.append(
                f"Finished {event['business_name']} | emails: {event['emails_found']} | score: {event['score']}"
            )
        elif event["event"] == "saved":
            progress_bar.progress(1.0)
            status.success(event["message"])
            log_lines.append(event["message"])

        log_area.code("\n".join(log_lines[-12:]), language="text")

    try:
        result = run_prospecting_workflow(
            keyword=keyword,
            location=location,
            max_results=max_results,
            output_path=output_path,
            skip_places=skip_places,
            config=config,
            progress_callback=on_progress,
        )
    except PlacesClientError as exc:
        status.error(str(exc))
        return
    except ValueError as exc:
        status.error(str(exc))
        return

    st.session_state.last_result = result


def render_result() -> None:
    result = st.session_state.last_result
    if result is None:
        st.info("Run a search from the sidebar.")
        return

    rows = result.rows
    if not rows:
        st.warning("No rows are available to download. Run a search that returns results first.")
        return

    emails_found = sum(1 for row in rows if row.get("email_found"))
    average_score = round(sum(int(row.get("opportunity_score", 0)) for row in rows) / len(rows), 1)
    display_rows = format_rows_for_csv(rows)
    csv_text = rows_to_csv_text(rows)
    csv_data = csv_text.encode("utf-8-sig")
    file_name = Path(result.output_path).name

    metric_cols = st.columns(4)
    metric_cols[0].metric("Businesses", len(rows))
    metric_cols[1].metric("With emails", emails_found)
    metric_cols[2].metric("Avg score", average_score)
    metric_cols[3].metric("CSV", result.output_path)

    st.caption(f"Download size: {len(csv_data):,} bytes")
    st.download_button(
        "Download CSV",
        data=csv_data,
        file_name=file_name,
        mime="text/csv;charset=utf-8",
        key=f"download-csv-{result.output_path}-{len(csv_data)}",
        use_container_width=True,
    )
    st.markdown(_csv_download_link(csv_data, file_name), unsafe_allow_html=True)

    st.dataframe(display_rows, use_container_width=True, hide_index=True)

    with st.expander("Top opportunities"):
        top_rows = sorted(display_rows, key=lambda row: int(row.get("opportunity_score", 0)), reverse=True)[:10]
        st.dataframe(top_rows, use_container_width=True, hide_index=True)


def _csv_download_link(csv_data: bytes, file_name: str) -> str:
    encoded = b64encode(csv_data).decode("ascii")
    return f'<a download="{file_name}" href="data:text/csv;charset=utf-8;base64,{encoded}">Fallback CSV download link</a>'


if __name__ == "__main__":
    main()
