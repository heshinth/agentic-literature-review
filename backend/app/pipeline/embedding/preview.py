import json
from pathlib import Path

from .types import SparseEmbeddingRecord


def save_embedding_preview(
    records: list[SparseEmbeddingRecord], output_path: str, max_records: int = 100
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    selected = records[:max_records]
    with path.open("w", encoding="utf-8") as f:
        for item in selected:
            preview = {
                "paper_id": item["paper_id"],
                "title": item["title"],
                "chunk_index": item["chunk_index"],
                "chunk_text_preview": item["chunk_text"][:400],
                "sparse_nnz": len(item["sparse_indices"]),
                "model": item["model"],
            }
            f.write(json.dumps(preview, ensure_ascii=False) + "\n")
