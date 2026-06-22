import os

import pandas as pd


def load_urls(input_file: str, test_mode: bool = False, max_urls: int | None = None) -> pd.DataFrame:
    urls = pd.read_csv(input_file)

    if "url" not in urls.columns:
        raise ValueError(f"{input_file} must contain a 'url' column.")

    if test_mode and max_urls is not None:
        urls = urls.head(max_urls)

    return urls


def save_summary(results: list[dict], output_dir: str, filename: str = "summary.csv") -> str:
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    pd.DataFrame(results).to_csv(filepath, index=False)
    return filepath
