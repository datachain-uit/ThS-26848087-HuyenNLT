"""Bước 3: chạy lại 5 baseline trên dữ liệu ĐÃ VÁ (xem run_baselines_va.py). Trừ IVGD-NetScience (Colab)."""
import _venv; _venv.ensure()
import subprocess, sys
r = subprocess.call([sys.executable, "-u", "run_baselines_va.py"])
print("\n=== XONG ===" if r == 0 else f"Dừng: mã lỗi {r}", flush=True)
