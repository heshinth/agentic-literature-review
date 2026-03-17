"""Retrieval pipeline: agentic loop over Qdrant sparse search → markdown summary.

Flow:
  1. Check Qdrant point count. If below MIN_POINTS_THRESHOLD, re-trigger ingestion.
  2. Generate initial search queries from the user topic (reuses existing query_generator).
  3. Search Qdrant for each query, collect + deduplicate chunks.
  4. Agentic loop (up to max_rounds total):
       - Ask the LLM: is the current context sufficient?
       - If not, run one additional targeted search (with optional year filter), merge chunks.
  5. Generate the final markdown summary with [^N] citation footnotes.
"""

from typing import Any

from app.agent.retrieval_agent import check_needs_more, generate_summary
from app.database.crud import get_paper_by_id
from app.database.db_config import SessionLocal
from app.pipeline.search_pipeline import build_queries, search_and_deduplicate_papers
from app.pipeline.storage.qdrant_search import (
    get_collection_point_count,
    search_papers,
)

# If Qdrant has fewer points than this after the normal pipeline, re-trigger ingestion.
MIN_POINTS_THRESHOLD = 50

# Number of Qdrant hits to fetch per query.
TOP_K_PER_QUERY = 10


def _merge_chunks(existing: list[dict], new: list[dict]) -> list[dict]:
    """Append new chunks, deduplicating by (paper_id, chunk_index)."""
    seen = {(c["paper_id"], c["chunk_index"]) for c in existing}
    merged = list(existing)
    for chunk in new:
        key = (chunk["paper_id"], chunk["chunk_index"])
        if key not in seen:
            seen.add(key)
            merged.append(chunk)
    return merged


def _fetch_papers_meta(paper_ids: set[str]) -> dict[str, dict[str, Any]]:
    """Batch-fetch full paper metadata from PostgreSQL for citation building."""
    meta: dict[str, dict[str, Any]] = {}
    with SessionLocal() as db:
        for pid in paper_ids:
            paper = get_paper_by_id(db, pid)
            if paper:
                meta[pid] = {
                    "title": paper.title,
                    "authors": paper.authors,
                    "year": paper.year,
                    "url": paper.url or paper.open_access_url or "",
                    "journal": paper.journal,
                }
    return meta


async def _run_ingestion(topic: str, logger) -> None:
    """Re-trigger search → ingest → embed → upsert when Qdrant data is thin."""
    from app.pipeline.embedding.prepare import prepare_sparse_embeddings
    from app.pipeline.pdf_ingest_pipeline import process_papers
    from app.pipeline.storage.qdrant_upsert import upsert_sparse_embeddings

    logger.warning(
        "Qdrant has fewer than %d points — triggering ingestion for topic: %s",
        MIN_POINTS_THRESHOLD,
        topic,
    )

    queries = build_queries(topic, logger)
    papers = search_and_deduplicate_papers(
        queries,
        logger,
        max_results_per_query=5,
        topic=topic,
    )

    if not papers:
        logger.warning("Re-ingestion: no papers found via Semantic Scholar.")
        return

    await process_papers(papers, logger)

    embedding_records, emb_summary = prepare_sparse_embeddings(logger)
    logger.info("Re-ingestion embedding summary: %s", emb_summary)

    if embedding_records:
        upsert_summary = upsert_sparse_embeddings(embedding_records, logger)
        logger.info("Re-ingestion upsert summary: %s", upsert_summary)
    else:
        logger.warning("Re-ingestion: no embedding records produced.")


def _initial_search(queries: list[str], logger) -> list[dict]:
    """Run all initial queries against Qdrant, return merged deduplicated chunks."""
    chunks: list[dict] = []
    for i, query in enumerate(queries):
        logger.info("Retrieval search (%d/%d): %s", i + 1, len(queries), query)
        hits = search_papers(query, top_k=TOP_K_PER_QUERY)
        chunks = _merge_chunks(chunks, hits)
    logger.info(
        "Initial retrieval: %d unique chunks from %d queries.",
        len(chunks),
        len(queries),
    )
    return chunks


async def run_retrieval(
    user_query: str,
    logger,
    max_rounds: int = 3,
) -> str:
    """Run the full agentic retrieval loop and return a markdown summary string.

    Args:
        user_query: The raw user research question.
        logger: Logger instance.
        max_rounds: Total search rounds (including the initial one). Max 3.

    Returns:
        Markdown string: thematic summary with [^N] footnotes + ## References section.
    """
    # ── Step 1: Guard — ensure Qdrant has enough data ────────────────────────
    point_count = get_collection_point_count()
    if point_count < MIN_POINTS_THRESHOLD:
        await _run_ingestion(user_query, logger)
        point_count = get_collection_point_count()

    if point_count == 0:
        logger.error("Qdrant collection is still empty after ingestion attempt.")
        return (
            "# No Results\n\nNo papers were found in the database for your query. "
            "Please check that the ingestion pipeline ran successfully."
        )

    # ── Step 2: Generate initial queries + first search ──────────────────────
    queries = build_queries(user_query, logger)
    chunks = _initial_search(queries, logger)

    if not chunks:
        logger.warning("Initial search returned no chunks from Qdrant.")
        return (
            "# No Results\n\nNo relevant papers were found in the vector database "
            "for your query. The database may need more papers on this topic."
        )

    # ── Step 3: Fetch PostgreSQL metadata for citation building ───────────────
    paper_ids = {c["paper_id"] for c in chunks}
    papers_meta = _fetch_papers_meta(paper_ids)

    # ── Step 4: Agentic loop (rounds 2…max_rounds) ────────────────────────────
    for round_num in range(2, max_rounds + 1):
        decision = check_needs_more(user_query, chunks, papers_meta, round_num)
        logger.info(
            "Round %d context check — needs_more: %s | query: %s | year_min: %s | year_max: %s",
            round_num,
            decision["needs_more_context"],
            decision["additional_query"],
            decision["year_min"],
            decision["year_max"],
        )

        if not decision["needs_more_context"]:
            logger.info(
                "Round %d: LLM judged context sufficient. Stopping loop.", round_num
            )
            break

        additional_query = decision["additional_query"]
        if not additional_query:
            logger.info(
                "Round %d: needs_more_context=True but no query provided. Stopping.",
                round_num,
            )
            break

        filters: dict | None = None
        if decision["year_min"] or decision["year_max"]:
            filters = {
                k: v
                for k, v in {
                    "year_min": decision["year_min"],
                    "year_max": decision["year_max"],
                }.items()
                if v is not None
            }

        logger.info(
            "Round %d: additional search — %s (filters: %s)",
            round_num,
            additional_query,
            filters,
        )
        new_hits = search_papers(
            additional_query, top_k=TOP_K_PER_QUERY, filters=filters
        )
        chunks = _merge_chunks(chunks, new_hits)

        # Fetch metadata for any newly discovered papers
        new_ids = {c["paper_id"] for c in new_hits} - paper_ids
        if new_ids:
            papers_meta.update(_fetch_papers_meta(new_ids))
            paper_ids.update(new_ids)

        logger.info("Round %d: total unique chunks now: %d", round_num, len(chunks))
    else:
        logger.info("Reached max rounds (%d). Proceeding to summary.", max_rounds)

    # ── Step 5: Generate final markdown summary ───────────────────────────────
    logger.info(
        "Generating markdown summary from %d chunks across %d papers.",
        len(chunks),
        len(paper_ids),
    )
    markdown = generate_summary(user_query, chunks, papers_meta)
    return markdown
