#!/bin/sh
# Builds phone.pdf (A5 pages in reading order) and print.pdf (A4 booklet sheets).
# Print print.pdf double-sided, flip on short edge, then fold and staple.
set -e
cd "$(dirname "$0")"
CHROME=$(ls ~/Library/Caches/ms-playwright/chromium_headless_shell-*/chrome-headless-shell-mac-arm64/chrome-headless-shell | tail -1)
FLAGS="--headless --no-pdf-header-footer --virtual-time-budget=8000 --run-all-compositor-stages-before-draw"
"$CHROME" $FLAGS --print-to-pdf=phone.pdf "file://$PWD/index.html" 2>/dev/null
"$CHROME" $FLAGS --print-to-pdf=print.pdf "file://$PWD/index.html?booklet" 2>/dev/null
echo "built phone.pdf and print.pdf"
OVER=$("$CHROME" --headless --virtual-time-budget=8000 --dump-dom "file://$PWD/index.html" 2>/dev/null | grep -c 'data-overflow="yes"' || true)
echo "pages overflowing: $OVER"
