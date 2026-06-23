import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import threading
from pathlib import Path
from analysis_service import analyze_large_text, estimate_analysis

from settings import INPUT_FILE, DEFAULT_CHUNK_SIZE
from main import main


class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Regulatory Web Scraper")
        self.root.geometry("900x600")

        self.csv_path = tk.StringVar(value=INPUT_FILE)

        self.build_ui()

    def open_folder(self, folder_path):
        os.makedirs(folder_path, exist_ok=True)

        try:
            os.startfile(folder_path)
        except AttributeError:
            subprocess.run(["open", folder_path], check=False)
        except Exception as error:
            self.log(f"Could not open folder: {error}")

    def analyze_folder(self, folder_path):
        folder = Path(folder_path)
        folder.mkdir(exist_ok=True)

        files = list(folder.glob("*.txt"))

        if not files:
            messagebox.showinfo(
                "No Files",
                f"No .txt files found in {folder_path}."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Analysis",
            f"Analyze {len(files)} text files from {folder_path}?"
        )

        if not confirm:
            return

        threading.Thread(
            target=self.run_folder_analysis,
            args=(files,),
            daemon=True
        ).start()

    def run_folder_analysis(self, files):
        output_dir = Path("analysis")
        output_dir.mkdir(exist_ok=True)

        total = len(files)

        for index, path in enumerate(files, start=1):
            try:
                self.log(f"Analyzing {index} of {total}: {path.name}")

                with open(path, "r", encoding="utf-8") as file:
                    text = file.read()

                max_chars = int(self.chunk_size.get())

                analysis = analyze_large_text(
                    text,
                    source_name=path.name,
                    max_chars=max_chars
                )

                output_path = output_dir / f"{path.stem}_analysis.md"

                with open(output_path, "w", encoding="utf-8") as file:
                    file.write(analysis)

                self.log(f"Saved: {output_path}")

            except Exception as error:
                self.log(f"Failed: {path.name} — {error}")

        self.log("Folder analysis complete.")

        self.root.after(
            0,
            lambda: messagebox.showinfo("Done", "Folder analysis complete.")
        )

    def build_ui(self):

        title = ttk.Label(
            self.root,
            text="Regulatory Web Scraper",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(pady=10)

    def estimate_existing_file(self):
        filepath = filedialog.askopenfilename(
            title="Select cleaned output or transcript",
            filetypes=[("Text Files", "*.txt")]
        )

        if not filepath:
            return

        try:
            path = Path(filepath)

            with open(path, "r", encoding="utf-8") as file:
                text = file.read()

            max_chars = int(self.chunk_size.get())

            estimate = estimate_analysis(
                text,
                source_name=path.name,
                max_chars=max_chars
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

            messagebox.showinfo("Claude Estimate", message)

        except Exception as error:
            self.log(f"Estimate failed: {error}")
            messagebox.showerror("Error", str(error))

        # ---------------------------
        # CSV Selection
        # ---------------------------

        frame = ttk.LabelFrame(self.root, text="Input")
        frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame, text="URLs CSV").grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="w"
        )

        ttk.Entry(
            frame,
            textvariable=self.csv_path,
            width=80
        ).grid(
            row=0,
            column=1,
            padx=5,
            pady=5
        )

        ttk.Button(
            frame,
            text="Browse",
            command=self.select_csv
        ).grid(
            row=0,
            column=2,
            padx=5,
            pady=5
        )

        # ---------------------------
        # Options
        # ---------------------------

        options = ttk.LabelFrame(self.root, text="Options")
        options.pack(fill="x", padx=10, pady=5)

        self.chunk_size = tk.StringVar(value=str(DEFAULT_CHUNK_SIZE))
        self.test_mode = tk.BooleanVar(value=True)
        self.download_audio = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            options,
            text="Test Mode",
            variable=self.test_mode
        ).pack(anchor="w", padx=10, pady=2)

        ttk.Checkbutton(
            options,
            text="Download & Transcribe Audio",
            variable=self.download_audio
        ).pack(anchor="w", padx=10, pady=2)

        ttk.Label(
            options,
            text="Claude chunk size"
        ).pack(anchor="w", padx=10, pady=(8, 0))

        ttk.Entry(
            options,
            textvariable=self.chunk_size,
            width=12
        ).pack(anchor="w", padx=10, pady=2)

        # ---------------------------
        # Buttons
        # ---------------------------

        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="Run Pipeline",
            command=self.start_pipeline
        ).pack(side="left")

        ttk.Button(
            button_frame,
            text="Analyze Existing Output",
            command=self.analyze_existing_file
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Analyze Output Folder",
            command=lambda: self.analyze_folder("output")
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Analyze Transcripts Folder",
            command=lambda: self.analyze_folder("transcripts")
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Open Output Folder",
            command=lambda: self.open_folder("output")
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Open Transcripts Folder",
            command=lambda: self.open_folder("transcripts")
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Open Analysis Folder",
            command=lambda: self.open_folder("analysis")
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Estimate Claude Cost",
            command=self.estimate_existing_file
        ).pack(side="left", padx=5)

        # ---------------------------
        # Log Output
        # ---------------------------

        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.log_box = ScrolledText(log_frame)
        self.log_box.pack(fill="both", expand=True)

    def select_csv(self):
        filename = filedialog.askopenfilename(
            title="Select URL CSV",
            filetypes=[("CSV Files", "*.csv")]
        )

        if filename:
            self.csv_path.set(filename)

    def log(self, message):
        self.root.after(0, self._log, message)

    def _log(self, message):
        self.log_box.insert(tk.END, message + "\n")
        self.log_box.see(tk.END)

    def start_pipeline(self):
        threading.Thread(
            target=self.run_pipeline,
            daemon=True
        ).start()

    def run_pipeline(self):

        try:
            self.log("Starting pipeline...")
            self.log(f"CSV: {self.csv_path.get()}")

            main(
                input_file=self.csv_path.get(),
                test_mode=self.test_mode.get(),
                download_audio=self.download_audio.get()
            )

            self.log("Pipeline complete.")

            self.root.after(
                0,
                lambda: messagebox.showinfo("Success", "Processing completed.")
            )

        except Exception as e:
            self.log(f"ERROR: {e}")

            self.root.after(
                0,
                lambda: messagebox.showerror("Error", str(e))
            )


    def analyze_existing_file(self):
        filepath = filedialog.askopenfilename(
            title="Select cleaned output or transcript",
            filetypes=[("Text Files", "*.txt")]
        )

        if not filepath:
            return

        threading.Thread(
            target=self.run_analysis,
            args=(filepath,),
            daemon=True
        ).start()


    def run_analysis(self, filepath):
        try:
            self.log(f"Analyzing: {filepath}")

            path = Path(filepath)

            with open(path, "r", encoding="utf-8") as file:
                text = file.read()

            max_chars = int(self.chunk_size.get())

            analysis = analyze_large_text(
                text,
                source_name=path.name,
                max_chars=max_chars
            )

            output_dir = Path("analysis")
            output_dir.mkdir(exist_ok=True)

            output_path = output_dir / f"{path.stem}_analysis.md"

            with open(output_path, "w", encoding="utf-8") as file:
                file.write(analysis)

            self.log(f"Analysis saved to: {output_path}")

            self.root.after(
                0,
                lambda: messagebox.showinfo("Success", f"Analysis saved to:\n{output_path}")
            )

        except Exception as error:
            self.log(f"Analysis failed: {error}")

            self.root.after(
                0,
                lambda: messagebox.showerror("Error", str(error))
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()