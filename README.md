# Chess (2D UI)

Ты прав: некоторые платформы/хранилища ругаются на бинарные файлы в репозитории.
Поэтому иконка теперь **не хранится как бинарник в git**, а генерируется локально перед сборкой.

## Что является desktop-приложением

`desktop_app.py` — desktop-обёртка (отдельное окно c названием **Chess**).

## Запуск как desktop (без `.exe`)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 desktop_app.py
```

## Сборка Windows `.exe` (Chess)

```bash
./build_windows_exe.sh
```

Скрипт сам:
1. ставит зависимости,
2. генерирует `assets/chess_icon.ico`,
3. собирает `Chess.exe` через PyInstaller.

Бинарные иконки (`.ico/.png`) в репозитории не хранятся.

## Запуск в браузере (альтернатива)

```bash
python3 app.py
```

Открыть: `http://127.0.0.1:8000`
