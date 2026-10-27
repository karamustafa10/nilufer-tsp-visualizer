"""Yerel HTTP sunucusu + tarayicida tam ekran acilis."""

from __future__ import annotations

import http.server
import socketserver
import threading
import time
import webbrowser
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def _open_browser(url: str) -> None:
    """Mumkunse Edge/Chrome tam ekran; degilse varsayilan tarayici."""
    candidates = [
        [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            f"--start-fullscreen",
            url,
        ],
        [
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            "--start-fullscreen",
            url,
        ],
        [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "--start-fullscreen",
            url,
        ],
        [
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "--start-fullscreen",
            url,
        ],
    ]
    import subprocess

    for cmd in candidates:
        exe = Path(cmd[0])
        if exe.exists():
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"Tarayici acildi (tam ekran): {exe.name}")
                return
            except OSError:
                continue
    webbrowser.open(url)
    print("Varsayilan tarayici acildi (Tam Ekran butonunu kullanin).")


def serve_and_open(port: int = 8765, open_browser: bool = True) -> socketserver.TCPServer:
    # Port doluysa sonraki portlari dene
    httpd = None
    for p in range(port, port + 20):
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", p), QuietHandler)
            port = p
            break
        except OSError:
            continue
    if httpd is None:
        raise RuntimeError("Uygun port bulunamadi.")

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{port}/index.html"
    print(f"Web arayuzu: {url}")
    if open_browser:
        time.sleep(0.4)
        _open_browser(url)
    return httpd
