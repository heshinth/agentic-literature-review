import asyncio
import json
import os
import traceback
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.schemas import ReviewRequest
from app.logging_config import get_logger
from app.pipeline.run_artifacts import generate_run_id, save_run_manifest

router = APIRouter(tags=["review"])

logger = get_logger(__name__)

TOTAL_STEPS = 6


def _is_network_error_message(message: str) -> bool:
    lowered = message.lower()
    return any(
        token in lowered
        for token in (
            "timeout",
            "timed out",
            "connection",
            "network",
            "tls",
            "ssl",
            "dns",
            "refused",
            "unreachable",
            "temporary failure",
            "name resolution",
            "api connection",
            "service unavailable",
            "502",
            "503",
            "504",
        )
    )


def _build_completion_payload(
    markdown: str,
    warnings: list[str],
    network_errors: list[str],
    ingest_summary: dict | None,
    embedding_summary: dict | None,
    qdrant_summary: dict | None,
    success: bool,
    pipeline_error: str | None,
) -> dict:
    failed_paper_ids: list[str] = []
    if ingest_summary and isinstance(ingest_summary.get("failed_paper_ids"), list):
        failed_paper_ids = [str(pid) for pid in ingest_summary["failed_paper_ids"]]

    return {
        "markdown": markdown,
        "success": success,
        "warnings": warnings,
        "network_errors": network_errors,
        "failed_paper_ids": failed_paper_ids,
        "ingest_summary": ingest_summary,
        "embedding_summary": embedding_summary,
        "qdrant_summary": qdrant_summary,
        "pipeline_error": pipeline_error,
    }


def _sse(
    event: str, message: str, step: int | None = None, data: dict | None = None
) -> str:
    payload: dict = {"event": event, "message": message}
    if step is not None:
        payload["step"] = step
        payload["total"] = TOTAL_STEPS
    if data is not None:
        payload["data"] = data
    return f"data: {json.dumps(payload)}\n\n"


