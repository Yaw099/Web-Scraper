import os
from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping, Sequence

from src.claude_analysis import (
    EVIDENCE_MEMO_MODE,
    FINAL_REPORT_MODE,
    analyze_text as analyze_with_claude,
)
from config.settings import DEFAULT_CHUNK_SIZE

MIN_CONSOLIDATION_CHARS = 100_000


@dataclass
class AnalysisEstimate:
    source_name: str
    character_count: int
    max_chars: int
    chunk_count: int
    api_key_found: bool


@dataclass(frozen=True)
class SourceContent:
    """One piece of content collected for an original input URL."""

    name: str
    text: str
    url: str = ""


def analyze_text(
    text: str,
    source_name: str = "unknown",
    research_instructions: str = "",
    source_url: str = "",
    enable_web_search: bool = False,
    max_web_searches: int = 5,
    analysis_mode: str = FINAL_REPORT_MODE,
) -> str:
    return analyze_with_claude(
        text,
        source_name,
        research_instructions=research_instructions,
        source_url=source_url,
        enable_web_search=enable_web_search,
        max_web_searches=max_web_searches,
        analysis_mode=analysis_mode,
    )


def _coerce_source_content(item: SourceContent | Mapping[str, object]) -> SourceContent:
    """Accept SourceContent objects or the dictionaries produced by the pipeline."""

    if isinstance(item, SourceContent):
        return item

    name = str(item.get("name") or "Untitled source")
    text = str(item.get("text") or "")
    url = str(item.get("url") or "")

    return SourceContent(name=name, text=text, url=url)


def combine_source_content(
    content_items: Sequence[SourceContent | Mapping[str, object]],
) -> str:
    """Combine source material while keeping each source's provenance visible."""

    sections = []
    seen_content_hashes = set()

    source_number = 0

    for raw_item in content_items:
        item = _coerce_source_content(raw_item)

        if not item.text.strip():
            continue

        content_hash = sha256(
            item.text.strip().encode("utf-8")
        ).hexdigest()

        if content_hash in seen_content_hashes:
            continue

        seen_content_hashes.add(content_hash)

        source_number += 1

        source_details = [
            f"===== SOURCE {source_number} =====",
            f"Name: {item.name}",
        ]

        if item.url.strip():
            source_details.append(f"URL: {item.url}")

        source_details.append("")
        source_details.append(item.text.strip())
        sections.append("\n".join(source_details))

    if not sections:
        raise ValueError("No non-empty source content was provided for analysis.")

    return "\n\n".join(sections)


def build_source_bundle_text(
    content_items: Sequence[SourceContent | Mapping[str, object]],
    research_instructions: str = "",
) -> str:
    """Prepare one link-level analysis request from the collected sources."""

    combined_sources = combine_source_content(content_items)
    instructions = research_instructions.strip()

    if not instructions:
        return combined_sources

    return (
        "===== USER RESEARCH INSTRUCTIONS =====\n"
        f"{instructions}\n\n"
        "===== COLLECTED SOURCE CONTENT =====\n\n"
        f"{combined_sources}"
    )


def analyze_source_bundle(
    source_url: str,
    content_items: Sequence[SourceContent | Mapping[str, object]],
    research_instructions: str = "",
    max_chars: int = DEFAULT_CHUNK_SIZE,
    enable_web_search: bool = False,
    max_web_searches: int = 5,
) -> str:
    """Create one analysis report for an original input URL and its sources.

    The caller can supply the scraped page plus any extracted documents found
    from that page. This function deliberately delegates to the existing
    chunking workflow so the current file-based analysis features continue to
    work while the GUI is converted to link-based analysis.
    """

    if not source_url or not source_url.strip():
        raise ValueError("A source URL is required for link-based analysis.")

    bundle_text = combine_source_content(content_items)

    return analyze_large_text(
        bundle_text,
        source_name=f"Source bundle: {source_url}",
        max_chars=max_chars,
        research_instructions=research_instructions,
        source_url=source_url,
        enable_web_search=enable_web_search,
        max_web_searches=max_web_searches,
    )


