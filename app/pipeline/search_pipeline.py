import json
from typing import Any

from agent.query_generator import generate_queries
from utils.s2_client import client


def build_queries(topic: str, logger) -> list[str]:
    logger.info(f"Generating queries for topic: {topic}")
    try:
        query_model = generate_queries(topic)
        queries = query_model.queries
        logger.info(f"Generated queries: {queries}")
        return queries
    except Exception as e:
        logger.error(f"Failed to generate queries: {e}")
        return [topic]


def search_and_deduplicate_papers(
    queries: list[str], logger, max_results_per_query: int = 5
) -> list[dict[str, Any]]:
    unique_papers: dict[str, dict[str, Any]] = {}

    for i, query in enumerate(queries):
        logger.info(f"Searching for ({i + 1}/{len(queries)}): {query}")
        try:
            search_results = client.s2_search_api(
                query=query, max_results=max_results_per_query
            )
            for paper in search_results:
                if not isinstance(paper, dict):
                    continue
                paper_id = paper.get("paper_id")
                if paper_id and paper_id not in unique_papers:
                    unique_papers[paper_id] = paper
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")

    result = list(unique_papers.values())
    logger.info(f"Found {len(result)} unique papers.")
    return result


def save_search_results(
    papers: list[dict[str, Any]], logger, output_file: str = "s2_search_results.json"
) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=4, ensure_ascii=False)
    logger.info(f"Saved S2 search results to {output_file}")
