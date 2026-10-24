#!/usr/bin/env python3
"""
Dashboard Launcher for Autonomous Closed-Loop Orchestration Pipeline
Starts the FastAPI web server strictly on a free port (default: 8088, NEVER 8000/3000)
and opens the browser automatically.
"""

import os
import sys
import time
import socket
import webbrowser
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uvicorn

FORBIDDEN_PORTS = {3000, 8000}

def is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    """Returns True if the port is free to bind."""
    if port in FORBIDDEN_PORTS:
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) != 0

def find_available_port(preferred: int = 8088, host: str = "127.0.0.1") -> int:
    """Finds an available port, strictly avoiding 8000, 3000, etc."""
    if is_port_free(preferred, host):
        return preferred
    for p in range(8089, 8150):
        if is_port_free(p, host):
            return p
    return 8088

def main():
    host = os.environ.get("HOST", "127.0.0.1")
    env_port = os.environ.get("PORT")

    if env_port and int(env_port) not in FORBIDDEN_PORTS:
        port = int(env_port)
    else:
        port = find_available_port(preferred=8088, host=host)

    url = f"http://localhost:{port}"

    print("=" * 80)
    print("  AUTONOMOUS CLOSED-LOOP ORCHESTRATION PIPELINE - WEB DASHBOARD")
    print("=" * 80)
    print(f"[*] Dashboard Port: {port} (Ports 8000 and 3000 are excluded)")
    print(f"[*] Starting local server on: {url}")
    print("[*] Press Ctrl+C in this terminal to stop the server.")
    print("=" * 80)

    # Launch browser after a short delay in background thread
    def open_browser():
        time.sleep(1.2)
        try:
            webbrowser.open(url)
            print(f"[✓] Opened dashboard in default browser: {url}")
        except Exception:
            pass

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI / Uvicorn server with hot reload
    uvicorn.run("dashboard_server:app", host=host, port=port, reload=True, log_level="info")

if __name__ == "__main__":
    main()
