import asyncio
import json
from curl_cffi import AsyncSession

from utils.s2_client import client
from database.create_tables import create_tables
from database.crud import add_paper
from database.db_config import SessionLocal

from downloader.download_pdf import download_pdf_from_url
from logging_config import get_logger
from agent.query_generator import generate_queries

logger = get_logger(__name__)

create_tables()

# 1. Get User Input
topic = input("Enter your research topic: ")
logger.info(f"Generating queries for topic: {topic}")

try:
    # 2. Generate Queries
    query_model = generate_queries(topic)
    queries = query_model.queries
    logger.info(f"Generated queries: {queries}")
except Exception as e:
    logger.error(f"Failed to generate queries: {e}")
    # Fallback to using the raw topic if generation fails
    queries = [topic]

# 3. Search and Deduplicate
unique_papers = {}
for i, query in enumerate(queries):
    logger.info(f"Searching for ({i + 1}/{len(queries)}): {query}")
    try:
        # Limit results per query to keep it manageable
        search_results = client.s2_search_api(query=query, max_results=5)
        for paper in search_results:
            pid = paper.get("paper_id")
            # Deduplicate using paper_id
            if pid and pid not in unique_papers:
                unique_papers[pid] = paper
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}")

result = list(unique_papers.values())
logger.info(f"Found {len(result)} unique papers.")

# Save the API results to a separate JSON file for easy inspection/searching
with open("s2_search_results.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4, ensure_ascii=False)
    logger.info("Saved S2 search results to s2_search_results.json")


async def main(papers):
    if not papers:
        logger.warning("No papers found.")
        return

    async with AsyncSession() as session:
        download_tasks = []
        for paper_data in papers:
            url = paper_data.get("open_access_url")
            # Only attempt download if we have a URL
            if url:
                download_tasks.append(
                    download_pdf_from_url(
                        session, url, f"{paper_data.get('paper_id')}.pdf"
                    )
                )
            else:
                logger.warning(f"No open access URL for: {paper_data.get('title')}")

        if download_tasks:
            logger.info(f"Downloading {len(download_tasks)} PDFs...")
            await asyncio.gather(*download_tasks)
        else:
            logger.info("No PDFs to download.")


# 4. Run Async Download
asyncio.run(main(result))

# Database operations (commented out for now)
"""with SessionLocal() as db:
    for paper_data in result:
        paper = add_paper(db, paper_data)
        if paper:
            logger.info(f"Added paper: {paper.title} ({paper.year})")
        else:
            logger.info(f"Skipped existing paper:{paper_data.get('title')}")"""
