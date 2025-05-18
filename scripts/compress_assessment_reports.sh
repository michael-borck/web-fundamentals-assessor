#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 REPORTS_DIR"
  exit 1
fi

REPORTS_DIR="$1"

if [ ! -d "$REPORTS_DIR" ]; then
  echo "Error: directory '$REPORTS_DIR' not found." >&2
  exit 1
fi

echo "Compressing each folder in '$REPORTS_DIR'…"
for dir in "$REPORTS_DIR"/*/; do
  # ensure it's a directory
  [ -d "$dir" ] || continue

  base="$(basename "$dir")"
  zipfile="$REPORTS_DIR/${base}.zip"

  # remove any old zip so we get a fresh copy
  [ -f "$zipfile" ] && rm -f "$zipfile"

  echo "  ↳ $base → ${base}.zip"
  zip -r "$zipfile" "$dir" >/dev/null
done

echo "All done!"

