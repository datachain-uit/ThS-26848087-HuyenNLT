"""Bước 1: chạy LPSI, NetSleuth, GCNSI, IVGD, SL-VAE trên Karate, Jazz, NetScience."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in [["run_baselines.py"]]:
    print("\n>>> python " + " ".join(cmd), flush=True)
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        sys.exit(f"Dừng: lệnh trả mã lỗi {r}")
print("\n=== XONG ===", flush=True)
