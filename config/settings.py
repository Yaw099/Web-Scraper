from pathlib import Path

# Input
INPUT_FILE = "urls.csv"

# Output folders
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
TRANSCRIPT_OUTPUT_DIR = "transcripts"
ANALYSIS_OUTPUT_DIR = "analysis"

#Pipeline
SUMMARY_FILENAME = "summary.csv"

# Claude
TEST_MODE = True
MAX_URLS = 1
DOWNLOAD_AUDIO = True

DEFAULT_CHUNK_SIZE = 12000

ANTHROPIC_MODEL = "claude-sonnet-4-5"
ANTHROPIC_MAX_TOKENS = 2000

# Whisper
TRANSCRIPTION_MODEL = "tiny"
TRANSCRIPTION_DEVICE = "cpu"
TRANSCRIPTION_COMPUTE_TYPE = "int8"

# Documents
DOCUMENT_OUTPUT_DIR = "output/documents"
DOCUMENT_TEXT_OUTPUT_DIR = "output/document_text"
DOCUMENT_ANALYSIS_OUTPUT_DIR = "output/document_analysis"