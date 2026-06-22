import sys

from analyze import transcribe
from clean import extract_structured_content
from fetch import cleanup_temp_file, download_audio_temp, fetch_html, is_video_page
from reports import load_urls, save_summary
from settings import (
    DOWNLOAD_AUDIO,
    INPUT_FILE,
    MAX_URLS,
    OUTPUT_DIR,
    SUMMARY_FILENAME,
    TEST_MODE,
    TRANSCRIPT_OUTPUT_DIR,
)
from storage import ensure_directories, save_text


def process_url(url: str) -> dict:
    print(f"Processing: {url}")

    html = fetch_html(url)

    if not html:
        return {
            "url": url,
            "status": "failed",
            "text_file": "",
            "character_count": 0,
            "transcript_status": "",
            "transcript_file": "",
        }

    print(f"Downloaded {len(html):,} characters")

    text = extract_structured_content(html, url)
    text_file = save_text(text, url, OUTPUT_DIR)

    transcript_status = ""
    transcript_file = ""

    if DOWNLOAD_AUDIO and is_video_page(url):
        audio_path = download_audio_temp(url)

        if audio_path:
            try:
                print(f"Downloaded audio to {audio_path}")
                transcript = transcribe(audio_path)
                transcript_file = save_text(transcript, url, TRANSCRIPT_OUTPUT_DIR)
                transcript_status = "transcribed"
            except Exception as error:
                print(f"Transcription failed: {error}")
                transcript_status = "transcription_failed"
            finally:
                cleanup_temp_file(audio_path)
                print("Deleted temporary audio")
        else:
            transcript_status = "audio_download_failed"

    return {
        "url": url,
        "status": "success",
        "text_file": text_file,
        "character_count": len(text),
        "transcript_status": transcript_status,
        "transcript_file": transcript_file,
    }


def main() -> None:
    print("Python executable:")
    print(sys.executable)
    print()

    ensure_directories(OUTPUT_DIR, TRANSCRIPT_OUTPUT_DIR)

    urls = load_urls(INPUT_FILE, test_mode=TEST_MODE, max_urls=MAX_URLS)

    results = []
    for _, row in urls.iterrows():
        results.append(process_url(row["url"]))

    summary_file = save_summary(results, OUTPUT_DIR, SUMMARY_FILENAME)
    print(f"Done. Summary saved to {summary_file}")


if __name__ == "__main__":
    main()
