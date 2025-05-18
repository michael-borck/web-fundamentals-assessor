#!/usr/bin/env bash
set -euo pipefail

SUBMISSIONS_DIR="master_assessment_reports"
if [ ! -d "$SUBMISSIONS_DIR" ]; then
  echo "Directory $SUBMISSIONS_DIR does not exist." >&2
  exit 1
fi

for d in "$SUBMISSIONS_DIR"/*/; do
  student_dir="${d%/}"
  out_file="$student_dir/results.txt"

  # skip if there's no results.txt
  if [ ! -f "$out_file" ]; then
    echo "  ↳ No results.txt in $student_dir — skipping."
    continue
  fi

  python3 scripts/add_total_score.py "$out_file"
  echo "  ✔ Added total score to $out_file"
done

