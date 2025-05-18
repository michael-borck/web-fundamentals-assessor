#!/usr/bin/env bash
set -euo pipefail

# Path to your prompt file (adjust if needed)
PROMPT_FILE="docs/prompt.txt"

# Directory containing student submission folders (adjust if needed)
SUBMISSIONS_DIR="master_assessment_reports"

# Path to the Python feedback script (adjust if needed)
FEEDBACK_SCRIPT="scripts/get_feedback.py"

for STUDENT_DIR in "$SUBMISSIONS_DIR"/*/; do
  CONTENT_FILE="${STUDENT_DIR}project-files.txt"
  OUTPUT_FILE="${STUDENT_DIR}results.txt"

  if [[ -f "$CONTENT_FILE" ]]; then
    echo "Processing ${STUDENT_DIR}…" >&2
    mkdir -p "$(dirname "$OUTPUT_FILE")"
    # Run feedback script and append both stdout and stderr to results.txt
    python "$FEEDBACK_SCRIPT" "$PROMPT_FILE" "$CONTENT_FILE" >> "$OUTPUT_FILE" 2>&1
    echo "→ Appended feedback to ${OUTPUT_FILE}" >&2
  else
    echo "Skipping ${STUDENT_DIR}: project-files.txt not found" >&2
  fi
done



