# Regulatory Web Scraper

Desktop tool for scraping regulatory webpages, discovering PUCT AdminMonitor meeting links, downloading/transcribing selected meeting audio, and generating AI-assisted analysis reports.

## Features

- Load URLs from `urls.csv`
- Scrape readable webpage text into `output/`
- Discover AdminMonitor meeting URLs from PUCT calendar pages
- Save discovered meetings to `output/discovered_meetings.csv`
- Transcribe selected AdminMonitor meeting videos into `transcripts/`
- Estimate AI analysis usage before sending text to Claude
- Generate AI analysis reports into `analysis/`

## System Requirements

* Windows 10 or Windows 11
* Python 3.10+
* Internet connection
* Anthropic API key (for AI analysis)

## Installation

### 1. Install Python

Download and install Python from:
https://www.python.org/downloads/

Verify installation:

```bash
py --version
```

### 2. Install Project Dependencies

Open a terminal in the project folder and run:

```bash
py -m pip install -r requirements.txt
```

### 3. Install Playwright Browsers

```bash
playwright install

or

py -m playwright install
```

### 4. Configure Claude API Access

Create a file named `.env` in the project root:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

### 5. Launch the Application

```bash
py gui.py
```

The Regulatory Web Scraper window should appear.


## Setup

Install dependencies:

```bash
py -m pip install -r requirements.txt
playwright install
```
## Recommended Workflow

1. Click Run Pipeline to scrape pages and discover meeting links.
2. Click Open Discovered Meetings CSV to review found meetings.
3. Click Transcribe Meeting URL and select a discovered meeting.
4. Click Open Transcripts Folder to review the transcript.
5. Click Estimate Claude Usage before running AI analysis.
6. Click Analyze Scraped Text File or Analyze Transcripts Folder.
7. Click Open Analysis Folder to review generated reports.