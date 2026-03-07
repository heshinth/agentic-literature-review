import json
import re
from pathlib import Path
from typing import Any

from fastembed import SparseTextEmbedding

from database.crud import get_papers_needing_embedding
from database.db_config import SessionLocal

BM42_MODEL = "Qdrant/bm42-all-minilm-l6-v2-attentions"


def semantic_chunk_text(text: str, max_chars: int = 1400) -> list[str]:
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n\n") if p and p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            sentences = [
                s.strip() for s in re.split(r"(?<=[.!?])\s+", paragraph) if s.strip()
            ]
            for sentence in sentences:
                if not current:
                    current = sentence
                    continue

                candidate = f"{current} {sentence}".strip()
                if len(candidate) <= max_chars:
                    current = candidate
                else:
                    chunks.append(current)
                    current = sentence
            continue

        if not current:
            current = paragraph
            continue

        candidate = f"{current}\n\n{paragraph}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def _sparse_vector_to_lists(vector: Any) -> tuple[list[int], list[float]]:
    if hasattr(vector, "indices") and hasattr(vector, "values"):
        return list(vector.indices), list(vector.values)

    if isinstance(vector, dict):
        return list(vector.get("indices", [])), list(vector.get("values", []))

    raise ValueError(f"Unsupported sparse vector format: {type(vector)}")


def prepare_sparse_embeddings(
    logger,
    model_name: str = BM42_MODEL,
    max_papers: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    records: list[dict[str, Any]] = []
    summary = {
        "papers_considered": 0,
        "papers_with_text": 0,
        "papers_chunked": 0,
        "chunks_total": 0,
        "chunks_embedded": 0,
        "papers_missing_text": 0,
    }

    with SessionLocal() as db:
        papers = get_papers_needing_embedding(db)
        if max_papers is not None:
            papers = papers[:max_papers]

        if not papers:
            logger.info("Embedding step: no papers need embedding.")
            return records, summary

        summary["papers_considered"] = len(papers)
        logger.info(
            "Embedding step: preparing sparse embeddings for %s papers using model %s",
            len(papers),
            model_name,
        )

        embedder = SparseTextEmbedding(model_name=model_name)

        for paper in papers:
            title = getattr(paper, "title", "Unknown title")
            text_obj = getattr(paper, "text_data", None)
            full_text = text_obj.full_text if text_obj else ""

            if not full_text or not full_text.strip():
                summary["papers_missing_text"] += 1
                logger.warning(
                    "Embedding skipped for %s | %s: no extracted text in DB",
                    paper.paper_id,
                    title,
                )
                continue

            summary["papers_with_text"] += 1
            chunks = semantic_chunk_text(full_text)
            if not chunks:
                logger.warning(
                    "Embedding skipped for %s | %s: semantic chunking produced 0 chunks",
                    paper.paper_id,
                    title,
                )
                continue

            summary["papers_chunked"] += 1
            summary["chunks_total"] += len(chunks)

            vectors = list(embedder.embed(chunks))
            for chunk_idx, (chunk_text, vector) in enumerate(zip(chunks, vectors)):
                indices, values = _sparse_vector_to_lists(vector)
                records.append(
                    {
                        "paper_id": paper.paper_id,
                        "title": title,
                        "chunk_index": chunk_idx,
                        "chunk_text": chunk_text,
                        "sparse_indices": indices,
                        "sparse_values": values,
                        "model": model_name,
                    }
                )

            summary["chunks_embedded"] += len(vectors)
            logger.info(
                "Embedded %s | %s: chunks=%s",
                paper.paper_id,
                title,
                len(vectors),
            )

    return records, summary


def save_embedding_preview(
    records: list[dict[str, Any]], output_path: str, max_records: int = 100
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
