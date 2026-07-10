# Regulatory Web Scraper

The Regulatory Web Scraper is a Windows desktop application for collecting information from regulatory websites. It can:

* Scrape webpages into clean, readable text.
* Discover AdminMonitor meeting links.
* Download regulatory documents.
* Extract text from common document formats.
* Download and transcribe meeting audio.
* Generate AI-assisted summaries and analysis using Claude.

This guide is written for Windows users with little or no programming experience.

---

# System Requirements

* Windows 10 or Windows 11
* Internet connection
* Python 3.10+ (tested with Python 3.13 and 3.14)
* LibreOffice (for legacy Microsoft Office document conversion)
* FFmpeg (for meeting audio conversion)
* Anthropic API key (only required for AI analysis)

---

# Step 1 – Install Python

Download Python from:

https://www.python.org/downloads/

During installation, make sure **Add Python to PATH** is checked.

After installation, open **PowerShell** and verify Python:

```powershell
py --version
```

You should see something similar to:

```
Python 3.13.x
```

---

# Step 2 – Install LibreOffice

LibreOffice allows the application to automatically convert older Microsoft Office documents such as:

* .doc → .docx
* .xls → .xlsx
* .ppt → .pptx

## Option A – Download from the Website (Recommended)

Download the latest Windows installer from:

https://www.libreoffice.org/download/download-libreoffice/

Run the installer using the default options.

---

## Option B – Install with PowerShell

```powershell
winget install TheDocumentFoundation.LibreOffice
```

After installation, verify it works:

```powershell
& "C:\Program Files\LibreOffice\program\soffice.exe" --version
```

You should see the LibreOffice version number.

---

# Step 3 – Install FFmpeg

FFmpeg is used to convert downloaded meeting videos into audio before transcription.

## Option A – Download from the Website (Recommended)

Go to:

https://ffmpeg.org/download.html

Choose the Windows build (Gyan.dev is recommended).

Download the **Essentials Build**.

Extract it to a permanent location such as:

```
C:\ffmpeg
```

Add the following folder to your Windows PATH:

```
C:\ffmpeg\bin
```

Restart PowerShell after adding it.

---

## Option B – Install with PowerShell

```powershell
winget install Gyan.FFmpeg
```

Verify the installation:

```powershell
ffmpeg -version
```

You should see version information.

---

# Step 4 – Download the Project

Download or clone the project into a folder of your choice.

Open **PowerShell** inside the project folder.

---

# Step 5 – Install Python Dependencies

Run:

```powershell
py -m pip install -r requirements.txt
```

---

# Step 6 – Install Playwright Browsers

Run:

```powershell
py -m playwright install
```

This only needs to be done once.

---

# Step 7 – Configure Claude

If you plan to use AI analysis, create a file named:

```
.env
```

inside the project folder.

Its contents should be:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your Anthropic API key.

If you only want scraping and transcription, this step can be skipped.

---

# Step 8 – Verify Installation

Run these commands:

```powershell
py --version
```

```powershell
ffmpeg -version
```

```powershell
py -m playwright --help
```

```powershell
& "C:\Program Files\LibreOffice\program\soffice.exe" --version
```

If all three commands succeed, your installation is complete.

---

# Starting the Application

From the project folder, run:

```powershell
py -m gui.gui
```

The Regulatory Web Scraper window should appear.

---

# Typical Workflow

## 1. Run the Pipeline

Click **Run Pipeline**.

The application will:

* Scrape each webpage.
* Save webpage text.
* Discover meeting links.
* Download linked documents.

---

## 2. Extract Document Text

Click:

**Extract Document Text**

Supported document types include:

* PDF
* DOC
* DOCX
* PPT
* PPTX
* XLS
* XLSX
* CSV
* TXT
* RTF

Legacy Microsoft Office files are automatically converted before extraction.

---

## 3. Transcribe Meetings

Click:

**Transcribe Meeting URL**

or

**Transcribe All Discovered Meetings**

Meeting audio will be downloaded, converted, and transcribed.

---

## 4. Estimate Claude Usage

Before sending large files to Claude, click:

**Estimate Claude Usage**

This estimates the number of analysis chunks without using your API credits.

---

## 5. Analyze Text

You can analyze:

* Individual scraped files
* Entire scraped folders
* Document text
* Meeting transcripts

Analysis reports are saved automatically.

---

# Output Folders

The application creates several folders:

```
output/
```

Scraped webpages and downloaded documents.

```
output/document_text/
```

Extracted document text.

```
output/document_analysis/
```

AI analysis of extracted documents.

```
transcripts/
```

Meeting transcripts.

```
analysis/
```

AI analysis of webpages and transcripts.

---

# Troubleshooting

## "ffmpeg not found"

FFmpeg is either not installed or is not on your Windows PATH.

Verify:

```powershell
ffmpeg -version
```

---

## "LibreOffice is required to convert this file"

Install LibreOffice and try again.

Verify:

```powershell
& "C:\Program Files\LibreOffice\program\soffice.exe" --version
```

---

## "Could not find a version that satisfies the requirement..."

Upgrade pip:

```powershell
py -m pip install --upgrade pip
```

Then reinstall the project dependencies:

```powershell
py -m pip install -r requirements.txt
```

---

## Playwright Errors

Reinstall the browser components:

```powershell
py -m playwright install
```

---

## Claude Analysis Doesn't Work

Check that:

* `.env` exists in the project folder.
* `ANTHROPIC_API_KEY` is entered correctly.
* You have an active internet connection.

---

# Need Help?

Run these commands:
```
py --version
py -m pip list
ffmpeg -version
py -m playwright --help
& "C:\Program Files\LibreOffice\program\soffice.exe" --version
```
Then include:

- the full error message,
- what button you clicked,
- and, if applicable, the URL being processed.


If an error occurs, copy the complete error message from the application's log window before requesting support. Including the full message makes troubleshooting much faster.
