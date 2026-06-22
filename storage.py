import os
from urllib.parse import urlparse


def ensure_directories(*directories: str) -> None:
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def safe_filename(url: str) -> str:
    parsed = urlparse(url)
    name = parsed.netloc + parsed.path

    if parsed.query:
        name += "_" + parsed.query

    name = (
        name.strip("/")
        .replace("/", "_")
        .replace(":", "_")
        .replace("?", "_")
        .replace("&", "_")
        .replace("=", "_")
    )

    return name or "page"


def save_text(text: str, url: str, output_dir: str) -> str:
    ensure_directories(output_dir)

    filepath = os.path.join(output_dir, safe_filename(url) + ".txt")

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(text)

    return filepath
