from src.analyze import transcribe
from src.fetch import cleanup_temp_file, download_audio_temp
from config.settings import TRANSCRIPT_OUTPUT_DIR
from src.storage import save_text


def transcribe_meeting_url(url: str) -> str:
    audio_path = download_audio_temp(url)

    if not audio_path:
        raise RuntimeError("Audio download failed.")

    try:
        transcript = transcribe(audio_path)
        transcript_file = save_text(transcript, url, TRANSCRIPT_OUTPUT_DIR)
        return transcript_file
    finally:
        cleanup_temp_file(audio_path)