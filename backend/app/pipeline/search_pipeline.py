import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.agent.query_generator import generate_queries
from app.utils.s2_client import client


def _tokenize(text: str) -> set[str]:
    if not text:
        return set()
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _paper_relevance_score(paper: dict[str, Any], topic_tokens: set[str]) -> float:
    title_tokens = _tokenize(str(paper.get("title") or ""))
    abstract_tokens = _tokenize(str(paper.get("abstract") or ""))

    if not topic_tokens:
        return 0.0

    title_overlap = len(topic_tokens & title_tokens)
    abstract_overlap = len(topic_tokens & abstract_tokens)

    # Strongly prefer title/abstract lexical overlap with the user topic.
    score = (3.0 * title_overlap) + (2.0 * abstract_overlap)

    year = paper.get("year")
    if isinstance(year, int):
        current_year = datetime.now().year
        recency_bonus = max(0.0, min(1.5, (year - (current_year - 10)) * 0.15))
        score += recency_bonus

    if paper.get("open_access_url"):
        score += 0.25

    if not paper.get("abstract"):
        score -= 0.75

    return round(score, 4)


def rank_and_filter_papers(
    papers: list[dict[str, Any]],
    topic: str,
    logger,
    max_papers: int = 30,
) -> list[dict[str, Any]]:
    if not papers:
        return papers

    topic_tokens = _tokenize(topic)
    if not topic_tokens:
        logger.info("Ranking skipped: topic tokenization produced no terms.")
        return papers[:max_papers]

    scored: list[dict[str, Any]] = []
    for paper in papers:
        score = _paper_relevance_score(paper, topic_tokens)
        item = dict(paper)
        item["relevance_score"] = score
        scored.append(item)

    scored.sort(key=lambda p: p.get("relevance_score", 0.0), reverse=True)
    filtered = scored[:max_papers]

    logger.info(
        "Ranked papers by abstract/title relevance: kept=%s dropped=%s max_papers=%s",
        len(filtered),
        max(0, len(scored) - len(filtered)),
        max_papers,
    )

    if filtered:
        top_preview = [
            {
                "paper_id": p.get("paper_id"),
                "year": p.get("year"),
                "score": p.get("relevance_score"),
            }
            for p in filtered[:5]
        ]
        logger.info("Top ranked paper preview: %s", top_preview)

    return filtered


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
    queries: list[str],
    logger,
    max_results_per_query: int = 5,
    topic: str | None = None,
    max_ranked_papers: int | None = None,
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

    ranking_topic = topic or ""
    ranked_cap = max_ranked_papers
    if ranked_cap is None:
        ranked_cap = int(os.getenv("MAX_RANKED_PAPERS", "30"))

    if ranking_topic.strip():
        return rank_and_filter_papers(
            result,
            topic=ranking_topic,
            logger=logger,
            max_papers=ranked_cap,
        )

    return result


def save_search_results(
    papers: list[dict[str, Any]],
    logger,
    output_file: str = "s2_search_results.json",
    topic: str | None = None,
    run_id: str | None = None,
) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=4, ensure_ascii=False)
    logger.info(f"Saved S2 search results to {output_file}")

    if not topic or not topic.strip():
        return

    ranked_dir = Path(os.getenv("RANKED_ARTIFACT_DIR", "logs/ranked"))
    ranked_dir.mkdir(parents=True, exist_ok=True)

    topic_slug = re.sub(r"[^\w]+", "_", topic.lower()).strip("_")[:80] or "topic"
    artifact_run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifact_path = ranked_dir / f"{artifact_run_id}_{topic_slug}.json"

    ranked_payload = {
        "run_id": artifact_run_id,
        "topic": topic,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "count": len(papers),
        "selection_reason": "Top ranked papers after deduplication and relevance scoring",
        "papers": [
            {
                "rank": idx,
                "paper_id": paper.get("paper_id"),
                "title": paper.get("title"),
                "year": paper.get("year"),
                "relevance_score": paper.get("relevance_score"),
                "has_open_access_url": bool(paper.get("open_access_url")),
            }
            for idx, paper in enumerate(papers, start=1)
        ],
    }

    artifact_path.write_text(
        json.dumps(ranked_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Saved ranked artifact to %s", artifact_path)
