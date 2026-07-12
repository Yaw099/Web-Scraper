import os
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
from config.settings import ANTHROPIC_MODEL, ANTHROPIC_MAX_TOKENS, ANALYSIS_OUTPUT_DIR

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def build_analysis_prompt(text: str, source_name: str) -> str:
    return f"""
You are analyzing regulatory meeting/page content for a client.

Source file:
{source_name}

Analyze the content and return a clear, structured report with these sections:

1. Executive Summary
2. Key Topics
3. Decisions or Actions
4. Important Dates
5. Organizations and People Mentioned
6. Links or References
7. Suggested Tags
8. Items That May Need Follow-Up

Content:
{text}
""".strip()


def analyze_text(text: str, source_name: str = "unknown") -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Missing ANTHROPIC_API_KEY. Set it before running Claude analysis."
        )

    client = Anthropic(api_key=api_key)

    prompt = build_analysis_prompt(text, source_name)

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=ANTHROPIC_MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.content[0].text


def analyze_text_file(filepath: str, output_dir: str = ANALYSIS_OUTPUT_DIR) -> str:
    os.makedirs(output_dir, exist_ok=True)

    path = Path(filepath)

    with open(path, "r", encoding="utf-8") as file:
        text = file.read()

    analysis = analyze_text(text, source_name=path.name)

    output_path = Path(output_dir) / f"{path.stem}_analysis.md"

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(analysis)

    return str(output_path)

