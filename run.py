import os
import sys
import socket
import uvicorn

def get_local_ip():
    """Retrieve local LAN IP for easy mobile phone access."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't need to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = 8000

    print("=" * 60)
    print("   CLEAN STREAM RIPPER")
    print("   Desktop & Mobile Web App")
    print("=" * 60)
    print(f" * Local Desktop URL:  http://localhost:{port}")
    print(f" * Mobile Phone URL:   http://{local_ip}:{port}")
    print("=" * 60)
    print("Tip: On your mobile phone browser, open the Mobile URL")
    print("and tap 'Install' or 'Add to Home Screen' for 1-tap ripping!")
    print("=" * 60)

    uvicorn.run("backend.app:app", host="0.0.0.0", port=port, reload=True)
