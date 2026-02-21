"""
Projeyi başlatmak için bu dosyayı çalıştır:
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
    """Sunucunun port'u dinleyip dinlemediğini kontrol eder."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def main():
    print("🚀 Career Assistant AI Agent başlatılıyor...")
    print(f"   http://localhost:{PORT}        → Demo arayüzü")
    print(f"   http://localhost:{PORT}/docs   → Swagger UI")
    print("   Durdurmak için CTRL+C\n")

    # Uvicorn sürecini başlat
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", HOST, "--port", str(PORT), "--reload"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

    # Sunucu hazır olana kadar bekle (max 15 saniye)
    print("⏳ Sunucu hazırlanıyor", end="", flush=True)
    for _ in range(30):
        if is_port_ready(HOST, PORT):
            break
        time.sleep(0.5)
        print(".", end="", flush=True)
    else:
        print("\n❌ Sunucu başlamadı. Hata için terminal çıktısını kontrol et.")
        server.terminate()
        sys.exit(1)

    print("\n✅ Sunucu hazır!\n")

    # Tarayıcıyı aç
    webbrowser.open(f"http://localhost:{PORT}")
    time.sleep(0.5)
    webbrowser.open(f"http://localhost:{PORT}/docs")

    # Sunucu kapanana kadar bekle
    try:
        server.wait()
    except KeyboardInterrupt:
        print("\n\n🛑 Sunucu kapatılıyor...")
        server.terminate()


if __name__ == "__main__":
    main()
