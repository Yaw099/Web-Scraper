import sys

from analyze import transcribe
from analysis_service import analyze_large_text
from clean import extract_structured_content
from fetch import cleanup_temp_file, download_audio_temp, fetch_html, is_video_page
from reports import load_urls, save_summary, save_discovered_meetings, save_document_summary
from documents import discover_document_links, download_documents_from_links
from settings import (
    DOWNLOAD_AUDIO,
    INPUT_FILE,
    MAX_URLS,
    OUTPUT_DIR,
    SUMMARY_FILENAME,
    TEST_MODE,
    TRANSCRIPT_OUTPUT_DIR,
    DOCUMENT_OUTPUT_DIR,
    DOCUMENT_TEXT_OUTPUT_DIR,
    DOCUMENT_ANALYSIS_OUTPUT_DIR,    
)
from storage import ensure_directories, save_text
from discovery import discover_meeting_urls

def process_url(url: str, download_audio: bool) -> dict:
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
            "analysis_status": "",
            "analysis_file": "",
            "analysis_character_count": 0,
            "chunks_used": 0,
            "discovered_meetings": "",
        }, [], []
    
    print(f"Downloaded {len(html):,} characters")

    discovered_meetings = discover_meeting_urls(html, url)
    
    discovered_rows = []
    for meeting_url in discovered_meetings:
        print(f"Discovered meeting: {meeting_url}")

        discovered_rows.append({
        "source_url": url,
        "meeting_url": meeting_url,
        "status": "discovered",
        "transcript_file": "",
    })


    text = extract_structured_content(html, url)

    document_links = discover_document_links(html, url)

    document_results = download_documents_from_links(
        links=document_links,
        output_folder=DOCUMENT_OUTPUT_DIR
    )

    document_rows = []

    for doc in document_results:
        document_rows.append({
            "source_url": url,
            "document_url": doc["url"],
            "local_path": doc.get("local_path", ""),
            "normalized_path": "",
            "document_text_file": "",
            "document_analysis_file": "",
            "file_type": doc.get("file_type", ""),
            "success": doc.get("success", False),
            "error": doc.get("error", ""),
            "analysis_status": "not_analyzed",
            "character_count": 0,
        })

        if doc["success"]:
            print(f"Document downloaded: {doc['url']}")
        else:
            print(f"Document download failed: {doc['url']} - {doc['error']}")

    text_file = save_text(text, url, OUTPUT_DIR)

    transcript_status = ""
    transcript_file = ""

    if download_audio and is_video_page(url):
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
        "analysis_status": "",
        "analysis_file": "",
        "analysis_character_count": 0,
        "chunks_used": 0,
    }, discovered_rows, document_rows


def main(input_file="urls.csv", test_mode=True, download_audio=True) -> None:
    print("Python executable:")
    print(sys.executable)
    print()

    ensure_directories(OUTPUT_DIR, TRANSCRIPT_OUTPUT_DIR, DOCUMENT_OUTPUT_DIR, DOCUMENT_TEXT_OUTPUT_DIR, DOCUMENT_ANALYSIS_OUTPUT_DIR,)

    urls = load_urls(input_file, test_mode=test_mode, max_urls=MAX_URLS)

    results = []
    all_discovered_meetings = []
    all_document_rows = []

    for _, row in urls.iterrows():
        result, discovered_rows, document_rows = process_url(row["url"], download_audio)
        results.append(result)
        all_discovered_meetings.extend(discovered_rows)
        all_document_rows.extend(document_rows)

    summary_file = save_summary(results, OUTPUT_DIR, SUMMARY_FILENAME)
    discovered_file = save_discovered_meetings(all_discovered_meetings, OUTPUT_DIR)
    document_file = save_document_summary(all_document_rows, OUTPUT_DIR)

    print(f"Document summary saved to {document_file}")
    print(f"Done. Summary saved to {summary_file}")
    print(f"Discovered meetings saved to {discovered_file}")

if __name__ == "__main__":
    main()
