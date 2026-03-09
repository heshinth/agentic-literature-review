from collections import defaultdict
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import models

from app.database.crud import update_paper_status
from app.database.db_config import SessionLocal
from app.pipeline.storage.qdrant_client import (
    SPARSE_VECTOR_NAME,
    ensure_sparse_collection,
    get_qdrant_client,
)


def _chunked(items: list[Any], size: int) -> list[list[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _build_point_id(paper_id: str, chunk_index: int) -> str:
    return str(uuid5(NAMESPACE_URL, f"{paper_id}:{chunk_index}"))


def upsert_sparse_embeddings(
    records: list[dict[str, Any]],
    logger,
    collection_name: str = "papers_sparse",
    batch_size: int = 64,
) -> dict[str, int]:
    summary = {
        "records_input": len(records),
        "records_upserted": 0,
        "batches_total": 0,
        "batches_failed": 0,
        "papers_marked_embedded": 0,
    }

    if not records:
        logger.info("Qdrant step: no embedding records to upsert.")
        return summary

    client = get_qdrant_client()
    ensure_sparse_collection(client, collection_name, logger)

    successful_papers: set[str] = set()
    grouped_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in records:
        grouped_records[item["paper_id"]].append(item)

    for paper_id, paper_records in grouped_records.items():
        paper_batches = _chunked(paper_records, batch_size)
        paper_ok = True

        for batch in paper_batches:
            summary["batches_total"] += 1
            points: list[models.PointStruct] = []

            for item in batch:
                point_id = _build_point_id(item["paper_id"], item["chunk_index"])
                sparse_vector = models.SparseVector(
                    indices=item["sparse_indices"],
                    values=item["sparse_values"],
                )
                payload = {
                    "paper_id": item["paper_id"],
                    "title": item["title"],
                    "year": item.get("year"),
                    "authors": item.get("authors"),
                    "journal": item.get("journal"),
                    "chunk_index": item["chunk_index"],
                    "chunk_text": item["chunk_text"],
                    "model": item["model"],
                }
                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector={SPARSE_VECTOR_NAME: sparse_vector},
                        payload=payload,
                    )
                )

            try:
                client.upsert(collection_name=collection_name, points=points, wait=True)
                summary["records_upserted"] += len(points)
            except Exception as e:
                paper_ok = False
                summary["batches_failed"] += 1
                logger.error(
                    "Qdrant upsert failed for paper %s batch of %s points: %s",
                    paper_id,
                    len(points),
                    e,
                )

        if paper_ok:
            successful_papers.add(paper_id)

    if successful_papers:
        with SessionLocal() as db:
            for paper_id in successful_papers:
                update_paper_status(db, paper_id, {"is_embedded": True})

    summary["papers_marked_embedded"] = len(successful_papers)
    logger.info(
        "Qdrant summary | collection=%s records_input=%s records_upserted=%s "
        "batches_total=%s batches_failed=%s papers_marked_embedded=%s",
        collection_name,
        summary["records_input"],
        summary["records_upserted"],
        summary["batches_total"],
        summary["batches_failed"],
        summary["papers_marked_embedded"],
    )

    return summary
