from typing import Any


def init_ingest_summary() -> dict[str, Any]:
    return {
        "added_new": 0,
        "already_in_db": 0,
        "already_extracted": 0,
        "already_downloaded": 0,
        "duplicate_url_skipped": 0,
        "missing_paper_id": 0,
        "missing_open_access_url": 0,
        "download_failed": 0,
        "extract_empty": 0,
        "stored_text": 0,
        "failed_paper_ids": [],
        "network_errors": [],
        "download_attempt_errors": {},
    }
