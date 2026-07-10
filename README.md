# Regulatory Web Scraper

A Windows desktop tool for collecting and analyzing regulatory meeting materials.

The app can scrape regulatory webpages, discover PUCT/AdminMonitor meeting links, download meeting documents, extract document text, transcribe meeting audio, and create AI-assisted analysis reports.

## What This Tool Does

- Loads webpage URLs from `urls.csv`
- Scrapes readable webpage text into `output/`
- Finds AdminMonitor meeting links on PUCT calendar pages
- Saves discovered meetings to `output/discovered_meetings.csv`
- Downloads linked documents into `output/documents/`
- Extracts text from supported document files into `output/document_text/`
- Transcribes selected or bulk AdminMonitor meeting videos into `transcripts/`
- Estimates Claude usage before sending text for AI analysis
- Creates AI analysis reports in `analysis/` or `output/document_analysis/`

## Supported Document Types

The tool can currently work with these document types:

- PDF: `.pdf`
- Word: `.docx`
- Legacy Word: `.doc`, converted to `.docx` with LibreOffice
- PowerPoint `.pptx`
- Legacy PowerPoint `.ppt`, converted to `.pptx` with LibreOffice
- Excel: `.xlsx`
- Legacy Excel: `.xls`, converted to `.xlsx` with LibreOffice
- CSV: `.csv`
- Text: `.txt`
- Rich text: `.rtf`, if supported by the extraction path

PDF support is for normal text-based PDFs. Scanned PDFs may produce little or no text until OCR support is added later.

## System Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- Internet connection
- Anthropic API key for Claude analysis
- LibreOffice, needed for older `.doc`, `.ppt` and `.xls` files
- FFmpeg, needed for meeting audio/transcription support

## Important Folder Terms

The **project folder** means the folder that contains files such as:

- `main.py`
- `gui.py`
- `requirements.txt`
- `urls.csv`

Run all PowerShell commands from that folder unless the instructions say otherwise.

## First-Time Setup

### 1. Install Python

Download Python from the official Python website:

<https://www.python.org/downloads/>

During installation, check the box that says:

```text
Add python.exe to PATH
```

After installing, open PowerShell and run:

```powershell
py --version
```

You should see a Python version number.

### 2. Open PowerShell in the Project Folder

In File Explorer, open the project folder.

Then click the address bar, type:

```text
powershell
```

and press Enter.

PowerShell should open directly inside the project folder.


### 3. Install Python Dependencies

With the virtual environment activated, run:

```powershell
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

### 4. Install Playwright Browsers

Run:

```powershell
py -m playwright install
```

This allows the scraper to load pages that require a browser-like fetch.

### 5. Install LibreOffice

LibreOffice is needed when the app encounters older Office files such as `.doc`, `.ppt` or `.xls`.

Download LibreOffice from:

<https://www.libreoffice.org/download/download-libreoffice/>

The app checks common Windows install locations automatically.

### 6. Install FFmpeg

FFmpeg is recommended for meeting audio downloads and transcription workflows.

The easiest Windows option is usually to install it with winget:

```powershell
winget install Gyan.FFmpeg
```

After installing, close and reopen PowerShell, then check:

```powershell
ffmpeg -version
```

If PowerShell prints version information, FFmpeg is installed correctly.

### 7. Create the `.env` File

Create a file named `.env` in the project folder.

Add this line inside it:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with the real Anthropic API key.

Do not include quotes unless the key specifically requires them.

## Starting the App

Then start the app:

The Regulatory Web Scraper window should open.

```powershell
py -m gui.gui
```

## Preparing `urls.csv`

The app expects a CSV file containing a column named:

```text
url
```

Example:

```csv
url
https://www.puc.texas.gov/agency/calendar/openmeetings/
https://www.adminmonitor.com/tx/puct/open_meeting/20260402/
```

The default file is usually named `urls.csv` and placed in the project folder.

You can also select a different CSV file from the app using the **Browse** button.

## Recommended Workflow

### 1. Run the Pipeline

Click:

```text
Run Pipeline
```

This scrapes the URLs, discovers meeting links, and downloads linked documents.

Main outputs:

- Scraped webpage text: `output/`
- Discovered meetings CSV: `output/discovered_meetings.csv`
- Downloaded documents: `output/documents/`

### 2. Review Discovered Meetings

Click:

```text
Open Discovered Meetings CSV
```

This opens the list of meeting URLs found by the pipeline.

### 3. Extract Document Text

Click:

```text
Extract Document Text
```

This reads documents from:

```text
output/documents/
```

and saves extracted text into:

```text
output/document_text/
```

### 4. Analyze Document Text

Click:

```text
Analyze Document Text Folder
```

This sends extracted document text to Claude and saves analysis results into:

```text
output/document_analysis/
```

### 5. Transcribe Meetings

For one meeting, click:

```text
Transcribe Meeting URL
```

For all discovered meetings, click:

```text
Transcribe All Discovered Meetings
```

Transcripts are saved into:

```text
transcripts/
```

Meeting transcription may take a long time and may download large temporary audio files.

### 6. Analyze Scraped Text or Transcripts

Use one of these buttons:

```text
Analyze Scraped Text File
Analyze Scraped Text Folder
Analyze Transcripts Folder
```

Analysis reports are saved into:

```text
analysis/
```

## Test Mode

Test Mode limits how much the app processes.

Use Test Mode when checking that the app works or testing a small change.

Turn Test Mode off when you want the app to process the full CSV.

## Output Folders

The app creates and uses these folders:

```text
output/
output/documents/
output/document_text/
output/document_analysis/
transcripts/
analysis/
```

If a folder does not exist, the app usually creates it automatically.

## Common PowerShell Commands


Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

Install a new dependency:

```powershell
py -m pip install package-name
```

Run the GUI:

```powershell
py -m gui.gui
```

Run the command-line pipeline directly:

```powershell
py main.py
```

Check Python version:

```powershell
py --version
```

Check FFmpeg:

```powershell
ffmpeg -version
```

## Troubleshooting


### `py` is not recognized

Python may not be installed correctly, or it may not have been added to PATH.

Reinstall Python and make sure this option is checked:

```text
Add python.exe to PATH
```

### `playwright` errors occur

Run:

```powershell
py -m playwright install
```

### `.doc`, `.ppt`,  or `.xls` files fail

Install LibreOffice, then rerun the extraction.

The app uses LibreOffice to convert old Office files:

```text
.doc  -> .docx
.ppt  -> .pptx
.xls  -> .xlsx
```

### PDFs extract little or no text

The PDF may be scanned instead of text-based.

Text-based PDFs should extract normally. Scanned PDFs need OCR support, which is not currently enabled.

### Transcription fails after the computer sleeps

Meeting transcription and audio conversion can fail if the computer goes to sleep during processing.

Before running long transcription jobs, plug in the laptop and temporarily disable sleep.

### Missing API key

Make sure the `.env` file exists in the project folder and contains:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

Then restart the app.

## Notes for Non-Technical Users

- Keep the project folder in one location. Do not move individual files around.
- Start the app from PowerShell using `py -m gui.gui`.
- Use the buttons in order when possible: run pipeline, extract document text, then analyze.
- Large meetings and large document folders may take time.
- Do not close the app or let the computer sleep while transcription or analysis is running.
- If something fails, check the log box at the bottom of the app first.
