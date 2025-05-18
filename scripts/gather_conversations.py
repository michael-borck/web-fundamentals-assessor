#!/usr/bin/env python3
import argparse
import os
import shutil
from pathlib import Path
import logging

from docx import Document
from pdfminer.high_level import extract_text as extract_pdf_text

logging.getLogger("pdfminer").setLevel(logging.ERROR)

def extract_docx(path: Path) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def process_file(file_path: Path, output_dir: Path):
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        text = extract_pdf_text(str(file_path))
        out_file = output_dir / (file_path.stem + ".txt")
        out_file.write_text(text, encoding="utf-8")
    elif ext == ".docx":
        text = extract_docx(file_path)
        out_file = output_dir / (file_path.stem + ".txt")
        out_file.write_text(text, encoding="utf-8")
    elif ext in {".txt", ".md"}:
        shutil.copy2(file_path, output_dir / file_path.name)
    # else: ignore

def main():
    parser = argparse.ArgumentParser(
        description="Recursively extract text from PDF/DOCX and copy TXT/MD into an output directory."
    )
    parser.add_argument("input_dir", help="Root folder to scan")
    parser.add_argument("output_dir", help="Folder where all .txt/.md (and extracted PDFs/DOCs) go")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Walk the tree
    for root, dirs, files in os.walk(input_dir):
        root_path = Path(root).resolve()

        # Skip walking into the output_dir itself
        if output_dir == root_path or output_dir in root_path.parents:
            continue

        for fname in files:
            file_path = root_path / fname
            process_file(file_path, output_dir)
    print(f"Processed files from {os.path.basename(input_dir)}") 
if __name__ == "__main__":
    main()

