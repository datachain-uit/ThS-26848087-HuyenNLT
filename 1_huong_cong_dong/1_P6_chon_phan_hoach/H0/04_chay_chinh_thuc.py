"""Bước 4: chạy H0 chính thức (seed 2026). Cần máy bật suốt thời gian chạy."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in [['run_h0.py']]:
    print("\n>>> python " + " ".join(cmd), flush=True)
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        sys.exit(f"Dừng: lệnh trả mã lỗi {r}")
print("\n=== XONG ===", flush=True)
