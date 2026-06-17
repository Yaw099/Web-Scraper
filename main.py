import os
import pandas as pd
from bs4 import BeautifulSoup
import subprocess
import tempfile
import shutil
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

INPUT_FILE = "urls.csv"
OUTPUT_DIR = "output"

def extract_structured_content(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    lines = []

    title = soup.find("title")
    if title:
        lines.append(f"# Page Title\n{title.get_text(strip=True)}\n")

    lines.append("# Headings")
    for h in soup.find_all(["h1", "h2", "h3", "h4"]):
        text = h.get_text(" ", strip=True)
        if text:
            lines.append(f"- {text}")

    lines.append("\n# Paragraphs")
    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)
        if text:
            lines.append(text)

    lines.append("\n# Tables")
    for i, table in enumerate(soup.find_all("table"), start=1):
        lines.append(f"\n## Table {i}")
        for row in table.find_all("tr"):
            cells = row.find_all(["th", "td"])
            values = [cell.get_text(" ", strip=True) for cell in cells]
            if values:
                lines.append(" | ".join(values))

    lines.append("\n# Links")
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        href = urljoin(url, a["href"])
        if text:
            lines.append(f"- {text}: {href}")

    lines.append("\n# Full Visible Text")
    body_text = soup.get_text("\n", strip=True)
    lines.append(body_text)

    return "\n".join(lines)


def download_audio_temp(url: str) -> str | None:
    temp_dir = tempfile.mkdtemp()

    output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

    command = [
        "py",
        "-m",
        "yt_dlp",
        "--playlist-items", "1",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "--output", output_template,
        url
    ]

    try:
        subprocess.run(command, check=True)

        for filename in os.listdir(temp_dir):
            if filename.endswith((".mp3", ".m4a", ".wav")):
                return os.path.join(temp_dir, filename)

        return None

    except subprocess.CalledProcessError as e:
        print(f"Audio download failed: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None


def is_video_page(url: str) -> bool:
    return "adminmonitor.com" in url.lower()


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


def fetch_html(url: str) -> str | None:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(ignore_https_errors=True)
            page.goto(url, wait_until="networkidle", timeout=60000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    DOWNLOAD_AUDIO = True

    urls = pd.read_csv(INPUT_FILE)

    TEST_MODE = True
    MAX_URLS = 1

    if TEST_MODE:
        urls = urls.head(MAX_URLS)

    results = []

    for _, row in urls.iterrows():
        url = row["url"]
        print(f"Processing: {url}")

        html = fetch_html(url)

        if not html:
            results.append({
                "url": url,
                "status": "failed",
                "text_file": ""
            })
            continue

        print(f"Downloaded {len(html):,} characters")

        text = extract_structured_content(html, url)
        filename = safe_filename(url) + ".txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        
        transcript_status = ""

        # Only do this for AdminMonitor pages
        if DOWNLOAD_AUDIO and is_video_page(url):

            audio_path = download_audio_temp(url)

            if audio_path:

                try:
                    print(f"Downloaded audio to {audio_path}")

                    #
                    # TRANSCRIPTION WILL GO HERE LATER
                    #
                    # transcript = transcribe(audio_path)
                    #
                    # save_transcript(transcript, url)
                    #

                    transcript_status = "ready_for_transcription"

                finally:
                    shutil.rmtree(os.path.dirname(audio_path))
                    print("Deleted temporary audio")

            else:
                transcript_status = "audio_download_failed"

        results.append({
            "url": url,
            "status": "success",
            "text_file": filepath,
            "character_count": len(text),
            "transcript_status": transcript_status
        })


    pd.DataFrame(results).to_csv(os.path.join(OUTPUT_DIR, "summary.csv"), index=False)
    print("Done. Check the output folder.")


if __name__ == "__main__":
    main()