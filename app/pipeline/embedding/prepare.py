from fastembed import SparseTextEmbedding

from app.database.crud import get_papers_needing_embedding
from app.database.db_config import SessionLocal

from .chunking import semantic_chunk_text
from .config import BM42_MODEL
from .types import SparseEmbeddingRecord, init_embedding_summary
from .vector_utils import sparse_vector_to_lists


def prepare_sparse_embeddings(
    logger,
    model_name: str = BM42_MODEL,
    max_papers: int | None = None,
) -> tuple[list[SparseEmbeddingRecord], dict[str, int]]:
    records: list[SparseEmbeddingRecord] = []
    summary = init_embedding_summary()

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
                indices, values = sparse_vector_to_lists(vector)
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
