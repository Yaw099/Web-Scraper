from faster_whisper import WhisperModel

from settings import (
    TRANSCRIPTION_COMPUTE_TYPE,
    TRANSCRIPTION_DEVICE,
    TRANSCRIPTION_MODEL,
)


def transcribe(audio_path: str) -> str:
    model = WhisperModel(
        TRANSCRIPTION_MODEL,
        device=TRANSCRIPTION_DEVICE,
        compute_type=TRANSCRIPTION_COMPUTE_TYPE,
    )

    segments, _info = model.transcribe(audio_path)

    lines: list[str] = []
    for segment in segments:
        lines.append(f"[{segment.start:.2f} - {segment.end:.2f}] {segment.text.strip()}")

    return "\n".join(lines)
