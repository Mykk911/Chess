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
  --onefile \
  --windowed \
  --name Chess \
  --icon assets/chess_icon.ico \
  --add-data "templates:templates" \
  --add-data "static:static" \
  desktop_app.py

if [ -f "dist/Chess.exe" ]; then
  cp dist/Chess.exe Chess.exe
  echo "Done: Chess.exe copied to project root"
else
  echo "Build finished, but dist/Chess.exe not found. Check dist/ folder."
  exit 1
fi
