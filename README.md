# Chess (2D UI)

Ты прав: `exe` не лежит в репозитории заранее.
Он создаётся локально у тебя на ПК после сборки.

## Где теперь будет `.exe`

После сборки файл появится **прямо в корне проекта**:

- `Chess.exe` (рядом с `app.py`)

## Сборка `Chess.exe` на Windows (самый простой способ)

Запусти двойным кликом:

- `build_windows_exe.bat`

или в консоли:

```bat
build_windows_exe.bat
```

## Сборка через Git Bash / WSL

```bash
./build_windows_exe.sh
```

## Desktop запуск без сборки exe

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 desktop_app.py
```

## Важно

- Бинарные файлы (`.exe`, `.ico`, `.png`) не коммитятся в git.
- Они генерируются локально скриптами.
