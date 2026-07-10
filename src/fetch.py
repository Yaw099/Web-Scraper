import os
import shutil
import subprocess
import sys
import tempfile

from playwright.sync_api import sync_playwright


def fetch_html(url: str) -> str | None:
    browser = None

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(ignore_https_errors=True)
            page.goto(url, wait_until="networkidle", timeout=60000)
            return page.content()

    except Exception as error:
        print(f"Failed to fetch {url}: {error}")
        return None

    finally:
        if browser:
            browser.close()


def is_video_page(url: str) -> bool:
    return "adminmonitor.com/tx/puct/open_meeting/" in url.lower()


def download_audio_temp(url: str) -> str | None:
    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--playlist-items",
        "1",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "5",
        "--output",
        output_template,
        url,
    ]

    try:
        subprocess.run(command, check=True)

        for filename in os.listdir(temp_dir):
            if filename.endswith((".mp3", ".m4a", ".wav")):
                return os.path.join(temp_dir, filename)

        shutil.rmtree(temp_dir, ignore_errors=True)
        return None

    except subprocess.CalledProcessError as error:
        print(f"Audio download failed: {error}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None


def cleanup_temp_file(filepath: str | None) -> None:
    if not filepath:
        return

    shutil.rmtree(os.path.dirname(filepath), ignore_errors=True)