async def _event_stream(queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    while True:
        item = await queue.get()
        if item is None:
            break
        yield item


async def _orchestrate(topic: str, queue: asyncio.Queue) -> None:
    run_id = generate_run_id("api")
    started_at = datetime.now(timezone.utc).isoformat()
    queries: list[str] = []
    papers: list[dict] = []
    ingest_summary: dict | None = None
    embedding_summary: dict | None = None
    qdrant_summary: dict | None = None
    markdown = ""
    warnings: list[str] = []
    network_errors: list[str] = []
    pipeline_error: str | None = None
    success = False

    try:
        from app.pipeline.search_pipeline import (
            build_queries,
            search_and_deduplicate_papers,
            save_search_results,
        )
        from app.pipeline.pdf_ingest_pipeline import process_papers
        from app.pipeline.embedding import (
            prepare_sparse_embeddings,
            save_embedding_preview,
        )
        from app.pipeline.storage import upsert_sparse_embeddings
        from app.pipeline.retrieval_pipeline import run_retrieval

        loop = asyncio.get_running_loop()

        # Step 1 — build queries
        await queue.put(_sse("status", "Generating search queries...", step=1))
        queries = await loop.run_in_executor(None, build_queries, topic, logger)

        # Step 2 — search & deduplicate
        await queue.put(_sse("status", "Searching and deduplicating papers...", step=2))
        papers = await loop.run_in_executor(
            None,
            lambda: search_and_deduplicate_papers(queries, logger, topic=topic),
        )
        await loop.run_in_executor(
            None,
            lambda: save_search_results(
                papers,
                logger,
                topic=topic,
                run_id=run_id,
            ),
        )

        # Step 3 — download & extract PDFs
        await queue.put(
            _sse("status", f"Downloading and extracting {len(papers)} PDFs...", step=3)
        )
        ingest_summary = await process_papers(papers, logger)
        if isinstance(ingest_summary, dict):
            download_failed = int(ingest_summary.get("download_failed") or 0)
            failed_ids = ingest_summary.get("failed_paper_ids") or []
            if download_failed:
                warnings.append(f"PDF download failed for {download_failed} paper(s).")
            if failed_ids:
                warnings.append(
                    "Failed paper IDs: " + ", ".join(str(pid) for pid in failed_ids)
                )

            ingest_network_errors = ingest_summary.get("network_errors") or []
            for err in ingest_network_errors:
                text = str(err)
                if text and text not in network_errors:
                    network_errors.append(text)

        # Step 4 — sparse embeddings
        run_embedding = os.getenv("RUN_EMBEDDING_STEP", "1") == "1"
        if run_embedding:
            await queue.put(_sse("status", "Creating sparse embeddings...", step=4))
            embedding_records, embedding_summary = await loop.run_in_executor(
                None, prepare_sparse_embeddings, logger
            )

            preview_path = os.getenv(
                "EMBEDDING_PREVIEW_PATH", "logs/embedding_preview.jsonl"
            )
            preview_count = int(os.getenv("EMBEDDING_PREVIEW_COUNT", "100"))
            await loop.run_in_executor(
                None,
                save_embedding_preview,
                embedding_records,
                preview_path,
                preview_count,
            )

            # Step 5 — upsert to Qdrant
            run_qdrant = os.getenv("RUN_QDRANT_STEP", "1") == "1"
            if run_qdrant:
                await queue.put(_sse("status", "Storing vectors in Qdrant...", step=5))
                collection = os.getenv("QDRANT_COLLECTION", "papers_sparse")
                batch_size = int(os.getenv("QDRANT_BATCH_SIZE", "64"))
                qdrant_summary = await loop.run_in_executor(
                    None,
                    lambda: upsert_sparse_embeddings(
                        records=embedding_records,
                        logger=logger,
                        collection_name=collection,
                        batch_size=batch_size,
                    ),
                )

        # Step 6 — retrieval & review generation
        await queue.put(
            _sse("status", "Running AI retrieval and generating review...", step=6)
        )
        markdown = await run_retrieval(topic, logger)
        success = True

    except Exception as exc:
        pipeline_error = str(exc)
        if _is_network_error_message(pipeline_error):
            network_errors.append(f"pipeline: {pipeline_error}")
        else:
            warnings.append(f"Pipeline exception: {pipeline_error}")
        logger.error("Pipeline error: %s", traceback.format_exc())
        await queue.put(
            _sse(
                "error",
                f"Pipeline failed: {exc}",
                data={
                    "warnings": warnings,
                    "network_errors": network_errors,
                    "pipeline_error": pipeline_error,
                },
            )
        )
    finally:
        completion_payload = _build_completion_payload(
            markdown=markdown,
            warnings=warnings,
            network_errors=network_errors,
            ingest_summary=ingest_summary,
            embedding_summary=embedding_summary,
            qdrant_summary=qdrant_summary,
            success=success,
            pipeline_error=pipeline_error,
        )
        completion_message = "Done!" if success else "Completed with errors"
        await queue.put(
            _sse(
                "result",
                completion_message,
                step=6,
                data=completion_payload,
            )
        )

        finished_at = datetime.now(timezone.utc).isoformat()
        manifest = {
            "run_id": run_id,
            "mode": "api",
            "topic": topic,
            "started_at": started_at,
            "finished_at": finished_at,
            "query_count": len(queries),
            "ranked_paper_count": len(papers),
            "ingest_summary": ingest_summary,
            "embedding_summary": embedding_summary,
            "qdrant_summary": qdrant_summary,
            "markdown_char_count": len(markdown or ""),
            "warnings": warnings,
            "network_errors": network_errors,
            "pipeline_error": pipeline_error,
            "success": success,
        }
        save_run_manifest(manifest, logger, run_id=run_id)
        await queue.put(None)  # sentinel — always close the stream


@router.post("/research")
async def research(request: ReviewRequest) -> StreamingResponse:
    queue: asyncio.Queue = asyncio.Queue()
    asyncio.create_task(_orchestrate(request.topic, queue))
    return StreamingResponse(
        _event_stream(queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
