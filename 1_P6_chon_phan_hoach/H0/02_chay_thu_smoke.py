"""Bước 2: chạy thử nhỏ (seed riêng 9999), đo thời gian, kiểm tra tất định. Không dùng cho H-a."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in [['run_h0.py', '--smoke'], ['analyze_h0.py', '--smoke']]:
    print("\n>>> python " + " ".join(cmd), flush=True)
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        sys.exit(f"Dừng: lệnh trả mã lỗi {r}")
print("\n=== XONG ===", flush=True)
