#!/usr/bin/env python3
"""
gather_files.py

Recursively collects all .txt and .md files under a directory
and writes them into a single .txt file, with each section
prefaced by a "--- Filename: relative/path ---" header.
"""

import argparse
from pathlib import Path

def gather_files(input_dir: Path, output_file: Path):
    """
    Walk input_dir for .txt .md .css .html .js files, and write them to output_file.
    """
    with output_file.open('w', encoding='utf-8') as out:
        # Sort for consistent ordering
        for path in sorted(input_dir.rglob('*')):
            if path.is_file() and path.suffix.lower() in ('.txt', '.md', '.css', '.html', '.js'):
                rel_path = path.relative_to(input_dir)
                out.write(f"--- Filename: {rel_path} ---\n")
                # Write file contents
                out.write(path.read_text(encoding='utf-8'))
                out.write('\n\n')  # blank line between entries

def main():
    parser = argparse.ArgumentParser(
        description="Gather all text (.txt .md .css .html .js) into one .txt file."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Root directory to scan for text files"
    )
    parser.add_argument(
        "output_file",
        type=Path,
        help="Path of the resulting .txt file"
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        parser.error(f"{args.input_dir!r} is not a directory.")
    # Ensure parent directory for output exists
    args.output_file.parent.mkdir(parents=True, exist_ok=True)

    gather_files(args.input_dir, args.output_file)
    print(f"Collected files from {args.input_dir} into {args.output_file}")

if __name__ == "__main__":
    main()

