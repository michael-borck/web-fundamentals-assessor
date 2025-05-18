#!/usr/bin/env bash
set -euo pipefail

##
## CONFIGURATION — adjust these to match your setup
##
# 1) Directory of student submissions to scan for PDF/DOCX/MD/TXT:
SUBMISSIONS_DIR="submissions"

# 2) Where to dump all extracted .txt/.md from step 1:
CONVERSATIONS_OUTDIR="conversations"

# 3) CSV listing students & URLs for process_assessments.py:
CSV_FILE="submissions/submissions.csv"

# 4) If you need to override the main_assessor script location:
MAIN_SCRIPT="scripts/main_assessor.py"      # default in-process_assessments.py already points here

# 5) Name of the folder inside each student dir holding the raw conversations:
MANUAL_FOLDER_NAME="conversations"

# 6) Base directory where all “final_assessment_report.md” files live (for extract_results.py):
RESULTS_BASE_DIR="master_assessment_reports"

##
## 1) Pre-processing — pull text out of every PDF/DOCX/MD/TXT
##

echo "→ Pre-processing: gathering conversations…"
for d in "$SUBMISSIONS_DIR"/*/; do
  # strip trailing slash so we don’t end up with a double ‘//’
  student_dir="${d%/}"
  out_dir="$student_dir/conversations"
  python scripts/gather_conversations.py "$student_dir/" "$out_dir"
done


##
## 2) Main assessment — run your assessor over the CSV
##
#echo "→ Main assessment: processing submissions…"
python scripts/process_assessments.py \
    "$CSV_FILE" \
    --manual-folder-name "$MANUAL_FOLDER_NAME" \
    --main-script "$MAIN_SCRIPT" \
    --submissions-folder "$SUBMISSIONS_DIR"

##
## 3) Post-processing — extract results tables for all students
##
#echo "→ Post-processing: extracting results…"
#python scripts/extract_results.py \
    #--all \
    #--simplified \
    #--ascii \
    #--base-dir "$RESULTS_BASE_DIR"

echo "✅ All steps complete."

