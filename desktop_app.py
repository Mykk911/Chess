import threading
import time

import webview

from app import app


def run_server() -> None:
    app.run(host="127.0.0.1", port=8000, debug=False, use_reloader=False)


def main() -> None:
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    time.sleep(1)
    webview.create_window("Chess", "http://127.0.0.1:8000", width=920, height=760)
    webview.start()


if __name__ == "__main__":
    main()
