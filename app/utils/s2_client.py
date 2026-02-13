import httpx
import os
from ratelimit import limits, sleep_and_retry

from logging_config import get_logger

logger = get_logger(__name__)
class S2Client:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("S2_API_KEY")

        if not self.api_key:
            logger.error("S2_API_KEY not set")
            raise ValueError("S2_API_KEY not set")

        self.client = httpx.Client(
            base_url="https://api.semanticscholar.org/",
            headers={"x-api-key": self.api_key},
            timeout=30.0,
        )

    @sleep_and_retry
    @limits(calls=1, period=1.05)
    def s2_search_api(self, query: str, max_results: int = 10) -> dict:
        params = {
            "query": query,
            "limit": max_results,
            "openAccessPdf": True,
            "fields": "title,abstract,authors,year,paperId,externalIds,url,isOpenAccess,openAccessPdf,journal",
        }
        response = self.client.get("graph/v1/paper/search/", params=params)
        logger.debug(f"Request URL: {response.url}")
        logger.info(f"S2 Search API response status: {response.status_code}")
        response.raise_for_status()
        data = response.json().get("data", [])

        formatted_data = []
        for item in data:
            formatted_item = {
                "paper_id": item.get("paperId"),
                "doi_id": item.get("externalIds", {}).get("DOI"),
                "arxiv_id": item.get("externalIds", {}).get("ArXiv"),
                "title": item.get("title"),
                "abstract": item.get("abstract"),
                "authors": ", ".join(
                    [author.get("name") for author in item.get("authors", [])]
                ),
                "year": item.get("year"),
                "url": item.get("url"),
                "open_access_url": item.get("openAccessPdf", {}).get("url"),
                "journal": item.get("journal", {}).get("name"),
            }
            formatted_data.append(formatted_item)
        return formatted_data

    def get_s2_recommendations(self, limit: int = 10):
        pass


client = S2Client()
