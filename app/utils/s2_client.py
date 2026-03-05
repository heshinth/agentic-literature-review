import httpx
import os
import logging
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

S2_DEBUG_FULL_RESPONSE = os.getenv("S2_DEBUG_FULL_RESPONSE", "0") == "1"

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
    @limits(calls=1, period=1.15)
    def s2_search_api(self, query: str, max_results: int = 10) -> dict:
        params = {
            "query": query,
            "limit": max_results,
            "openAccessPdf": True,
            "fields": "title,abstract,authors,year,paperId,externalIds,url,isOpenAccess,openAccessPdf,journal",
        }
        url = "graph/v1/paper/search/"

        # INPUT LOG (what you send)
        logger.info("[S2][INPUT] endpoint=%s params=%s", url, params)

        response = self.client.get(url, params=params)

        # OUTPUT LOG (status + URL)
        logger.info("[S2][OUTPUT] status=%s final_url=%s", response.status_code, response.url)

        # Optional full body log
        if S2_DEBUG_FULL_RESPONSE:
            logger.info("[S2][OUTPUT_BODY] %s", response.text)

        response.raise_for_status()
        data = response.json()

        # Optional summary log
        logger.info("[S2][PARSED] keys=%s", list(data.keys()))

        formatted_data = []
        for item in data.get("data", []):
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
