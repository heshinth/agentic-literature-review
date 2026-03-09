import asyncio
import json
import os
import traceback
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.schemas import ReviewRequest
from app.logging_config import get_logger

router = APIRouter(tags=["review"])

logger = get_logger(__name__)

TOTAL_STEPS = 6


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
            None, search_and_deduplicate_papers, queries, logger
        )
        await loop.run_in_executor(None, save_search_results, papers, logger)

        # Step 3 — download & extract PDFs
        await queue.put(
            _sse("status", f"Downloading and extracting {len(papers)} PDFs...", step=3)
        )
        await process_papers(papers, logger)

        # Step 4 — sparse embeddings
        run_embedding = os.getenv("RUN_EMBEDDING_STEP", "1") == "1"
        if run_embedding:
            await queue.put(_sse("status", "Creating sparse embeddings...", step=4))
            embedding_records, _ = await loop.run_in_executor(
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
                await loop.run_in_executor(
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

        await queue.put(_sse("result", "Done!", step=6, data={"markdown": markdown}))

    except Exception as exc:
        logger.error("Pipeline error: %s", traceback.format_exc())
        await queue.put(_sse("error", f"Pipeline failed: {exc}"))
    finally:
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
