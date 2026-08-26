import os

import pandas as pd
from pathlib import Path

SUMMARY_COLUMNS = [
    "url",
    "status",
    "text_file",
    "character_count",
    "transcript_status",
    "transcript_file",
    "analysis_status",
    "analysis_file",
    "analysis_character_count",
    "analysis_error",
    "chunks_used",
]

DOCUMENT_SUMMARY_COLUMNS = [
    "source_url",
    "document_url",
    "local_path",
    "normalized_path",
    "archive_path",
    "document_text_file",
    "file_type",
    "success",
    "error",
    "character_count",
    "extraction_status",
    "extraction_error",
    "document_analysis_file",
    "analysis_status",
]

def load_urls(input_file: str, test_mode: bool = False, max_urls: int | None = None) -> pd.DataFrame:
    urls = pd.read_csv(input_file)

    if "url" not in urls.columns:
        raise ValueError(f"{input_file} must contain a 'url' column.")

    if test_mode and max_urls is not None:
        urls = urls.head(max_urls)

    return urls


def save_summary(results, output_dir, filename):
    os.makedirs(output_dir, exist_ok=True)

    df = pd.DataFrame(results)

    for column in SUMMARY_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[SUMMARY_COLUMNS]

    summary_path = os.path.join(output_dir, filename)
    df.to_csv(summary_path, index=False)

    return summary_path


def update_link_analysis_result(
    source_url: str,
    output_dir,
    analysis_status: str,
    analysis_file: str = "",
    analysis_character_count: int = 0,
    analysis_error: str = "",
    filename="summary.csv",
) -> Path:
    """Record the result of one link-level Claude analysis in summary.csv."""

    output_path = Path(output_dir) / filename

    if not output_path.exists():
        raise FileNotFoundError(
            f"Summary not found: {output_path}. Run the pipeline first."
        )

    df = pd.read_csv(output_path, dtype=str, keep_default_na=False)

    for column in SUMMARY_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    matches = df["url"].astype(str).eq(source_url)

    if not matches.any():
        raise ValueError(f"No summary row found for source URL: {source_url}")

    df.loc[matches, "analysis_status"] = analysis_status
    df.loc[matches, "analysis_file"] = analysis_file
    df.loc[matches, "analysis_character_count"] = str(
        analysis_character_count
    )
    df.loc[matches, "analysis_error"] = analysis_error

    df = df[SUMMARY_COLUMNS]
    df.to_csv(output_path, index=False)

    return output_path


def save_document_summary(document_rows, output_dir, filename="document_summary.csv"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / filename

    df = pd.DataFrame(document_rows)

    for column in DOCUMENT_SUMMARY_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    df = df[DOCUMENT_SUMMARY_COLUMNS]
    df.to_csv(output_path, index=False)
    return output_path


def _path_key(path_value) -> str:
    """Create a stable comparison key for document paths."""

    if path_value is None or pd.isna(path_value):
        return ""

    value = str(path_value).strip()
    if not value:
        return ""

    return str(Path(value).resolve()).casefold()


def update_document_extraction_results(
    extraction_rows,
    output_dir,
    filename="document_summary.csv",
) -> tuple[Path, int]:
    """Record document-text extraction outcomes in document_summary.csv.

    A document can appear under more than one source URL, so every matching
    row is updated. The download ``success`` and ``error`` fields are left
    untouched; extraction has its own status and error fields.
    """

    output_path = Path(output_dir) / filename

    if not output_path.exists():
        raise FileNotFoundError(
            f"Document summary not found: {output_path}. Run the pipeline first."
        )

    df = pd.read_csv(output_path, dtype=str, keep_default_na=False)

    for column in DOCUMENT_SUMMARY_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    updated_rows = 0

    for extraction in extraction_rows:
        local_key = _path_key(extraction.get("local_path"))
        normalized_key = _path_key(extraction.get("normalized_path"))
        matching_keys = {key for key in (local_key, normalized_key) if key}

        if not matching_keys:
            continue

        local_matches = df["local_path"].map(_path_key).isin(matching_keys)
        normalized_matches = (
            df["normalized_path"].map(_path_key).isin(matching_keys)
        )
        matches = local_matches | normalized_matches

        if not matches.any():
            continue

        updated_rows += int(matches.sum())
        status = extraction.get("extraction_status", "failed")
        error = extraction.get("extraction_error", "")

        df.loc[matches, "normalized_path"] = str(
            extraction.get("normalized_path") or ""
        )
        df.loc[matches, "extraction_status"] = status
        df.loc[matches, "extraction_error"] = str(error or "")

        if status == "extracted":
            df.loc[matches, "document_text_file"] = str(
                extraction.get("document_text_file") or ""
            )
            df.loc[matches, "character_count"] = str(
                extraction.get("character_count") or 0
            )

    df = df[DOCUMENT_SUMMARY_COLUMNS]
    df.to_csv(output_path, index=False)

    return output_path, updated_rows


def save_discovered_meetings(discovered_rows, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, "discovered_meetings.csv")

    columns = [
        "source_url",
        "meeting_url",
        "status",
        "transcript_file",
    ]

    df = pd.DataFrame(discovered_rows)

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    df = df[columns]
    df.to_csv(filepath, index=False)

    return filepath
