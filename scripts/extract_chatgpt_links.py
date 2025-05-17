#!/usr/bin/env python3
"""
extract_chatgpt_links.py

Recursively scan a folder for .txt, .md, .pdf, .docx files and extract ChatGPT share links.
If any are found, write them (one per line) to <search_root>/chats.txt.
"""

import os
import re
import argparse
from pathlib import Path

from PyPDF2 import PdfReader
from docx import Document

# regex to catch both OpenAI share links and ShareGPT links
URL_PATTERN = re.compile(
    r'https?://(?:chat\.openai\.com/share/[A-Za-z0-9\-]+|sharegpt\.com/c/[A-Za-z0-9_\-]+)'
)

def extract_links_from_text(text):
    return URL_PATTERN.findall(text)

def extract_from_txt_md(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return extract_links_from_text(f.read())
    except:
        return []

def extract_from_pdf(path):
    links = []
    try:
        reader = PdfReader(str(path))
        for page in reader.pages:
            text = page.extract_text() or ""
            links += extract_links_from_text(text)
    except:
        pass
    return links

def extract_from_docx(path):
    try:
        doc = Document(str(path))
        text = "\n".join(p.text for p in doc.paragraphs)
        return extract_links_from_text(text)
    except:
        return []

def scan_folder(root):
    all_links = set()
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            ext = Path(fname).suffix.lower()
            full = Path(dirpath) / fname
            if ext in {'.txt', '.md'}:
                found = extract_from_txt_md(full)
            elif ext == '.pdf':
                found = extract_from_pdf(full)
            elif ext == '.docx':
                found = extract_from_docx(full)
            else:
                continue
            all_links.update(found)
    return all_links

def main():
    parser = argparse.ArgumentParser(
        description="Extract ChatGPT/share links and save to chats.txt in the search folder"
    )
    parser.add_argument('search_path', help="Root folder to recursively scan")
    args = parser.parse_args()

    root = Path(args.search_path)
    links = scan_folder(root)

    if links:
        out_file = root / 'chats.txt'
        with out_file.open('w', encoding='utf-8') as f:
            for link in sorted(links):
                f.write(link + "\n")
        print(f"Found {len(links)} link(s). Saved to {out_file}")
    else:
        print("No ChatGPT share links found. No file created.")

if __name__ == '__main__':
    main()

