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
    return oa_locations

if __name__ == "__main__":
    sample_doi = "10.3390/instruments6030028"
    oa_info = get_oa_status(sample_doi)
    print(oa_info)