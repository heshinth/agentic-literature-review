import httpx
import os


EMAIL = os.getenv("UNPAYWALL_EMAIL", "heshinth2004@gmail.com")


def get_oa_status(doi: str) -> list[str]:
    api_url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": EMAIL}

    response = httpx.get(api_url, params=params)
    response.raise_for_status()

    response = response.json()
    oa_locations = response.get("oa_locations", [])
    oa_locations_url = [loc.get("url_for_pdf") for loc in oa_locations]
    oa_locations_url = [url for url in oa_locations_url if url]
    return oa_locations_url
