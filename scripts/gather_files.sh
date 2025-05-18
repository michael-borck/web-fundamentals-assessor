#!/usr/bin/env bash
set -euo pipefail

SUBMISSIONS_DIR="master_assessment_reports"

for d in "$SUBMISSIONS_DIR"/*/; do
  student_dir="${d%/}"
  out_file="$student_dir/project-files.txt"
  python3 scripts/gather_files.py "$student_dir" "$out_file"
done

