from fastembed import SparseTextEmbedding
from qdrant_client import models

from app.pipeline.embedding.config import BM42_MODEL
from app.pipeline.storage.qdrant_client import SPARSE_VECTOR_NAME, get_qdrant_client


def get_collection_point_count(collection_name: str = "papers_sparse") -> int:
    """Return number of points in the collection, or 0 if it does not exist."""
    client = get_qdrant_client()
    try:
        info = client.get_collection(collection_name)
        return info.points_count or 0
    except Exception:
        return 0


def search_papers(
    query: str,
    top_k: int = 10,
    collection_name: str = "papers_sparse",
    filters: dict | None = None,
) -> list[dict]:
    """Sparse-vector search with optional metadata filters.

    Args:
        query: Natural language query string.
        top_k: Maximum number of results to return.
        collection_name: Qdrant collection to search.
        filters: Optional dict with keys year_min and/or year_max (int).

    Returns:
        List of dicts with keys: paper_id, title, chunk_text, chunk_index,
        score, year, authors, journal.
    """
    embedder = SparseTextEmbedding(model_name=BM42_MODEL)
    query_vector = next(iter(embedder.embed([query])))
    indices = query_vector.indices.tolist()
    values = query_vector.values.tolist()

    qdrant_filter = None
    if filters:
        conditions = []
        year_min = filters.get("year_min")
        year_max = filters.get("year_max")
        if year_min is not None:
            conditions.append(
                models.FieldCondition(
                    key="year",
                    range=models.Range(gte=year_min),
                )
            )
        if year_max is not None:
            conditions.append(
                models.FieldCondition(
                    key="year",
                    range=models.Range(lte=year_max),
                )
            )
        if conditions:
            qdrant_filter = models.Filter(must=conditions)

    client = get_qdrant_client()
    results = client.query_points(
        collection_name=collection_name,
        query=models.SparseVector(indices=indices, values=values),
        using=SPARSE_VECTOR_NAME,
        limit=top_k,
        query_filter=qdrant_filter,
        with_payload=True,
    )

    hits = []
    for point in results.points:
        payload = point.payload or {}
        hits.append(
            {
                "paper_id": payload.get("paper_id", ""),
                "title": payload.get("title", ""),
                "chunk_text": payload.get("chunk_text", ""),
                "chunk_index": payload.get("chunk_index", 0),
                "score": point.score,
                "year": payload.get("year"),
                "authors": payload.get("authors"),
                "journal": payload.get("journal"),
            }
        )

    return hits
