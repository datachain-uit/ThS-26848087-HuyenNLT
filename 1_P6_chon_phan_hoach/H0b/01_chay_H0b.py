"""Chạy H0b (thăm dò 9 ô) với 8 tiến trình, rồi phân tích và viết H0b_REPORT.md. Dùng chung .venv của thư mục H0."""
import _venv; _venv.ensure()
import subprocess, sys
r = subprocess.call([sys.executable, "-u", "h0b.py", "--workers", "8"])
print("\n=== XONG ===" if r == 0 else f"Dừng: mã lỗi {r}", flush=True)
