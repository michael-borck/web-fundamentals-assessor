#!/usr/bin/env python3
"""
extract_links.py

Traverse a root directory of student folders, find the first GitHub repo URL
and Netlify link in any .md/.txt/.pdf/.docx under each student folder, extract username,
and write one row per student. If none found, records "none".

Usage:
    python extract_links.py [--ssh] <root_dir> <output.csv>
"""

import os
import re
import csv
import argparse
import logging

import pdfplumber
from docx import Document

# -----------------------------------------------------------------------------
# Suppress pdfplumber and pdfminer warnings
# -----------------------------------------------------------------------------
logging.getLogger("pdfplumber").setLevel(logging.ERROR)
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# Regex to capture GitHub owner and repo
GITHUB_REGEX = re.compile(
    r'(?:https?://github\.com/|git@github\.com:)'
    r'(?P<owner>[\w\-]+)/(?P<repo>[\w\-.]+)'
    r'(?:\.git)?'
)

# Raw and clean Netlify patterns
RAW_NETLIFY_REGEX = re.compile(r'https?://[A-Za-z0-9\-.]+\.netlify\.app[^\s]*')
CLEAN_NETLIFY_REGEX = re.compile(
    r'https?://[A-Za-z0-9\-.]+\.netlify\.app(?:/[^\s"\'<>\)]*)?'
)

def extract_text_from_pdf(path):
    """Extract all text from a PDF file using pdfplumber."""
    texts = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    texts.append(txt)
    except Exception:
        pass
    return "\n".join(texts)

def extract_text_from_docx(path):
    """Extract all text from a .docx file using python-docx."""
    texts = []
    try:
        doc = Document(path)
        for para in doc.paragraphs:
            if para.text:
                texts.append(para.text)
    except Exception:
        pass
    return "\n".join(texts)

def find_links_in_tree(root, use_ssh=False):
    owner = None
    repo = None
    netlify = None

    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            lname = fname.lower()
            if not lname.endswith(('.md', '.txt', '.pdf', '.docx')):
                continue

            fullpath = os.path.join(dirpath, fname)
            # load lines from the appropriate reader
            if lname.endswith('.pdf'):
                text = extract_text_from_pdf(fullpath)
                lines = text.splitlines()
            elif lname.endswith('.docx'):
                text = extract_text_from_docx(fullpath)
                lines = text.splitlines()
            else:
                with open(fullpath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()

            for line in lines:
                # GitHub
                if owner is None:
                    m = GITHUB_REGEX.search(line)
                    if m:
                        owner = m.group('owner')
                        repo  = m.group('repo')

                # Netlify
                if netlify is None:
                    raw = RAW_NETLIFY_REGEX.search(line)
                    if raw:
                        candidate = raw.group(0).strip()
                        clean = CLEAN_NETLIFY_REGEX.search(candidate)
                        if clean:
                            netlify = clean.group(0)

                if owner and netlify:
                    break

            if owner and netlify:
                break
        if owner and netlify:
            break

    # build GitHub URL
    if owner and repo:
        if use_ssh:
            github_url = f'git@github.com:{owner}/{repo}.git'
        else:
            github_url = f'https://github.com/{owner}/{repo}'
    else:
        github_url = None

    return owner, github_url, netlify

def traverse_and_extract(root_dir, csv_path, use_ssh=False):
    rows = []
    for entry in sorted(os.listdir(root_dir)):
        student_dir = os.path.join(root_dir, entry)
        if not os.path.isdir(student_dir):
            continue

        owner, github, netlify = find_links_in_tree(student_dir, use_ssh)
        rows.append({
            'student':  entry,
            'username': owner   or 'none',
            'github':   github  or 'none',
            'netlify':  netlify or 'none'
        })

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['student', 'username', 'github', 'netlify']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Extracted {len(rows)} student entries to {csv_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract GitHub usernames and links (HTTPS or SSH) plus clean Netlify links per student folder."
    )
    parser.add_argument('--ssh', action='store_true',
                        help="Output GitHub URLs in SSH form (git@github.com:owner/repo.git)")
    parser.add_argument('root_dir', help="Root directory containing student-number folders")
    parser.add_argument('output_csv', help="CSV file to write results to")
    args = parser.parse_args()

    if not os.path.isdir(args.root_dir):
        parser.error(f"{args.root_dir} is not a directory or does not exist.")

    traverse_and_extract(args.root_dir, args.output_csv, use_ssh=args.ssh)

if __name__ == '__main__':
    main()

