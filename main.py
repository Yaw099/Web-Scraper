import sys
import traceback
from src.analyze import transcribe
from src.clean import extract_structured_content
from src.fetch import cleanup_temp_file, download_audio_temp, fetch_html, is_video_page
from src.reports import load_urls, save_summary, save_discovered_meetings, save_document_summary
from src.documents import (
    discover_document_links,
    download_documents_from_links,
    is_downloadable_url,
    normalize_url_for_dedup,
)
from config.settings import (
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
from src.storage import ensure_directories, save_text
from src.discovery import discover_meeting_urls

def process_direct_document(url: str) -> tuple[dict, list[dict], list[dict]]:
    """Download a document URL supplied directly in urls.csv.

    Direct document URLs do not have a webpage to scrape, so they bypass
    Playwright and are added straight to the normal document-download results.
    """
    print(f"Processing direct document: {url}")

    document_results = download_documents_from_links(
        links=[url],
        output_folder=DOCUMENT_OUTPUT_DIR,
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

    document_downloaded = bool(document_results and document_results[0]["success"])

    return {
        "url": url,
        "status": "success" if document_downloaded else "failed",
        "text_file": "",
        "character_count": 0,
        "transcript_status": "",
        "transcript_file": "",
        "analysis_status": "",
        "analysis_file": "",
        "analysis_character_count": 0,
        "chunks_used": 0,
    }, [], document_rows


def process_url(url: str, download_audio: bool,) -> tuple[dict, list[dict], list[dict]]:
    print(f"Processing: {url}")

    if is_downloadable_url(url):
        return process_direct_document(url)

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
            "archive_path": doc.get("archive_path", ""),
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


def main(
    input_file=INPUT_FILE,
    test_mode=TEST_MODE,
    download_audio=DOWNLOAD_AUDIO,
) -> None:
    print("Python executable:")
    print(sys.executable)
    print()

    ensure_directories(
        OUTPUT_DIR,
        TRANSCRIPT_OUTPUT_DIR,
        DOCUMENT_OUTPUT_DIR,
        DOCUMENT_TEXT_OUTPUT_DIR,
        DOCUMENT_ANALYSIS_OUTPUT_DIR,
    )

    urls = load_urls(input_file, test_mode=test_mode, max_urls=MAX_URLS)

    results = []
    all_discovered_meetings = []
    all_document_rows = []
    seen_input_urls = set()

    for _, row in urls.iterrows():
        url_value = row["url"]

        if not isinstance(url_value, str):
            print("Skipping blank or invalid URL.")
            continue

        url = (
            url_value.strip()
            .strip('"')
            .strip("'")
        )

        if not url:
            print("Skipping blank or invalid URL.")
            continue

        url_key = normalize_url_for_dedup(url)

        if url_key in seen_input_urls:
            print(f"Skipping duplicate input URL: {url}")
            continue

        seen_input_urls.add(url_key)

        try:
            pipeline_result, discovered_rows, document_rows = process_url(
                url,
                download_audio,
            )

            results.append(pipeline_result)
            all_discovered_meetings.extend(discovered_rows)
            all_document_rows.extend(document_rows)

        except Exception as error:
            print(f"ERROR processing {url}: {error}")
            traceback.print_exc()

            results.append({
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
            })

    summary_file = save_summary(results, OUTPUT_DIR, SUMMARY_FILENAME)
    discovered_file = save_discovered_meetings(all_discovered_meetings, OUTPUT_DIR)
    document_file = save_document_summary(all_document_rows, OUTPUT_DIR)

    print(f"Document summary saved to {document_file}")
    print(f"Done. Summary saved to {summary_file}")
    print(f"Discovered meetings saved to {discovered_file}")

if __name__ == "__main__":
    main()


# https://www.ercot.com/committees/ros/dwg
# https://www.puc.texas.gov/agency/calendar/openmeetings/
# https://www.ercot.com/committees/rms/tdtms
# https://www.ercot.com/committees/prs
# https://www.ercot.com/committees/tac/llwg
# https://www.ercot.com/mktrules/issues/PGRR145
# https://www.ercot.com/mktrules/issues/NPRR1325
# https://www.adminmonitor.com/tx/puct/open_meeting/20260326/
# https://www.adminmonitor.com/tx/puct/open_meeting/20260402/


# https://spp.org/news-list/southwest-power-pool-board-approves-accelerated-pathway-for-large-load-connection/
# https://spp.org/Documents/74204/RR696.zip
# https://spp.org/Documents/74189/large%20load%20stakeholder%20engagement%20forum%20meeting%20materials%2020250701.zip
# https://spp.org/markets-operations/high-impact-large-load-hill-integration/
# https://spp.org/Documents/75365/one%20pager%20-%20high%20impact%20large%20load%20process.docx
# https://spp.org/Documents/75366/One%20Pager%20-%20SPP%20High%20Impact%20Large%20Load%20Generator%20Assessment.docx
# https://spp.org/spp-documents-filings/?id=540504https://spp.org/spp-documents-filings/?id=540504
# https://spp.org/spp-documents-filings/?id=540500
# https://spp.org/spp-documents-filings/?id=540506
# "https://spp.org/Documents/75698/20260112%20CHILLS%20and%20PALS%20Stakeholder%20Engagement%20Forum,%20Presentation.pptx"
# "https://spp.org/Documents/75348/20251121%20CHILLS%20Stakeholder%20Engagement%20Forum,%20Presentation.pptx"
