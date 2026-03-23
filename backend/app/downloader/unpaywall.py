import httpx
import os
import time
from functools import lru_cache


EMAIL = os.getenv("UNPAYWALL_EMAIL", "heshinth2004@gmail.com")
UNPAYWALL_TIMEOUT_SECONDS = float(os.getenv("UNPAYWALL_TIMEOUT_SECONDS", "12"))
UNPAYWALL_MAX_RETRIES = int(os.getenv("UNPAYWALL_MAX_RETRIES", "3"))


def _normalize_doi(doi: str) -> str:
    value = doi.strip()
    value = value.removeprefix("https://doi.org/")
    value = value.removeprefix("http://doi.org/")
    return value


@lru_cache(maxsize=512)
def _cached_oa_status(doi: str, email: str) -> tuple[str, ...]:
    api_url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": email}

    last_error: Exception | None = None
    for attempt in range(UNPAYWALL_MAX_RETRIES):
        try:
            response = httpx.get(api_url, params=params, timeout=UNPAYWALL_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
            oa_locations = payload.get("oa_locations", [])
            oa_locations_url = [loc.get("url_for_pdf") for loc in oa_locations]
            oa_locations_url = [url for url in oa_locations_url if url]
            return tuple(oa_locations_url)
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            last_error = exc
            # Retry on transient failures.
            if attempt < UNPAYWALL_MAX_RETRIES - 1:
                time.sleep(0.5 * (attempt + 1))

    if last_error:
        raise last_error
    return tuple()


def get_oa_status(doi: str) -> list[str]:
    doi_norm = _normalize_doi(doi)
    return list(_cached_oa_status(doi_norm, EMAIL))
