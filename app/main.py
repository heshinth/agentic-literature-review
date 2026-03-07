import asyncio
import os

from database.create_tables import create_tables
from logging_config import get_logger
from pipeline.search_pipeline import (
    build_queries,
    search_and_deduplicate_papers,
    save_search_results,
)
from pipeline.pdf_ingest_pipeline import process_papers
from pipeline.embedding_pipeline import (
    prepare_sparse_embeddings,
    save_embedding_preview,
)

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

    run_embedding_step = os.getenv("RUN_EMBEDDING_STEP", "1") == "1"
    if run_embedding_step:
        embedding_records, embedding_summary = prepare_sparse_embeddings(logger)

        preview_path = os.getenv(
            "EMBEDDING_PREVIEW_PATH", "logs/embedding_preview.jsonl"
        )
        preview_count = int(os.getenv("EMBEDDING_PREVIEW_COUNT", "100"))
        save_embedding_preview(embedding_records, preview_path, preview_count)

        logger.info(
            "Embedding summary | papers_considered=%s papers_with_text=%s papers_chunked=%s "
            "chunks_total=%s chunks_embedded=%s papers_missing_text=%s preview_file=%s",
            embedding_summary["papers_considered"],
            embedding_summary["papers_with_text"],
            embedding_summary["papers_chunked"],
            embedding_summary["chunks_total"],
            embedding_summary["chunks_embedded"],
            embedding_summary["papers_missing_text"],
            preview_path,
        )
    else:
        logger.info("Embedding step skipped (RUN_EMBEDDING_STEP != 1)")


if __name__ == "__main__":
    asyncio.run(run())
