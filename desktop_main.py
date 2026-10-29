import os
import sys
import time
import socket
import threading
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
    # Locate icon path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(base_dir, "frontend", "icon.ico")

    port = find_free_port()

    # Start FastAPI backend in background daemon thread
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()

    # Wait until FastAPI responds
    if not wait_for_server(port):
        print(f"Failed to start backend server on port {port}")
        sys.exit(1)

    app_url = f"http://127.0.0.1:{port}"

    # Create native desktop window
    window = webview.create_window(
        title="Clean Stream Ripper",
        url=app_url,
        width=780,
        height=860,
        min_size=(540, 640),
        background_color="#070913"
    )

    # Launch desktop UI
    webview.start(icon=icon_path if os.path.exists(icon_path) else None)

