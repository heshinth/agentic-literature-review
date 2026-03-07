import asyncio

from database.create_tables import create_tables
from logging_config import get_logger
from pipeline.search_pipeline import (
    build_queries,
    search_and_deduplicate_papers,
    save_search_results,
)
from pipeline.pdf_ingest_pipeline import process_papers

logger = get_logger(__name__)

create_tables()


async def run() -> None:
    topic = input("Enter your research topic: ")
    queries = build_queries(topic, logger)
    papers = search_and_deduplicate_papers(queries, logger)
    save_search_results(papers, logger)

    summary = await process_papers(papers, logger)
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


if __name__ == "__main__":
    asyncio.run(run())
