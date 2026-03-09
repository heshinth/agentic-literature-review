import json

from app.agent.groq_client import client as groq_client
from app.agent.prompt_instructions import (
    needs_more_context_prompt,
    retrieval_summary_prompt,
)

# Fast small model for binary context-sufficiency check (6K TPM on free tier).
_CHECK_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
# Larger model for final summary quality (12K TPM on free tier).
_SUMMARY_MODEL = "llama-3.3-70b-versatile"

# Hard caps to stay within free-tier token limits.
_MAX_CONTEXT_CHUNKS = 25  # chunks passed to any LLM call
_MAX_EXCERPT_CHARS = 800  # characters per chunk excerpt in the prompt


def _build_context_str(
    chunks: list[dict],
    papers_meta: dict,
) -> tuple[str, list[dict]]:
    """Deduplicate chunks, assign per-paper citation numbers, build context string.

    Args:
        chunks: List of chunk dicts from Qdrant search results.
        papers_meta: Dict keyed by paper_id with full metadata from PostgreSQL.

    Returns:
        Tuple of (formatted context string, ordered citation metadata list).
    """
    # Deduplicate by (paper_id, chunk_index), then cap to budget
    seen_keys: set[tuple[str, int]] = set()
    unique_chunks: list[dict] = []
    for chunk in chunks:
        key = (chunk["paper_id"], chunk["chunk_index"])
        if key not in seen_keys:
            seen_keys.add(key)
            unique_chunks.append(chunk)

    unique_chunks = unique_chunks[:_MAX_CONTEXT_CHUNKS]

    # Assign sequential citation numbers grouped by paper (order of first appearance)
    paper_citation_num: dict[str, int] = {}
    next_num = 1
    for chunk in unique_chunks:
        pid = chunk["paper_id"]
        if pid not in paper_citation_num:
            paper_citation_num[pid] = next_num
            next_num += 1

    # Build formatted context string
    lines: list[str] = []
    for chunk in unique_chunks:
        pid = chunk["paper_id"]
        n = paper_citation_num[pid]
        meta = papers_meta.get(pid, {})

        title = meta.get("title") or chunk.get("title") or "Unknown Title"
        authors = meta.get("authors") or chunk.get("authors") or ""
        year = meta.get("year") or chunk.get("year") or ""
        journal = meta.get("journal") or chunk.get("journal") or ""

        header = f'[{n}] "{title}"'
        if authors or year:
            parts = []
            if authors:
                parts.append(authors)
            if year:
                parts.append(str(year))
            header += f" ({', '.join(parts)})"
        if journal:
            header += f" — {journal}"

        excerpt = chunk["chunk_text"]
        if len(excerpt) > _MAX_EXCERPT_CHARS:
            excerpt = excerpt[:_MAX_EXCERPT_CHARS].rstrip() + "…"

        lines.append(header)
        lines.append(f'Excerpt: "{excerpt}"')
        lines.append("")

    context_str = "\n".join(lines).strip()

    # Build ordered citation metadata list (one entry per unique paper)
    citation_list: list[dict] = []
    seen_pids: set[str] = set()
    for chunk in unique_chunks:
        pid = chunk["paper_id"]
        if pid not in seen_pids:
            seen_pids.add(pid)
            meta = papers_meta.get(pid, {})
            citation_list.append(
                {
                    "citation_num": paper_citation_num[pid],
                    "paper_id": pid,
                    "title": meta.get("title") or chunk.get("title", ""),
                    "authors": meta.get("authors") or chunk.get("authors", ""),
                    "year": meta.get("year") or chunk.get("year"),
                    "url": meta.get("url") or meta.get("open_access_url") or "",
                }
            )

    return context_str, citation_list


def check_needs_more(
    user_query: str,
    chunks: list[dict],
    papers_meta: dict,
    round_num: int,
) -> dict:
    """Ask the LLM whether the current context is sufficient.

    Returns a dict with keys: needs_more_context (bool), additional_query (str|None),
    year_min (int|None), year_max (int|None).
    """
    context_str, _ = _build_context_str(chunks, papers_meta)
    prompt = needs_more_context_prompt(user_query, context_str, round_num)

    response = groq_client.chat.completions.create(
        model=_CHECK_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content

    try:
        result = json.loads(content)
        return {
            "needs_more_context": bool(result.get("needs_more_context", False)),
            "additional_query": result.get("additional_query") or None,
            "year_min": result.get("year_min") or None,
            "year_max": result.get("year_max") or None,
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "needs_more_context": False,
            "additional_query": None,
            "year_min": None,
            "year_max": None,
        }


def generate_summary(
    user_query: str,
    chunks: list[dict],
    papers_meta: dict,
) -> str:
    """Generate a markdown literature review summary from the accumulated chunks.

    Returns the full markdown string including the References section.
    """
    context_str, _ = _build_context_str(chunks, papers_meta)
    prompt = retrieval_summary_prompt(user_query, context_str)

    response = groq_client.chat.completions.create(
        model=_SUMMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content

    try:
        result = json.loads(content)
        return result.get("summary", content)
    except (json.JSONDecodeError, ValueError):
        return content
