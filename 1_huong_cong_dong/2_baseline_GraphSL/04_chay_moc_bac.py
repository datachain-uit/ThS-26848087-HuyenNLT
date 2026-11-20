"""Bước 4: mốc so sánh "đoán theo bậc" trên dữ liệu gốc (lỗi) và bản vá — vài phút."""
import _venv; _venv.ensure()
import subprocess, sys
r = subprocess.call([sys.executable, "-u", "degree_baseline.py"])
print("\n=== XONG ===" if r == 0 else f"Dừng: mã lỗi {r}", flush=True)
