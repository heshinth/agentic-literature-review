import asyncio
import json
import os
from curl_cffi import AsyncSession

from utils.s2_client import client
from database.create_tables import create_tables
from database.crud import add_paper, get_paper_by_id, update_paper_status
from database.db_config import SessionLocal
from database import crud

from downloader.download_pdf import download_pdf_from_url
from logging_config import get_logger
from agent.query_generator import generate_queries
from utils.pdf_extractor import extract_pdf_bytes_by_column

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
            if not isinstance(paper, dict):
                continue
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

    concurrency = int(os.getenv("PIPELINE_CONCURRENCY", "5"))
    semaphore = asyncio.Semaphore(concurrency)

    async def download_and_extract_one(session: AsyncSession, paper_data: dict):
        paper_id = paper_data.get("paper_id")
        if not paper_id:
            return {"paper_id": "unknown", "status": "missing_paper_id", "text": ""}

        url = paper_data.get("open_access_url")
        if not url:
            return {
                "paper_id": paper_id,
                "status": "missing_open_access_url",
                "text": "",
            }

        async with semaphore:
            logger.info(f"Downloading and extracting: {paper_id}")
            pdf_bytes = await download_pdf_from_url(
                session=session,
                pdf_url=url,
                filename=f"{paper_id}.pdf",
                save_to_file=False,
            )

            if not pdf_bytes:
                return {"paper_id": paper_id, "status": "download_failed", "text": ""}

            extracted_text = await asyncio.to_thread(
                extract_pdf_bytes_by_column, pdf_bytes, paper_id
            )
            return {
                "paper_id": paper_id,
                "status": "downloaded_and_extracted",
                "text": extracted_text or "",
            }

    with SessionLocal() as db:
        summary = {
            "added_new": 0,
            "already_in_db": 0,
            "already_extracted": 0,
            "missing_paper_id": 0,
            "missing_open_access_url": 0,
            "download_failed": 0,
            "extract_empty": 0,
            "stored_text": 0,
        }

        # Insert papers first so status tracking is always present
        for paper_data in papers:
            inserted = add_paper(db, paper_data)
            if inserted:
                logger.info(f"Added paper: {inserted.title} ({inserted.year})")
                summary["added_new"] += 1
            else:
                paper_title = paper_data.get("title", "Unknown title")
                logger.info(f"Skipped insert (already in database): {paper_title}")
                summary["already_in_db"] += 1

        papers_to_process = []
        for paper_data in papers:
            paper_id = paper_data.get("paper_id")
            if not paper_id:
                logger.warning("Skipped pipeline item: missing paper_id")
                summary["missing_paper_id"] += 1
                continue

            db_paper = get_paper_by_id(db, paper_id)
            if not db_paper:
                logger.warning(
                    f"Skipped {paper_id}: not found in database after insert step"
                )
                continue

            if db_paper.is_extracted:
                logger.info(f"Skipped {paper_id}: already extracted in database")
                summary["already_extracted"] += 1
                continue

            papers_to_process.append(paper_data)

        if not papers_to_process:
            logger.info("No papers need download/extraction.")
            return

        async with AsyncSession() as session:
            tasks = [
                download_and_extract_one(session, paper_data)
                for paper_data in papers_to_process
            ]
            pipeline_results = await asyncio.gather(*tasks)

        for item in pipeline_results:
            if not item:
                continue

            paper_id = item["paper_id"]
            status = item.get("status")

            if status == "missing_paper_id":
                logger.warning("Skipped pipeline item: missing paper_id")
                summary["missing_paper_id"] += 1
                continue

            if status == "missing_open_access_url":
                logger.warning(f"Skipped {paper_id}: missing open access URL")
                summary["missing_open_access_url"] += 1
                continue

            if status == "download_failed":
                logger.warning(f"Skipped {paper_id}: download failed")
                summary["download_failed"] += 1
                continue

            update_paper_status(db, paper_id, {"is_downloaded": True})

            extracted_text = item["text"]
            if not extracted_text.strip():
                logger.warning(f"Skipped {paper_id}: extract produced empty text")
                summary["extract_empty"] += 1
                continue

            crud.add_paper_text(db, paper_id, extracted_text)
            update_paper_status(db, paper_id, {"is_extracted": True})
            logger.info(f"Stored extracted text for {paper_id}")
            summary["stored_text"] += 1

        logger.info(
            "Pipeline summary | added_new=%s already_in_db=%s already_extracted=%s "
            "missing_paper_id=%s missing_open_access_url=%s download_failed=%s "
            "extract_empty=%s stored_text=%s",
            summary["added_new"],
            summary["already_in_db"],
            summary["already_extracted"],
            summary["missing_paper_id"],
            summary["missing_open_access_url"],
            summary["download_failed"],
            summary["extract_empty"],
            summary["stored_text"],
        )


# 4. Run Async Download
asyncio.run(main(result))