def analyze_source_collection(
    source_urls: Sequence[str],
    content_items: Sequence[SourceContent | Mapping[str, object]],
    research_instructions: str = "",
    max_chars: int = DEFAULT_CHUNK_SIZE,
    enable_web_search: bool = False,
    max_web_searches: int = 5,
) -> str:
    """Create one report from source material collected from several URLs."""

    clean_urls = [url.strip() for url in source_urls if url and url.strip()]

    if not clean_urls:
        raise ValueError("At least one source URL is required for bulk analysis.")

    bundle_text = combine_source_content(content_items)
    source_url_summary = "Multiple selected URLs:\n" + "\n".join(clean_urls)

    return analyze_large_text(
        bundle_text,
        source_name=(
            f"Source collection: {len(clean_urls)} original URL(s)"
        ),
        max_chars=max_chars,
        research_instructions=research_instructions,
        source_url=source_url_summary,
        enable_web_search=enable_web_search,
        max_web_searches=max_web_searches,
    )


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


def consolidate_partial_reports(
    partial_reports: list[str],
    source_name: str,
    max_chars: int,
    research_instructions: str = "",
    source_url: str = "",
    enable_web_search: bool = False,
    max_web_searches: int = 5,
) -> str:
    """Reduce partial reports in groups until one final report remains."""

    current_reports = partial_reports
    round_number = 1
    consolidation_max_chars = max(max_chars, MIN_CONSOLIDATION_CHARS)

    while len(current_reports) > 1:
        combined_reports = "\n\n---\n\n".join(current_reports)

        report_groups = chunk_text(
            combined_reports,
            max_chars=consolidation_max_chars,
        )

        next_reports = []
        is_final_consolidation = len(report_groups) == 1

        for group_index, group in enumerate(report_groups, start=1):
            report = analyze_text(
                group,
                (
                    f"{source_name} - consolidation round "
                    f"{round_number}, group {group_index} of "
                    f"{len(report_groups)}"
                ),
                research_instructions=research_instructions,
                source_url=source_url,
                enable_web_search=(
                    enable_web_search and is_final_consolidation
                ),
                max_web_searches=max_web_searches,
                analysis_mode=(
                    FINAL_REPORT_MODE
                    if is_final_consolidation
                    else EVIDENCE_MEMO_MODE
                ),
            )
            next_reports.append(report)

        if len(next_reports) >= len(current_reports):
            raise RuntimeError(
                "Consolidation did not reduce the number of reports. "
                "Use a smaller Claude chunk size and try again."
            )

        current_reports = next_reports
        round_number += 1

    return current_reports[0]


def analyze_large_text(
    text: str,
    source_name: str = "unknown",
    max_chars: int = DEFAULT_CHUNK_SIZE,
    research_instructions: str = "",
    source_url: str = "",
    enable_web_search: bool = False,
    max_web_searches: int = 5,
) -> str:
    if not text or not text.strip():
        raise ValueError(f"{source_name} contains no text to analyze.")

    chunks = chunk_text(text, max_chars=max_chars)

    if len(chunks) == 1:
        return analyze_text(
            chunks[0],
            source_name,
            research_instructions=research_instructions,
            source_url=source_url,
            enable_web_search=enable_web_search,
            max_web_searches=max_web_searches,
            analysis_mode=FINAL_REPORT_MODE,
        )

    partial_reports = []

    for index, chunk in enumerate(chunks, start=1):
        partial = analyze_text(
            chunk,
            f"{source_name} - chunk {index} of {len(chunks)}",
            research_instructions=research_instructions,
            source_url=source_url,
            enable_web_search=False,
            max_web_searches=max_web_searches,
            analysis_mode=EVIDENCE_MEMO_MODE,
        )
        partial_reports.append(
            f"# Chunk {index} Evidence Memo\n\n{partial}"
        )

    final_report = consolidate_partial_reports(
        partial_reports,
        source_name=source_name,
        max_chars=max_chars,
        research_instructions=research_instructions,
        source_url=source_url,
        enable_web_search=enable_web_search,
        max_web_searches=max_web_searches,
    )

    return f"# Final Combined Report\n\n{final_report}"
