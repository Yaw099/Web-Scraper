from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).resolve().parent.parent

# Input
INPUT_FILE = ROOT_DIR / "urls.csv"

# Output folders
OUTPUT_DIR = ROOT_DIR / "output"
TRANSCRIPT_OUTPUT_DIR = ROOT_DIR / "transcripts"
ANALYSIS_OUTPUT_DIR = ROOT_DIR / "analysis"

# Pipeline
SUMMARY_FILENAME = "summary.csv"

# Runtime options
TEST_MODE = True
MAX_URLS = 1
DOWNLOAD_AUDIO = True

# Claude
DEFAULT_CHUNK_SIZE = 12000
ANTHROPIC_MODEL = "claude-sonnet-4-5"
ANTHROPIC_MAX_TOKENS = 2000

# Whisper
TRANSCRIPTION_MODEL = "tiny"
TRANSCRIPTION_DEVICE = "cpu"
TRANSCRIPTION_COMPUTE_TYPE = "int8"

# Documents
DOCUMENT_OUTPUT_DIR = OUTPUT_DIR / "documents"
DOCUMENT_TEXT_OUTPUT_DIR = OUTPUT_DIR / "document_text"
DOCUMENT_ANALYSIS_OUTPUT_DIR = OUTPUT_DIR / "document_analysis"