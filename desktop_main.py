import os
import sys
import time
import socket
import threading

# Set Windows AppUserModelID so taskbar groups properly with the app icon
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CleanApps.CleanStreamRipper.1.0")
    except Exception:
        pass

import uvicorn
import webview

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def run_server(port):
    from backend.app import app
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

def wait_for_server(port, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=0.5):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.1)
    return False

if __name__ == "__main__":
    # Locate icon path across frozen package and development layouts
    candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        mei_dir = getattr(sys, "_MEIPASS", exe_dir)
        candidates.extend([
            os.path.join(exe_dir, "icon.ico"),
            os.path.join(mei_dir, "icon.ico"),
            os.path.join(mei_dir, "frontend", "icon.ico"),
        ])
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.extend([
        os.path.join(base_dir, "icon.ico"),
        os.path.join(base_dir, "frontend", "icon.ico"),
    ])
    icon_path = next((p for p in candidates if os.path.exists(p)), None)

    port = find_free_port()

    # Start FastAPI backend in background daemon thread
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()

    # Wait until FastAPI responds
    if not wait_for_server(port):
        print(f"Failed to start backend server on port {port}")
        sys.exit(1)

    app_url = f"http://127.0.0.1:{port}"

    # Create native desktop window - compact height for zero scrolling on all screens
    window = webview.create_window(
        title="Clean Stream Ripper",
        url=app_url,
        width=740,
        height=620,
        min_size=(640, 500),
        background_color="#070913"
    )

    # Launch desktop UI
    webview.start(icon=icon_path if os.path.exists(icon_path) else None)

