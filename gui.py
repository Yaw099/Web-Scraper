import os
import subprocess
import threading
import tkinter as tk
import pandas as pd
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from analysis_service import analyze_large_text, estimate_analysis
from main import main
from settings import DEFAULT_CHUNK_SIZE, INPUT_FILE
from meeting_transcription import transcribe_meeting_url


class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Regulatory Web Scraper")
        self.root.geometry("1050x650")

        self.csv_path = tk.StringVar(value=INPUT_FILE)
        self.status_text = tk.StringVar(value="Status: Ready")
        self.chunk_size = tk.StringVar(value=str(DEFAULT_CHUNK_SIZE))
        self.test_mode = tk.BooleanVar(value=True)
        self.download_audio = tk.BooleanVar(value=True)

        self.build_ui()

    def build_ui(self):
        title = ttk.Label(
            self.root,
            text="Regulatory Web Scraper",
            font=("Segoe UI", 16, "bold"),
        )
        title.pack(pady=10)

        status_label = ttk.Label(
            self.root,
            textvariable=self.status_text,
            font=("Segoe UI", 10)
        )
        status_label.pack(pady=(0, 10))

        input_frame = ttk.LabelFrame(self.root, text="Input")
        input_frame.pack(fill="x", padx=10, pady=5)

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
            width=90,
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

        options_frame = ttk.LabelFrame(self.root, text="Options")
        options_frame.pack(fill="x", padx=10, pady=5)

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

        pipeline_frame = ttk.LabelFrame(self.root, text="1. Pipeline")
        pipeline_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            pipeline_frame,
            text="Run Pipeline",
            command=self.start_pipeline,
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            pipeline_frame,
            text="Transcribe Meeting URL",
            command=self.prompt_transcribe_meeting_url,
        ).pack(side="left", padx=5, pady=5)

        analysis_frame = ttk.LabelFrame(self.root, text="2. AI Analysis")
        analysis_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            analysis_frame,
            text="Estimate Claude Usage",
            command=self.estimate_existing_file,
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            analysis_frame,
            text="Analyze Scraped Text File",
            command=self.analyze_existing_file,
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            analysis_frame,
            text="Analyze Scraped Text Folder",
            command=lambda: self.analyze_folder("output"),
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            analysis_frame,
            text="Analyze Transcripts Folder",
            command=lambda: self.analyze_folder("transcripts"),
        ).pack(side="left", padx=5, pady=5)

        folder_frame = ttk.LabelFrame(self.root, text="3. Results Folders")
        folder_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            folder_frame,
            text="Open Scraped Text Folder",
            command=lambda: self.open_folder("output"),
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            folder_frame,
            text="Open Discovered Meetings CSV",
            command=lambda: self.open_file("output/discovered_meetings.csv"),
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            folder_frame,
            text="Open Transcripts Folder",
            command=lambda: self.open_folder("transcripts"),
        ).pack(side="left", padx=5, pady=5)

        ttk.Button(
            folder_frame,
            text="Open Analysis Folder",
            command=lambda: self.open_folder("analysis"),
        ).pack(side="left", padx=5, pady=5)

        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

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
        os.makedirs(folder_path, exist_ok=True)

        try:
            os.startfile(folder_path)
        except AttributeError:
            subprocess.run(["open", folder_path], check=False)
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
            self.log(f"ERROR: {error}")
            self.set_status("Error occurred. See log for details.")

            self.root.after(
                0,
                lambda: messagebox.showerror("Error", str(error)),
            )

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
            self.log(f"Meeting transcription failed: {error}")
            self.set_status("Error occurred. See log for details.")

            self.root.after(
                0,
                lambda: messagebox.showerror("Error", str(error)),
            )

    def estimate_existing_file(self):
        self.set_status("Estimating...")
        filepath = filedialog.askopenfilename(
            title="Select cleaned scraped text or transcript",
            filetypes=[("Text Files", "*.txt")],
        )

        if not filepath:
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
            self.set_status("Ready")

        except Exception as error:
            self.log(f"Analysis failed: {error}")
            self.set_status("Error occurred. See log for details.")

            self.root.after(
                0,
                lambda: messagebox.showerror("Error", str(error)),
            )

    def analyze_folder(self, folder_path):
        folder = Path(folder_path)
        folder.mkdir(exist_ok=True)

        files = list(folder.glob("*.txt"))

        if not files:
            messagebox.showinfo(
                "No Files",
                f"No .txt files found in {folder_path}.",
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Analysis",
            f"Analyze {len(files)} text files from {folder_path}?",
        )

        if not confirm:
            return

        threading.Thread(
            target=self.run_folder_analysis,
            args=(files,),
            daemon=True,
        ).start()

    def run_folder_analysis(self, files):
        output_dir = Path("analysis")
        output_dir.mkdir(exist_ok=True)

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

                self.set_status("Ready")

            except Exception as error:
                self.log(f"Failed: {path.name} — {error}")

        self.log("Folder analysis complete.")

        self.root.after(
            0,
            lambda: messagebox.showinfo("Done", "Folder analysis complete."),
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()