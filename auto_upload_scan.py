import os
import time
import requests
from pathlib import Path
from datetime import datetime

# === KONFIGURASI ===
FOLDER_SCAN = Path("C:/ScanMasuk")
FOLDER_UPLOAD_SUCCESS = FOLDER_SCAN / "uploaded"
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg'}
UPLOAD_URL = "http://192.168.100.79:8000/scan-upload/" # Ganti sesuai domain lokal

# Buat folder "uploaded" jika belum ada
FOLDER_UPLOAD_SUCCESS.mkdir(parents=True, exist_ok=True)

def log(status, message):
    """Print log dengan timestamp dan ikon status."""
    icons = {
        "success": "✅",
        "error": "❌",
        "info": "ℹ️",
        "warning": "⚠️",
    }
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {icons.get(status, '')} {message}")

def upload_file(file_path: Path) -> bool:
    """Upload satu file ke server."""
    try:
        with file_path.open('rb') as f:
            files = {'file': (file_path.name, f)}
            response = requests.post(UPLOAD_URL, files=files)

        if response.status_code == 200:
            log("success", f"Berhasil upload: {file_path.name}")
            return True
        else:
            log("error", f"Gagal upload ({response.status_code}): {file_path.name}")
            return False

    except requests.exceptions.ConnectionError:
        log("warning", "Tidak dapat terhubung ke server. Pastikan server aktif.")
        return False
    except Exception as e:
        log("error", f"Error saat upload {file_path.name}: {e}")
        return False

def pantau_folder():
    """Pantau folder untuk file baru dan upload otomatis."""
    log("info", f"Memantau folder: {FOLDER_SCAN}")

    while True:
        for file_path in FOLDER_SCAN.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                success = upload_file(file_path)
                if success:
                    destination = FOLDER_UPLOAD_SUCCESS / file_path.name
                    file_path.rename(destination)
        time.sleep(5)

if __name__ == "__main__":
    pantau_folder()
