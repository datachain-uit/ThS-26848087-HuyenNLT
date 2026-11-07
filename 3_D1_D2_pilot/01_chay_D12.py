"""Bấm Run trong VS Code. Thứ tự:
  1. test_kcenter.py   — kiểm tra k-center đã sửa (phải in ĐẠT)
  2. d12.py --smoke    — chạy rất nhỏ để kiểm code (thư mục smoke/, không dùng kết luận)
  3. d12.py            — pilot chính thức: khóa D12_PLAN.md + code, chạy D1 (40 việc) + D2 (8 việc), viết D12_REPORT.md
Log: logs/d12.log. Dùng chung .venv của H0."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in (["test_kcenter.py"], ["d12.py", "--smoke"], ["d12.py"]):
    print(f"\n===== {' '.join(cmd)} =====", flush=True)
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        print(f"DỪNG: {cmd[0]} trả mã {r}", flush=True)
        sys.exit(r)
