import litellm
import os
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from app.agent.prompt_instructions import search_query


class QueryModel(BaseModel):
    queries: List[str] = Field(..., description="List of query strings")
    reasoning: List[str] = Field(..., description="List of reasoning strings")


def generate_queries(
    query: str,
    model: str = "groq/groq/compound",
    api_key_env: Optional[str] = "GROQ_API_KEY",
) -> QueryModel:
    """Generate search queries and reasoning for a given query string."""
    if api_key_env:
        key = os.environ.get(api_key_env)
        if key:
            os.environ["GROQ_API_KEY"] = key

    prompt = search_query(query)
    response = litellm.completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    content = response.choices[0].message.content
    try:
        return QueryModel.model_validate_json(content)
    except (ValidationError, ValueError) as e:
        raise RuntimeError(f"failed to parse model output: {e}")


if __name__ == "__main__":
    result = generate_queries("deep learning for natural language processing")
    print(result.json(indent=2))
