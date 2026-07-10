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
    "chunks_used",
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


def save_document_summary(document_rows, output_dir, filename="document_summary.csv"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = Path(output_dir) / filename

    df = pd.DataFrame(document_rows)

    if df.empty:
        df = pd.DataFrame(columns=[
            "source_url",
            "document_url",
            "local_path",
            "normalized_path",
            "document_text_file",
            "file_type",
            "success",
            "error",
            "character_count",
            "document_analysis_file",
            "analysis_status",
        ])

    df.to_csv(output_path, index=False)
    return output_path


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