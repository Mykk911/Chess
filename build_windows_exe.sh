#!/usr/bin/env bash
set -e

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

python3 scripts/generate_icon.py

pyinstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name Chess \
  --icon assets/chess_icon.ico \
  --add-data "templates:templates" \
  --add-data "static:static" \
  desktop_app.py

echo "Done. EXE: dist/Chess/Chess.exe (or dist/Chess.exe depending on PyInstaller mode)"
