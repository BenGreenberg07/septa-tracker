#!/usr/bin/env bash
# Rebuild docs/wiring-diagram.pdf: sheet 1 (the as-built diagram) plus the
# power sheets 2-4 from sheets.html and figures.py.
set -e
cd "$(dirname "$0")"
/opt/homebrew/bin/python3 ../../rpi5/tools/make-wiring-diagram.py >/dev/null
/opt/homebrew/bin/python3 figures.py >/dev/null
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --no-pdf-header-footer --print-to-pdf-no-header \
  --print-to-pdf="../wiring-diagram.pdf" "file://$PWD/sheets.html" 2>/dev/null
echo "wrote docs/wiring-diagram.pdf"
