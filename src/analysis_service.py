import os
from dataclasses import dataclass
from src.claude_analysis import analyze_text as analyze_with_claude
from config.settings import DEFAULT_CHUNK_SIZE


@dataclass
class AnalysisEstimate:
    source_name: str
    character_count: int
    max_chars: int
    chunk_count: int
    api_key_found: bool


def analyze_text(text: str, source_name: str = "unknown") -> str:
    return analyze_with_claude(text, source_name)


def chunk_text(text: str, max_chars: int = DEFAULT_CHUNK_SIZE) -> list[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than 0.")

    chunks = []
    current = []

    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # Handle paragraphs that exceed the limit on their own.
        if len(paragraph) > max_chars:
            if current:
                chunks.append("\n\n".join(current))
                current = []

            remaining = paragraph

            while len(remaining) > max_chars:
                chunks.append(remaining[:max_chars])
                remaining = remaining[max_chars:]

            if remaining:
                current = [remaining]

            continue

        candidate = "\n\n".join(current + [paragraph])

        if len(candidate) > max_chars and current:
            chunks.append("\n\n".join(current))
            current = [paragraph]
        else:
            current.append(paragraph)

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def estimate_analysis(
    text: str,
    source_name: str = "unknown",
    max_chars: int = DEFAULT_CHUNK_SIZE
) -> AnalysisEstimate:
    chunks = chunk_text(text, max_chars=max_chars)

    return AnalysisEstimate(
        source_name=source_name,
        character_count=len(text),
        max_chars=max_chars,
        chunk_count=len(chunks),
        api_key_found=bool(os.getenv("ANTHROPIC_API_KEY")),
    )


def analyze_large_text(
    text: str,
    source_name: str = "unknown",
    max_chars: int = DEFAULT_CHUNK_SIZE
) -> str:
    if not text or not text.strip():
        raise ValueError(f"{source_name} contains no text to analyze.")

    chunks = chunk_text(text, max_chars=max_chars)

    if len(chunks) == 1:
        return analyze_text(chunks[0], source_name)

    partial_reports = []

    for index, chunk in enumerate(chunks, start=1):
        partial = analyze_text(
            chunk,
            f"{source_name} - chunk {index} of {len(chunks)}"
        )
        partial_reports.append(
            f"# Chunk {index} Analysis\n\n{partial}"
        )

    combined = "\n\n---\n\n".join(partial_reports)

    final_report = analyze_text(
        combined,
        f"{source_name} - combined chunk reports"
    )

    return (
        f"# Final Combined Report\n\n"
        f"{final_report}\n\n"
        f"---\n\n"
        f"# Partial Chunk Reports\n\n"
        f"{combined}"
    )