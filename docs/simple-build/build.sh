#!/usr/bin/env bash
# Rebuild docs/simple-case-build-guide.pdf from guide.html and figures.py.
set -e
cd "$(dirname "$0")"
/opt/homebrew/bin/python3 figures.py >/dev/null
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --no-pdf-header-footer --print-to-pdf-no-header \
  --print-to-pdf="../simple-case-build-guide.pdf" "file://$PWD/guide.html" 2>/dev/null
echo "wrote docs/simple-case-build-guide.pdf"
