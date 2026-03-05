@echo off
setlocal

if not exist .venv (
  py -3 -m venv .venv
)

call .venv\Scripts\activate
pip install -r requirements.txt

python scripts\generate_icon.py

pyinstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name Chess ^
  --icon assets\chess_icon.ico ^
  --add-data "templates;templates" ^
  --add-data "static;static" ^
  desktop_app.py

if exist dist\Chess.exe (
  copy /Y dist\Chess.exe Chess.exe >nul
  echo Done: Chess.exe copied to project root
) else (
  echo Build finished, but dist\Chess.exe not found
  exit /b 1
)
