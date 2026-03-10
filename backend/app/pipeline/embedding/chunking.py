import re

from .config import DEFAULT_MAX_CHARS


def semantic_chunk_text(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
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
