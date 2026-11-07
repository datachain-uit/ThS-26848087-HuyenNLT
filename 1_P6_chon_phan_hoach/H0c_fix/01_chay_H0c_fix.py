"""Bấm Run trong VS Code. Chạy test bản sửa, rồi chạy lại H0c (đã sửa kcenter_seq) với 8 tiến trình.
Kết quả: H0c_fix_REPORT.md, results/summary/, log: logs/h0c_fix.log. Xem BUGFIX.md."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in (["test_kcenter.py"], ["h0c.py", "--workers", "8"]):
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        sys.exit(r)
