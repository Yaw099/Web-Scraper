import os
import re
import subprocess
import threading
import tkinter as tk
import pandas as pd
from hashlib import sha256
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from urllib.parse import urlparse

from src.analysis_service import (
    analyze_large_text,
    analyze_source_collection,
    analyze_source_bundle,
    estimate_analysis,
)
from main import main
from config.settings import (
    ANALYSIS_OUTPUT_DIR,
    DEFAULT_CHUNK_SIZE,
    INPUT_FILE,
    OUTPUT_DIR,
    SUMMARY_FILENAME,
)
from src.meeting_transcription import transcribe_meeting_url
from src.reports import update_link_analysis_result

class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Regulatory Web Scraper")
        self.root.geometry("1050x700")
        self.root.minsize(750, 550)

        self.csv_path = tk.StringVar(value=INPUT_FILE)
        self.status_text = tk.StringVar(value="Status: Ready")
        self.chunk_size = tk.StringVar(value=str(DEFAULT_CHUNK_SIZE))
        self.test_mode = tk.BooleanVar(value=True)
        self.download_audio = tk.BooleanVar(value=True)
        self.enable_web_search = tk.BooleanVar(value=False)
        self.max_web_searches = tk.StringVar(value="5")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.main_frame.columnconfigure(0, weight=1)

        self.build_ui()

    def build_ui(self):
        title = ttk.Label(
            self.main_frame,
            text="Regulatory Web Scraper",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(pady=10)

        status_label = ttk.Label(
            self.main_frame,
            textvariable=self.status_text,
            font=("Segoe UI", 10),
        )
        status_label.pack(pady=(0, 10))

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, pady=(0, 10))

        collection_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(collection_tab, text="Collection")

        documents_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(documents_tab, text="Documents")

        meetings_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(meetings_tab, text="Meetings")

        analysis_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(analysis_tab, text="Analysis")

        log_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_tab, text="Log")

        input_frame = ttk.LabelFrame(collection_tab, text="Input")
        input_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(input_frame, text="URLs CSV").grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        ttk.Entry(
            input_frame,
            textvariable=self.csv_path,
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="ew",
        )

        ttk.Button(
            input_frame,
            text="Browse",
            command=self.select_csv,
        ).grid(
            row=0,
            column=2,
            padx=5,
            pady=5,
        )

        input_frame.columnconfigure(1, weight=1)

        options_frame = ttk.LabelFrame(collection_tab, text="Options")
        options_frame.pack(fill="x", pady=5)

        ttk.Checkbutton(
            options_frame,
            text="Test Mode",
            variable=self.test_mode,
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")

        ttk.Checkbutton(
            options_frame,
            text="Download Meeting Audio & Transcribe",
            variable=self.download_audio,
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")

        ttk.Label(
            options_frame,
            text="Claude chunk size",
        ).grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Entry(
            options_frame,
            textvariable=self.chunk_size,
            width=12,
        ).grid(row=0, column=2, padx=5, pady=5, sticky="w")

        pipeline_frame = ttk.LabelFrame(collection_tab, text="Pipeline")
        pipeline_frame.pack(fill="x", pady=5)

        for column in range(1):
            pipeline_frame.columnconfigure(column, weight=1)

        ttk.Button(
            pipeline_frame,
            text="Run Pipeline",
            command=self.start_pipeline,
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        meeting_processing_frame = ttk.LabelFrame(
            meetings_tab,
            text="Transcription",
        )
        meeting_processing_frame.pack(fill="x", pady=5)

        for column in range(2):
            meeting_processing_frame.columnconfigure(column, weight=1)

        ttk.Button(
            meeting_processing_frame,
            text="Transcribe Meeting URL",
            command=self.prompt_transcribe_meeting_url,
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ttk.Button(
            meeting_processing_frame,
            text="Transcribe All Discovered Meetings",
            command=self.confirm_bulk_transcribe_meetings,
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        meeting_files_frame = ttk.LabelFrame(
            meetings_tab,
            text="Meeting Files",
        )
        meeting_files_frame.pack(fill="x", pady=5)

        for column in range(2):
            meeting_files_frame.columnconfigure(column, weight=1)

        ttk.Button(
            meeting_files_frame,
            text="Open Discovered Meetings CSV",
            command=lambda: self.open_file("output/discovered_meetings.csv"),
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ttk.Button(
            meeting_files_frame,
            text="Open Transcripts Folder",
            command=lambda: self.open_folder("transcripts"),
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        link_analysis_frame = ttk.LabelFrame(
            analysis_tab,
            text="Link Analysis",
        )
        link_analysis_frame.pack(fill="both", expand=False, pady=5)
        link_analysis_frame.columnconfigure(0, weight=1)
        link_analysis_frame.columnconfigure(1, weight=1)

        ttk.Label(
            link_analysis_frame,
            text=(
                "Additional Research Instructions (optional):"
            ),
        ).grid(row=0, column=0, padx=5, pady=(5, 0), sticky="w")

        self.research_instructions_box = ScrolledText(
            link_analysis_frame,
            height=7,
            wrap="word",
        )
        self.research_instructions_box.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=5,
            pady=5,
            sticky="ew",
        )

        ttk.Checkbutton(
            link_analysis_frame,
            text="Search the web for additional sources",
            variable=self.enable_web_search,
        ).grid(row=2, column=0, padx=5, pady=(0, 5), sticky="w")

        web_search_limit_frame = ttk.Frame(link_analysis_frame)
        web_search_limit_frame.grid(
            row=2,
            column=1,
            padx=5,
            pady=(0, 5),
            sticky="e",
        )

        ttk.Label(
            web_search_limit_frame,
            text="Maximum web searches:",
        ).pack(side="left", padx=(0, 5))

        ttk.Spinbox(
            web_search_limit_frame,
            from_=1,
            to=20,
            textvariable=self.max_web_searches,
            width=5,
        ).pack(side="left")

        ttk.Button(
            link_analysis_frame,
            text="Analyze Selected URLs",
            command=self.prompt_analyze_link,
        ).grid(row=3, column=0, padx=5, pady=(0, 5), sticky="ew")

        ttk.Button(
            link_analysis_frame,
            text="Analyze All URLs",
            command=self.prompt_analyze_all_links,
        ).grid(row=3, column=1, padx=5, pady=(0, 5), sticky="ew")

        analysis_frame = ttk.LabelFrame(analysis_tab, text="File Analysis")
        analysis_frame.pack(fill="x", pady=5)

        for column in range(2):
            analysis_frame.columnconfigure(column, weight=1)

        ttk.Button(
            analysis_frame,
            text="Estimate Claude Usage",
            command=self.estimate_existing_file,
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ttk.Button(
            analysis_frame,
            text="Analyze Scraped Text File",
            command=self.analyze_existing_file,
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Button(
            analysis_frame,
            text="Analyze Scraped Text Folder",
            command=lambda: self.analyze_folder("output"),
        ).grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        ttk.Button(
            analysis_frame,
            text="Analyze Transcripts Folder",
            command=lambda: self.analyze_folder("transcripts"),
        ).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        analysis_file_frame = ttk.LabelFrame(analysis_tab, text="Web Page Files")
        analysis_file_frame.pack(fill="x", pady=5)

        for column in range(2):
            analysis_file_frame.columnconfigure(column, weight=1)

        ttk.Button(
            analysis_file_frame,
            text="Open Scraped Text Folder",
            command=lambda: self.open_folder("output"),
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ttk.Button(
            analysis_file_frame,
            text="Open Analysis Folder",
            command=lambda: self.open_folder("analysis"),
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        document_frame = ttk.LabelFrame(documents_tab, text="Documents")
        document_frame.pack(fill="x", pady=5)

        for column in range(2):
            document_frame.columnconfigure(column, weight=1)

        ttk.Button(
            document_frame,
            text="Extract Document Text",
            command=self.extract_document_text,
        ).grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ttk.Button(
            document_frame,
            text="Analyze Document Text Folder",
            command=lambda: self.analyze_folder(
                "output/document_text",
                "output/document_analysis",
            ),
        ).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Button(
            document_frame,
            text="Open Documents Folder",
            command=lambda: self.open_folder("output/documents"),
        ).grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        ttk.Button(
            document_frame,
            text="Open Document Analysis Folder",
            command=lambda: self.open_folder("output/document_analysis"),
        ).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        log_frame = ttk.LabelFrame(log_tab, text="Log")
        log_frame.pack(fill="both", expand=True, pady=5)

        self.log_box = ScrolledText(log_frame)
        self.log_box.pack(fill="both", expand=True)

    def set_status(self, message):
        self.root.after(
            0,
            lambda: self.status_text.set(f"Status: {message}")
        )

    def select_csv(self):
        filename = filedialog.askopenfilename(
            title="Select URL CSV",
            filetypes=[("CSV Files", "*.csv")],
        )

        if filename:
            self.csv_path.set(filename)
    
    def open_file(self, filepath):
        path = Path(filepath)

        if not path.exists():
            messagebox.showinfo(
                "File Not Found",
                f"{filepath} does not exist yet. Run the pipeline first."
            )
            return

        try:
            os.startfile(path)
        except AttributeError:
            subprocess.run(["open", str(path)], check=False)
        except Exception as error:
            self.log(f"Could not open file: {error}")

    def open_folder(self, folder_path):
        path = Path(folder_path)
        path.mkdir(parents=True, exist_ok=True)

        try:
            os.startfile(str(path.resolve()))
        except AttributeError:
            subprocess.run(["open", str(path.resolve())], check=False)
        except Exception as error:
            self.log(f"Could not open folder: {error}")

    def get_chunk_size(self):
        try:
            value = int(self.chunk_size.get())
        except ValueError:
            raise ValueError("Claude chunk size must be a number.")

        if value <= 0:
            raise ValueError("Claude chunk size must be greater than 0.")

        return value

    def log(self, message):
        self.root.after(0, self._log, message)

    def _log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def start_pipeline(self):
        threading.Thread(
            target=self.run_pipeline,
            daemon=True,
        ).start()

    def run_pipeline(self):
        try:
            self.set_status("Running pipeline...")
            self.log("Starting pipeline...")
            self.log(f"CSV: {self.csv_path.get()}")

            main(
                input_file=self.csv_path.get(),
                test_mode=self.test_mode.get(),
                download_audio=self.download_audio.get(),
            )

            self.log("Pipeline complete.")
            self.set_status("Ready")

            self.root.after(
                0,
                lambda: messagebox.showinfo("Success", "Processing completed."),
            )

        except Exception as error:
            error_message = str(error)
            self.log(f"ERROR: {error_message}")
            self.set_status("Error occurred. See log for details.")

            self.root.after(
                0,
                lambda: messagebox.showerror("Error", error_message),
            )

    def extract_document_text(self):
        threading.Thread(
            target=self.run_extract_document_text,
            daemon=True,
        ).start()


    def run_extract_document_text(self):
        from src.storage import save_text
        from src.reports import update_document_extraction_results
        from config.settings import (
            DOCUMENT_OUTPUT_DIR,
            DOCUMENT_TEXT_OUTPUT_DIR,
            OUTPUT_DIR,
        )
        from src.documents import (
            DOCUMENT_EXTENSIONS,
            extract_text,
            file_sha256,
            normalize_document,
        )

        document_folder = Path(DOCUMENT_OUTPUT_DIR)
        text_folder = Path(DOCUMENT_TEXT_OUTPUT_DIR)
        text_folder.mkdir(parents=True, exist_ok=True)

        if not document_folder.exists():
            self.log("No documents folder found. Run the pipeline first.")
            self.set_status("Ready")
            return

        files = [
            path
            for path in document_folder.rglob("*")
            if path.is_file()
            and path.suffix.lower() in DOCUMENT_EXTENSIONS
        ]

        if not files:
            self.log("No documents found to extract.")
            self.set_status("Ready")
            return

        self.set_status("Extracting document text...")
        extraction_rows = []
        extraction_cache = {}

        for index, path in enumerate(files, start=1):
            normalized_path = ""
            content_hash = None

            try:
                if not path.exists():
                    self.log(f"Skipping missing converted file: {path.name}")
                    continue

                self.log(f"Extracting {index} of {len(files)}: {path.name}")

                content_hash = file_sha256(path)
                cached_result = extraction_cache.get(content_hash)

                if cached_result is not None:
                    duplicate_result = dict(cached_result)
                    duplicate_result["local_path"] = str(path)
                    extraction_rows.append(duplicate_result)
                    self.log(
                        f"Reused extracted text for duplicate: {path.name}"
                    )
                    continue

                normalized_path = normalize_document(path)
                text = extract_text(normalized_path)

                if text.strip():
                    text_file = save_text(
                        text,
                        path.name,
                        DOCUMENT_TEXT_OUTPUT_DIR
                    )
                    self.log(f"Saved text: {text_file}")
                    extraction_result = {
                        "local_path": str(path),
                        "normalized_path": str(normalized_path),
                        "document_text_file": str(text_file),
                        "character_count": len(text),
                        "extraction_status": "extracted",
                        "extraction_error": "",
                    }
                    extraction_rows.append(extraction_result)
                    extraction_cache[content_hash] = extraction_result
                else:
                    self.log(f"No text extracted: {path.name}")
                    extraction_result = {
                        "local_path": str(path),
                        "normalized_path": str(normalized_path),
                        "extraction_status": "no_text",
                        "extraction_error": "No text could be extracted.",
                    }
                    extraction_rows.append(extraction_result)
                    extraction_cache[content_hash] = extraction_result

            except Exception as error:
                self.log(f"Failed to extract {path.name}: {error}")
                extraction_result = {
                    "local_path": str(path),
                    "normalized_path": str(normalized_path),
                    "extraction_status": "failed",
                    "extraction_error": str(error),
                }
                extraction_rows.append(extraction_result)

                if content_hash is not None:
                    extraction_cache[content_hash] = extraction_result

        try:
            summary_path, updated_rows = update_document_extraction_results(
                extraction_rows,
                OUTPUT_DIR,
            )
            self.log(
                "Updated document summary: "
                f"{summary_path} ({updated_rows} row(s) matched)"
            )
        except Exception as error:
            self.log(f"Could not update document summary: {error}")

        self.set_status("Ready")
        self.log("Document text extraction complete.")

    def get_available_analysis_urls(self):
        summary_path = Path(OUTPUT_DIR) / SUMMARY_FILENAME

        if not summary_path.exists():
            messagebox.showinfo(
                "No Pipeline Results",
                "Run the pipeline first to create the URL summary.",
            )
            return []

        try:
            summary = pd.read_csv(
                summary_path,
                dtype=str,
                keep_default_na=False,
            )
        except Exception as error:
            messagebox.showerror(
                "Error",
                f"Could not read the URL summary:\n{error}",
            )
            return []

        if "url" not in summary.columns:
            messagebox.showerror(
                "Invalid Summary",
                "The URL summary does not contain a url column.",
            )
            return []

        if "status" in summary.columns:
            summary = summary[
                summary["status"].astype(str).str.lower().eq("success")
            ]

        urls = [
            url.strip()
            for url in summary["url"].tolist()
            if isinstance(url, str) and url.strip()
        ]
        urls = list(dict.fromkeys(urls))

        if not urls:
            messagebox.showinfo(
                "No URLs",
                "No completed URLs were found in the URL summary.",
            )
            return []

        return urls

    def get_link_analysis_options(self):
        try:
            chunk_size = self.get_chunk_size()
        except ValueError as error:
            messagebox.showerror("Invalid Chunk Size", str(error))
            return None

        research_instructions = self.research_instructions_box.get(
            "1.0",
            "end-1c",
        ).strip()

        enable_web_search = self.enable_web_search.get()
        max_web_searches = 5

        if enable_web_search:
            try:
                max_web_searches = int(self.max_web_searches.get())
            except (TypeError, ValueError):
                messagebox.showerror(
                    "Invalid Web Search Limit",
                    "Maximum web searches must be a whole number from 1 to 20.",
                )
                return None

            if not 1 <= max_web_searches <= 20:
                messagebox.showerror(
                    "Invalid Web Search Limit",
                    "Maximum web searches must be between 1 and 20.",
                )
                return None

        return (
            research_instructions,
            chunk_size,
            enable_web_search,
            max_web_searches,
        )

    def prompt_analyze_link(self):
        urls = self.get_available_analysis_urls()

        if not urls:
            return

        options = self.get_link_analysis_options()

        if options is None:
            return

        (
            research_instructions,
            chunk_size,
            enable_web_search,
            max_web_searches,
        ) = options

        popup = tk.Toplevel(self.root)
        popup.title("Select URLs to Analyze")
        popup.geometry("900x400")

        ttk.Label(
            popup,
            text=(
                "Select one or more original URLs. Each webpage and its "
                "associated extracted documents will be analyzed together. "
                "Use Ctrl-click or Shift-click to select multiple URLs."
            ),
            wraplength=850,
        ).pack(anchor="w", padx=10, pady=(10, 5))

        listbox = tk.Listbox(
            popup,
            width=130,
            height=14,
            selectmode=tk.EXTENDED,
        )
        listbox.pack(fill="both", expand=True, padx=10, pady=5)

        for url in urls:
            listbox.insert(tk.END, url)

        def begin_analysis():
            selection = listbox.curselection()

            if not selection:
                messagebox.showerror(
                    "No Selection",
                    "Please select a URL to analyze.",
                    parent=popup,
                )
                return

            source_urls = [urls[index] for index in selection]
            link_count = len(source_urls)
            web_search_notice = (
                "\n\nWeb search is enabled for the final synthesis "
                f"(up to {max_web_searches} searches)."
                if enable_web_search
                else ""
            )
            confirmed = messagebox.askyesno(
                "Confirm Link Analysis",
                f"Analyze {link_count} selected URL(s) and their associated "
                "extracted documents in one Claude report? This uses API "
                f"credits.{web_search_notice}",
                parent=popup,
            )

            if not confirmed:
                return

            popup.destroy()
            self.start_selected_link_analysis(
                source_urls,
                research_instructions,
                chunk_size,
                enable_web_search,
                max_web_searches,
            )

        ttk.Button(
            popup,
            text="Analyze Selected URLs",
            command=begin_analysis,
        ).pack(pady=(0, 10))

    def prompt_analyze_all_links(self):
        urls = self.get_available_analysis_urls()

        if not urls:
            return

        options = self.get_link_analysis_options()

        if options is None:
            return

        (
            research_instructions,
            chunk_size,
            enable_web_search,
            max_web_searches,
        ) = options
        web_search_notice = (
            "\n\nWeb search is enabled for the final synthesis "
            f"(up to {max_web_searches} searches)."
            if enable_web_search
            else ""
        )
        confirmed = messagebox.askyesno(
            "Confirm Bulk Analysis",
            f"Analyze all {len(urls)} URL(s) and their associated extracted "
            "documents in one Claude report? This can require multiple Claude "
            f"requests and use substantial API credits.{web_search_notice}",
        )

        if not confirmed:
            return

        self.start_selected_link_analysis(
            urls,
            research_instructions,
            chunk_size,
            enable_web_search,
            max_web_searches,
        )

    def start_selected_link_analysis(
        self,
        source_urls,
        research_instructions,
        chunk_size,
        enable_web_search,
        max_web_searches,
    ):
        target = (
            self.run_link_analysis
            if len(source_urls) == 1
            else self.run_bulk_link_analysis
        )

        threading.Thread(
            target=target,
            args=(
                source_urls,
                research_instructions,
                chunk_size,
                enable_web_search,
                max_web_searches,
            )
            if len(source_urls) > 1
            else (
                source_urls[0],
                research_instructions,
                chunk_size,
                enable_web_search,
                max_web_searches,
            ),
            daemon=True,
        ).start()

    def collect_link_content(self, source_url):
        """Load the webpage and extracted documents associated with one URL."""

        summary_path = Path(OUTPUT_DIR) / SUMMARY_FILENAME
        summary = pd.read_csv(summary_path, dtype=str, keep_default_na=False)
        source_rows = summary[summary["url"].astype(str).eq(source_url)]

        if source_rows.empty:
            raise ValueError(f"No pipeline result found for: {source_url}")

        content_items = []
        seen_paths = set()
        seen_content_hashes = set()

        for text_file in source_rows["text_file"].tolist():
            text_path = Path(str(text_file))

            if not text_file or not text_path.exists():
                continue

            path_key = str(text_path.resolve())
            if path_key in seen_paths:
                continue

            text = text_path.read_text(encoding="utf-8")
            content_hash = sha256(text.strip().encode("utf-8")).hexdigest()

            if content_hash in seen_content_hashes:
                continue

            content_items.append({
                "name": "Main webpage",
                "url": source_url,
                "text": text,
            })
            seen_paths.add(path_key)
            seen_content_hashes.add(content_hash)

        document_summary_path = Path(OUTPUT_DIR) / "document_summary.csv"

        if document_summary_path.exists():
            documents = pd.read_csv(
                document_summary_path,
                dtype=str,
                keep_default_na=False,
            )

            if "source_url" in documents.columns:
                documents = documents[
                    documents["source_url"].astype(str).eq(source_url)
                ]

                for _, document in documents.iterrows():
                    text_file = document.get("document_text_file", "")
                    text_path = Path(str(text_file))

                    if not text_file or not text_path.exists():
                        continue

                    path_key = str(text_path.resolve())
                    if path_key in seen_paths:
                        continue

                    document_name = Path(
                        str(document.get("local_path", ""))
                    ).name or "Associated document"

                    text = text_path.read_text(encoding="utf-8")
                    content_hash = sha256(
                        text.strip().encode("utf-8")
                    ).hexdigest()

                    if content_hash in seen_content_hashes:
                        continue

                    content_items.append({
                        "name": (
                            f"{document_name} "
                            f"(associated with {source_url})"
                        ),
                        "url": document.get("document_url", ""),
                        "text": text,
                    })
                    seen_paths.add(path_key)
                    seen_content_hashes.add(content_hash)

        if not content_items:
            raise ValueError(
                "No readable webpage or extracted document text was found for "
                "the selected URL. Run the pipeline, then extract document text."
            )

        return content_items

    def get_link_analysis_output_path(self, source_url):
        parsed = urlparse(source_url)
        label = f"{parsed.netloc}{parsed.path}".strip("/") or "link"
        label = re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_")
        label = label[:80] or "link"
        short_hash = sha256(source_url.encode("utf-8")).hexdigest()[:10]

        output_dir = Path(ANALYSIS_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)

        return output_dir / f"{label}_{short_hash}_analysis.md"

    def deduplicate_content_items(self, content_items):
        """Remove exact duplicate text while preserving the first source."""

        unique_items = []
        seen_hashes = set()

        for item in content_items:
            text = str(item.get("text") or "").strip()

            if not text:
                continue

            content_hash = sha256(text.encode("utf-8")).hexdigest()

            if content_hash in seen_hashes:
                continue

            seen_hashes.add(content_hash)
            unique_items.append(item)

        return unique_items, len(content_items) - len(unique_items)

    def get_bulk_analysis_output_path(self, source_urls):
        short_hash = sha256(
            "\n".join(sorted(source_urls)).encode("utf-8")
        ).hexdigest()[:10]

        output_dir = Path(ANALYSIS_OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)

        return output_dir / (
            f"bulk_{len(source_urls)}_links_{short_hash}_analysis.md"
        )

    def run_link_analysis(
        self,
        source_url,
        research_instructions,
        chunk_size,
        enable_web_search,
        max_web_searches,
    ):
        try:
            self.set_status("Preparing link analysis...")
            content_items = self.collect_link_content(source_url)
            self.log(
                f"Analyzing {source_url} with {len(content_items)} source(s)."
            )
            if enable_web_search:
                self.log(
                    "Web search enabled for final synthesis "
                    f"(up to {max_web_searches} searches)."
                )
            self.set_status("Analyzing selected URL...")

            analysis = analyze_source_bundle(
                source_url=source_url,
                content_items=content_items,
                research_instructions=research_instructions,
                max_chars=chunk_size,
                enable_web_search=enable_web_search,
                max_web_searches=max_web_searches,
            )

            output_path = self.get_link_analysis_output_path(source_url)
            output_path.write_text(analysis, encoding="utf-8")

            update_link_analysis_result(
                source_url=source_url,
                output_dir=OUTPUT_DIR,
                filename=SUMMARY_FILENAME,
                analysis_status="complete",
                analysis_file=str(output_path),
                analysis_character_count=len(analysis),
            )

            self.log(f"Link analysis saved to: {output_path}")
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Success",
                    f"Link analysis saved to:\n{output_path}",
                ),
            )

        except Exception as error:
            error_message = str(error)
            self.log(f"Link analysis failed for {source_url}: {error_message}")

            try:
                update_link_analysis_result(
                    source_url=source_url,
                    output_dir=OUTPUT_DIR,
                    filename=SUMMARY_FILENAME,
                    analysis_status="failed",
                    analysis_error=error_message,
                )
            except Exception as update_error:
                self.log(
                    "Could not update link analysis status: "
                    f"{update_error}"
                )

            self.root.after(
                0,
                lambda: messagebox.showerror("Link Analysis Error", error_message),
            )

        finally:
            self.set_status("Ready")

    def run_bulk_link_analysis(
        self,
        source_urls,
        research_instructions,
        chunk_size,
        enable_web_search,
        max_web_searches,
    ):
        try:
            self.set_status("Preparing bulk link analysis...")
            content_items = []

            for index, source_url in enumerate(source_urls, start=1):
                self.log(
                    f"Collecting sources for {index} of {len(source_urls)}: "
                    f"{source_url}"
                )
                content_items.extend(self.collect_link_content(source_url))

            content_items, duplicate_count = self.deduplicate_content_items(
                content_items
            )

            if duplicate_count:
                self.log(
                    f"Skipped {duplicate_count} exact duplicate analysis "
                    "source(s)."
                )

            self.log(
                f"Analyzing {len(source_urls)} URL(s) with "
                f"{len(content_items)} total source(s)."
            )
            if enable_web_search:
                self.log(
                    "Web search enabled for final synthesis "
                    f"(up to {max_web_searches} searches)."
                )
            self.set_status("Analyzing selected URLs...")

            analysis = analyze_source_collection(
                source_urls=source_urls,
                content_items=content_items,
                research_instructions=research_instructions,
                max_chars=chunk_size,
                enable_web_search=enable_web_search,
                max_web_searches=max_web_searches,
            )

            output_path = self.get_bulk_analysis_output_path(source_urls)
            output_path.write_text(analysis, encoding="utf-8")

            for source_url in source_urls:
                update_link_analysis_result(
                    source_url=source_url,
                    output_dir=OUTPUT_DIR,
                    filename=SUMMARY_FILENAME,
                    analysis_status="included_in_bulk_analysis",
                    analysis_file=str(output_path),
                    analysis_character_count=len(analysis),
                )

            self.log(f"Bulk analysis saved to: {output_path}")
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Success",
                    f"Bulk analysis saved to:\n{output_path}",
                ),
            )

        except Exception as error:
            error_message = str(error)
            self.log(f"Bulk link analysis failed: {error_message}")
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Bulk Analysis Error",
                    error_message,
                ),
            )

        finally:
            self.set_status("Ready")

    def prompt_transcribe_meeting_url(self):
        csv_path = Path("output/discovered_meetings.csv")

        if not csv_path.exists():
            messagebox.showinfo(
                "No Discovered Meetings",
                "Run the pipeline first to create output/discovered_meetings.csv."
            )
            return

        try:
            df = pd.read_csv(csv_path)
        except Exception as error:
            messagebox.showerror("Error", f"Could not read discovered meetings CSV:\n{error}")
            return

        if "meeting_url" not in df.columns or df.empty:
            messagebox.showinfo(
                "No Meeting URLs",
                "No meeting_url values were found in discovered_meetings.csv."
            )
            return

        urls = df["meeting_url"].dropna().drop_duplicates().tolist()

        popup = tk.Toplevel(self.root)
        popup.title("Select Meeting to Transcribe")
        popup.geometry("900x400")

        ttk.Label(
            popup,
            text="Select a discovered AdminMonitor meeting:"
        ).pack(anchor="w", padx=10, pady=(10, 5))

        listbox = tk.Listbox(popup, width=130, height=12)
        listbox.pack(fill="both", expand=True, padx=10, pady=5)

        for url in urls:
            listbox.insert(tk.END, url)

        def submit():
            selection = listbox.curselection()

            if not selection:
                messagebox.showerror("No Selection", "Please select a meeting URL.")
                return

            url = urls[selection[0]]
            popup.destroy()

            threading.Thread(
                target=self.run_meeting_transcription,
                args=(url,),
                daemon=True,
            ).start()

        ttk.Button(
            popup,
            text="Transcribe Selected Meeting",
            command=submit
        ).pack(pady=10)


    def run_meeting_transcription(self, url):
        try:
            self.set_status("Transcribing meeting...")
            self.log(f"Transcribing meeting URL: {url}")

            transcript_file = transcribe_meeting_url(url)

            self.log(f"Transcript saved to: {transcript_file}")
            self.set_status("Ready")

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Success",
                    f"Transcript saved to:\n{transcript_file}"
                ),
            )

        except Exception as error:
            error_message = str(error)
            self.log(f"ERROR: {error_message}")
            self.set_status("Error occurred. See log for details.")

            self.root.after(
                0,
                lambda: messagebox.showerror("Error", error_message),
            )
    
    def confirm_bulk_transcribe_meetings(self):
        csv_path = Path("output/discovered_meetings.csv")

        if not csv_path.exists():
            messagebox.showinfo(
                "No Discovered Meetings",
                "Run the pipeline first to create output/discovered_meetings.csv."
            )
            return

        try:
            df = pd.read_csv(csv_path)
        except Exception as error:
            messagebox.showerror("Error", f"Could not read discovered meetings CSV:\n{error}")
            return

        if "meeting_url" not in df.columns or df.empty:
            messagebox.showinfo(
                "No Meeting URLs",
                "No meeting_url values were found in discovered_meetings.csv."
            )
            return

        urls = df["meeting_url"].dropna().drop_duplicates().tolist()

        if not urls:
            messagebox.showinfo("No Meetings", "No valid meeting URLs found.")
            return

        confirm = messagebox.askyesno(
            "Confirm Bulk Transcription",
            f"Transcribe {len(urls)} discovered meetings?\n\n"
            "This may take a long time and download large audio files."
        )

        if not confirm:
            return

        threading.Thread(
            target=self.run_bulk_meeting_transcription,
            args=(urls,),
            daemon=True,
        ).start()


    def run_bulk_meeting_transcription(self, urls):
        total = len(urls)

        for index, url in enumerate(urls, start=1):
            try:
                self.set_status(f"Transcribing meeting {index} of {total}")
                self.log(f"Transcribing meeting {index} of {total}: {url}")

                transcript_file = transcribe_meeting_url(url)

                self.log(f"Transcript saved to: {transcript_file}")

            except Exception as error:
                self.log(f"Failed to transcribe {url}: {error}")

        self.set_status("Ready")
        self.log("Bulk meeting transcription complete.")

        self.root.after(
            0,
            lambda: messagebox.showinfo(
                "Done",
                "Bulk meeting transcription complete."
            ),
        )

    def estimate_existing_file(self):
        self.set_status("Estimating...")
        filepath = filedialog.askopenfilename(
            title="Select cleaned scraped text or transcript",
            filetypes=[("Text Files", "*.txt")],
        )

        if not filepath:
            self.set_status("Ready")
            return

        try:
            path = Path(filepath)

            with open(path, "r", encoding="utf-8") as file:
                text = file.read()

            estimate = estimate_analysis(
                text,
                source_name=path.name,
                max_chars=self.get_chunk_size(),
            )

            message = (
                f"File: {estimate.source_name}\n"
                f"Characters: {estimate.character_count:,}\n"
                f"Chunk size: {estimate.max_chars:,}\n"
                f"Estimated chunks: {estimate.chunk_count}\n"
                f"API key found: {estimate.api_key_found}\n\n"
                "This does not send anything to Claude."
            )

            self.log("Claude estimate:")
            self.log(message)
            self.set_status("Ready")

            messagebox.showinfo("Claude Estimate", message)

        except Exception as error:
            self.log(f"Estimate failed: {error}")
            self.set_status("Error occurred. See log for details.")
            messagebox.showerror("Error", str(error))

    def analyze_existing_file(self):
        filepath = filedialog.askopenfilename(
            title="Select cleaned output or transcript",
            filetypes=[("Text Files", "*.txt")],
        )

        if not filepath:
            self.set_status("Ready")
            return

        threading.Thread(
            target=self.run_analysis,
            args=(Path(filepath),),
            daemon=True,
        ).start()

    def run_analysis(self, path):
        self.set_status(f"Analyzing {path.name}")
        try:
            self.log(f"Analyzing: {path}")

            with open(path, "r", encoding="utf-8") as file:
                text = file.read()

            analysis = analyze_large_text(
                text,
                source_name=path.name,
                max_chars=self.get_chunk_size(),
            )

            output_dir = Path("analysis")
            output_dir.mkdir(exist_ok=True)

            output_path = output_dir / f"{path.stem}_analysis.md"

            with open(output_path, "w", encoding="utf-8") as file:
                file.write(analysis)

            self.log(f"Analysis saved to: {output_path}")

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Success",
                    f"Analysis saved to:\n{output_path}",
                ),
            )

        except Exception as error:
            error_message = str(error)
            self.log(f"ERROR: {error_message}")
            self.set_status("Error occurred. See log for details.")

            self.root.after(
                0,
                lambda: messagebox.showerror("Error", error_message),
            )
            
        self.set_status("Ready")

    def analyze_folder(self, folder_path, output_folder="analysis"):
        folder = Path(folder_path)
        folder.mkdir(exist_ok=True)

        files = list(folder.glob("*.txt"))

        if not files:
            messagebox.showinfo("No Files", f"No .txt files found in {folder_path}.")
            return

        confirm = messagebox.askyesno(
            "Confirm Analysis",
            f"Analyze {len(files)} text files from {folder_path}?",
        )

        if not confirm:
            return

        threading.Thread(
            target=self.run_folder_analysis,
            args=(files, output_folder),
            daemon=True,
        ).start()

    def run_folder_analysis(self, files, output_folder="analysis"):
        output_dir = Path(output_folder)
        output_dir.mkdir(parents=True, exist_ok=True)

        total = len(files)

        for index, path in enumerate(files, start=1):

            self.set_status(
                f"Analyzing {index} of {total}: {path.name}"
            )

            try:
                self.log(f"Analyzing {index} of {total}: {path.name}")

                with open(path, "r", encoding="utf-8") as file:
                    text = file.read()

                analysis = analyze_large_text(
                    text,
                    source_name=path.name,
                    max_chars=self.get_chunk_size(),
                )

                output_path = output_dir / f"{path.stem}_analysis.md"

                with open(output_path, "w", encoding="utf-8") as file:
                    file.write(analysis)

                self.log(f"Saved: {output_path}")

            except Exception as error:
                self.log(f"Failed: {path.name} — {error}")

        self.set_status("Ready")
        self.log("Folder analysis complete.")

        self.root.after(
            0,
            lambda: messagebox.showinfo("Done", "Folder analysis complete."),
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()
