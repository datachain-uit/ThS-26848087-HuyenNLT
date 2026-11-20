"""Bước 5: phân tích H-a, H-b và sinh BAO_CAO_H0.md từ kết quả máy vừa chạy."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in [['analyze_h0.py']]:
    print("\n>>> python " + " ".join(cmd), flush=True)
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        sys.exit(f"Dừng: lệnh trả mã lỗi {r}")
print("\n=== XONG ===", flush=True)
