import os

import pandas as pd

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
