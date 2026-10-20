#!/usr/bin/env bash
# Rebuild docs/mounting-and-case-plan.pdf from plan.html and figures.py.
set -e
cd "$(dirname "$0")"
/opt/homebrew/bin/python3 figures.py
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --no-pdf-header-footer --print-to-pdf-no-header \
  --print-to-pdf="../mounting-and-case-plan.pdf" "file://$PWD/plan.html" 2>/dev/null
echo "wrote docs/mounting-and-case-plan.pdf"
