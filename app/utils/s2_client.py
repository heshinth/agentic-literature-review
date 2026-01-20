import httpx
import os

class S2Client:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("S2_API_KEY")

        if not self.api_key:
            raise ValueError("S2_API_KEY not set")

        self.client = httpx.Client(
            base_url="https://api.semanticscholar.org/",
            headers={"x-api-key": self.api_key},
            timeout=1.1,
        )

    def s2_search_api(self, query: str, max_results: int = 10) -> dict:
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,abstract,authors,year,paperId,externalIds,url,openAccessPdf",
        }
        response = self.client.get("graph/v1/paper/search/", params=params)
        response.raise_for_status()
        return response.json().get("data", [])

    def get_s2_recommendations(self, limit: int = 10):
        pass


client = S2Client()
