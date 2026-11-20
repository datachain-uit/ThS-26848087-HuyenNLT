"""Bấm Run (▶) trong VS Code. Chạy bước HIỆU CHỈNH f của P6-F (trước khi khóa giao thức; Review 07/11 Mục 7.1, 7.5).
Chỉ dùng bộ định vị KHÔNG cộng đồng và hai mốc sàn. KHÔNG phải lượt chạy P6-F chính thức.
Log hiện ngay trong terminal này và lưu ở logs/hieu_chinh_f.log. Dùng chung .venv của H0.
Kết quả: HIEU_CHINH_F.md, results/V3_table.csv, results/V3_theo_tang.csv, results/f_chon.json."""
import _venv; _venv.ensure()
import datetime as dt
import os
import shutil
import subprocess
import sys

MARK = ".da_chay_tren_windows"
OLD = "_ban_chay_thu_may_ao"
if not os.path.exists(MARK):
    # Kết quả có sẵn (nếu có) là từ lượt chạy thử trên máy ảo Linux, khác phiên bản thư viện → dời đi, chạy lại từ đầu.
    cu = [p for p in ("results", "logs", "HIEU_CHINH_F.md") if os.path.exists(p)]
    if cu:
        os.makedirs(OLD, exist_ok=True)
        for p in cu:
            shutil.move(p, os.path.join(OLD, p))
        print(f"Đã dời kết quả chạy thử cũ ({', '.join(cu)}) sang {OLD}/ — có thể xóa thư mục này.", flush=True)
    open(MARK, "w", encoding="utf-8").write(f"Lượt chạy đầu trên Windows: {dt.datetime.now():%Y-%m-%d %H:%M:%S}\n")

print("\n===== hieu_chinh_f.py =====", flush=True)
r = subprocess.call([sys.executable, "-u", "hieu_chinh_f.py"])
print(f"\n===== KẾT THÚC (mã {r}). Mở HIEU_CHINH_F.md để xem bảng. =====", flush=True)
sys.exit(r)
