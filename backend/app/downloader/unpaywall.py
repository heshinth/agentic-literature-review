import httpx
from rich import print

EMAIL = "heshinth2004@gmail.com"

def get_oa_status(doi: str) -> dict:
    api_url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": EMAIL}

    response = httpx.get(api_url, params=params)
    response.raise_for_status()

    response = response.json()
    oa_locations = response.get("oa_locations", [])
    oa_locations_url = [loc.get("url_for_pdf") for loc in oa_locations]
    return oa_locations_url

if __name__ == "__main__":
    sample_doi = "10.1186/s13643-024-02575-4"
    oa_info = get_oa_status(sample_doi)
    print(oa_info)