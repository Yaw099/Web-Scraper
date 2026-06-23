# Web-Scraper

URL list
-  → fetch page HTML
-  → extract readable text
-  → chunk long pages
-  → send chunks to Claude/OpenAI
-  → return structured JSON
-  → save to SQLite
-  → generate summary/report/search index



# Regulatory Web Scraper

Desktop tool for collecting regulatory webpage content, downloading/transcribing meeting audio, and generating Claude-based analysis reports.

## Setup

Install dependencies:

```bash
py -m pip install -r requirements.txt
playwright install