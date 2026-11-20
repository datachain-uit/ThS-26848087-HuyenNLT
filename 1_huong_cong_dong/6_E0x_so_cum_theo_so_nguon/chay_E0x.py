"""Lối tắt: bấm Run (▶) trong VS Code để chạy E0x (thư mục 6_E0x_so_cum_va_vung_dinh_danh).
Tạo 17/11/2026 vì workspace hiện tại chưa mở thư mục 6_E0x. Xóa được sau khi chạy xong.
18/11 08:10: bù đến đủ 10 seed (mức tối thiểu của plan), không đặt hạn sớm."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(here, "..", "..", "1_huong_cong_dong", "6_E0x_so_cum_theo_so_nguon", "e0x.py")
sys.exit(subprocess.call([sys.executable, "-u", os.path.abspath(target), "--seeds", "10", "--deadline", "23:59"] + sys.argv[1:]))
