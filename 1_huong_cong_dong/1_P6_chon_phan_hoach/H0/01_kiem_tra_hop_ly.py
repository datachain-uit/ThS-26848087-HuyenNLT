"""Bước 1: kiểm tra hợp lý trên cây + kiểm tra phụ tính định danh (seed riêng)."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in [['sanity_checks.py'], ['identifiability_check.py']]:
    print("\n>>> python " + " ".join(cmd), flush=True)
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        sys.exit(f"Dừng: lệnh trả mã lỗi {r}")
print("\n=== XONG ===", flush=True)
