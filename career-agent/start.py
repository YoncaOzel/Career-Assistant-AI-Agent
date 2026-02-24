"""
Run this file to start the project:
    python start.py
"""

import subprocess
import sys
import time
import webbrowser
import socket
import os

HOST = "127.0.0.1"
PORT = 8080


def is_port_ready(host: str, port: int) -> bool:
    """Checks whether the server is listening on the given port."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def main():
    print("🚀 Career Assistant AI Agent starting...")
    print(f"   http://localhost:{PORT}        → Main UI")
    print(f"   http://localhost:{PORT}/docs   → Swagger UI")
    print("   Press CTRL+C to stop\n")

    # Start the Uvicorn process
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", HOST, "--port", str(PORT), "--reload"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    # Wait until the server is ready (max 15 seconds)
    print("⏳ Server starting", end="", flush=True)
    for _ in range(30):
        if is_port_ready(HOST, PORT):
            break
        time.sleep(0.5)
        print(".", end="", flush=True)
    else:
        print("\n❌ Server failed to start. Check terminal output for errors.")
        server.terminate()
        sys.exit(1)

    print("\n✅ Server ready!\n")

    # Open the browser
    webbrowser.open(f"http://localhost:{PORT}")
    time.sleep(0.5)
    webbrowser.open(f"http://localhost:{PORT}/docs")

    # Sunucu kapanana kadar bekle
    try:
        server.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down server...")
        server.terminate()


if __name__ == "__main__":
    main()
