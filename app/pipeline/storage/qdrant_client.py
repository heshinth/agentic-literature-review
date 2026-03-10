import os

from qdrant_client import QdrantClient, models

SPARSE_VECTOR_NAME = "text"


def get_qdrant_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url=url)


def ensure_sparse_collection(
    client: QdrantClient,
    collection_name: str,
    logger,
) -> None:
    if client.collection_exists(collection_name):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config={},
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: models.SparseVectorParams(
                modifier=models.Modifier.IDF,
            )
        },
    )
    logger.info("Created Qdrant collection: %s", collection_name)
