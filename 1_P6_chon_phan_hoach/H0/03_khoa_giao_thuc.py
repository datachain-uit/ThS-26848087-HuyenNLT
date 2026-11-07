"""Bước 3: khóa giao thức (SHA-256) — chỉ chạy sau khi học viên chốt H0_PROTOCOL.md."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in [['lock_protocol.py']]:
    print("\n>>> python " + " ".join(cmd), flush=True)
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        sys.exit(f"Dừng: lệnh trả mã lỗi {r}")
print("\n=== XONG ===", flush=True)
