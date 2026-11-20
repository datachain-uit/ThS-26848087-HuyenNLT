"""Bấm Run trong VS Code. Thứ tự:
  1. test_kcenter.py       — kiểm tra bản sửa k-center (phải in ĐẠT)
  2. identifiability_v2.py — kiểm tra định danh nguồn, so sánh công bằng (vài phút)
  3. h0p.py                — H0' chính thức: 16 đồ thị × 2 mô hình quan sát × 3 k × 200 cascade (~5–15 phút)
Kết quả: H0p_REPORT.md, results/summary/, results/identifiability_v2_*.csv; log: logs/h0p.log."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in (["test_kcenter.py"], ["identifiability_v2.py"], ["h0p.py"]):
    print(f"\n===== {' '.join(cmd)} =====", flush=True)
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        print(f"DỪNG: {cmd[0]} trả mã {r}", flush=True)
        sys.exit(r)
