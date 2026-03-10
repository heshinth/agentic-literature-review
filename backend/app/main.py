import asyncio
import os
import re
import sys
from pathlib import Path

# Allow running as `uv run app/main.py` by adding repo root to import path.
if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from app.database.create_tables import create_tables
from app.logging_config import get_logger
from app.pipeline.search_pipeline import (
    build_queries,
    search_and_deduplicate_papers,
    save_search_results,
)
from app.pipeline.pdf_ingest_pipeline import process_papers
from app.pipeline.embedding import prepare_sparse_embeddings, save_embedding_preview
from app.pipeline.storage import upsert_sparse_embeddings
from app.pipeline.retrieval_pipeline import run_retrieval

logger = get_logger(__name__)

try:
    create_tables()
except Exception as _db_exc:
    logger.error("DB not reachable: %s", _db_exc)
    sys.exit(1)


async def run() -> None:
    topic = input("Enter your research topic: ")
    queries = build_queries(topic, logger)
    papers = search_and_deduplicate_papers(queries, logger)
    save_search_results(papers, logger)

    summary = await process_papers(papers, logger)
    logger.info(
        "Pipeline summary | added_new=%s already_in_db=%s already_extracted=%s "
        "already_downloaded=%s duplicate_url_skipped=%s "
        "missing_paper_id=%s missing_open_access_url=%s download_failed=%s "
        "extract_empty=%s stored_text=%s",
        summary["added_new"],
        summary["already_in_db"],
        summary["already_extracted"],
        summary["already_downloaded"],
        summary["duplicate_url_skipped"],
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

        run_qdrant_step = os.getenv("RUN_QDRANT_STEP", "1") == "1"
        if run_qdrant_step:
            qdrant_collection = os.getenv("QDRANT_COLLECTION", "papers_sparse")
            qdrant_batch_size = int(os.getenv("QDRANT_BATCH_SIZE", "64"))
            qdrant_summary = upsert_sparse_embeddings(
                records=embedding_records,
                logger=logger,
                collection_name=qdrant_collection,
                batch_size=qdrant_batch_size,
            )
            logger.info(
                "Qdrant storage summary | collection=%s records_input=%s records_upserted=%s "
                "batches_total=%s batches_failed=%s papers_marked_embedded=%s",
                qdrant_collection,
                qdrant_summary["records_input"],
                qdrant_summary["records_upserted"],
                qdrant_summary["batches_total"],
                qdrant_summary["batches_failed"],
                qdrant_summary["papers_marked_embedded"],
            )
        else:
            logger.info("Qdrant storage step skipped (RUN_QDRANT_STEP != 1)")
    else:
        logger.info("Embedding step skipped (RUN_EMBEDDING_STEP != 1)")

    # ── Step 7: AI Retrieval & Markdown Summary ───────────────────────────────
    logger.info("Starting AI retrieval for topic: %s", topic)
    markdown = await run_retrieval(topic, logger)
    print("\n" + "=" * 60)
    print(markdown)
    print("=" * 60 + "\n")
    _save_summary(markdown, topic, logger)


def _save_summary(markdown: str, topic: str, logger) -> None:
    """Save the generated markdown summary to outputs/{slug}.md."""
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(exist_ok=True)

    slug = re.sub(r"[^\w]+", "_", topic.lower()).strip("_")
    slug = slug[:80]  # cap filename length
    output_path = outputs_dir / f"{slug}.md"

    output_path.write_text(markdown, encoding="utf-8")
    logger.info("Summary saved to %s", output_path)


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(0)
    except Exception as exc:
        logger.error("Fatal error: %s", exc)
        sys.exit(1)
