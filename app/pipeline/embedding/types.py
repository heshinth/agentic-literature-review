from typing import TypedDict


class SparseEmbeddingRecord(TypedDict):
    paper_id: str
    title: str
    year: int | None
    authors: str | None
    journal: str | None
    chunk_index: int
    chunk_text: str
    sparse_indices: list[int]
    sparse_values: list[float]
    model: str


def init_embedding_summary() -> dict[str, int]:
    return {
        "papers_considered": 0,
        "papers_with_text": 0,
        "papers_chunked": 0,
        "chunks_total": 0,
        "chunks_embedded": 0,
        "papers_missing_text": 0,
    }
