from typing import Any


def sparse_vector_to_lists(vector: Any) -> tuple[list[int], list[float]]:
    if hasattr(vector, "indices") and hasattr(vector, "values"):
        return list(vector.indices), list(vector.values)

    if isinstance(vector, dict):
        return list(vector.get("indices", [])), list(vector.get("values", []))

    raise ValueError(f"Unsupported sparse vector format: {type(vector)}")
