#!/usr/bin/env python3
import argparse
import re
import sys

def main():
    parser = argparse.ArgumentParser(
        description="Recompute and insert a single Total Score line in your results file."
    )
    parser.add_argument('filename', help="Path to the results file to update")
    args = parser.parse_args()

    # 1. Read in
    try:
        with open(args.filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        sys.exit(f"Error reading {args.filename}: {e}")

    # 2. Remove any existing Total Score lines
    lines = [l for l in lines if not re.match(r'^\s*Total Score:', l)]

    # 3. Find all " | <number>" lines and sum
    score_re = re.compile(r'\|\s*([-+]?\d+(?:\.\d+)?)\s*$')
    total = 0.0
    last_score_idx = None
    for idx, line in enumerate(lines):
        m = score_re.search(line)
        if m:
            try:
                total += float(m.group(1))
                last_score_idx = idx
            except ValueError:
                pass

    if last_score_idx is None:
        sys.exit("No score lines found in the file; nothing to total.")

    # 4. Insert the one correct Total Score line
    total_line = f"Total Score: {total}\n"
    lines.insert(last_score_idx + 1, total_line)

    # 5. Write it back
    try:
        with open(args.filename, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    except Exception as e:
        sys.exit(f"Error writing {args.filename}: {e}")

if __name__ == '__main__':
    main()

