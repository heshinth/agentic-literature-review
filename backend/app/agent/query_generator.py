from pydantic import BaseModel, Field, ValidationError
from typing import List
from .prompt_instructions import search_query
from .groq_client import client


class QueryModel(BaseModel):
    queries: List[str] = Field(..., description="List of query strings")
    reasoning: List[str] = Field(..., description="List of reasoning strings")


def generate_queries(
    query: str,
    model: str = "llama-3.3-70b-versatile",
) -> QueryModel:
    """Generate search queries and reasoning for a given query string."""
    prompt = search_query(query)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    try:
        return QueryModel.model_validate_json(content)
    except (ValidationError, ValueError) as e:
        raise RuntimeError(f"failed to parse model output: {e}")


if __name__ == "__main__":
    result = generate_queries("deep learning for natural language processing")
    print(result.json(indent=2))
