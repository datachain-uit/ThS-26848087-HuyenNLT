"""Lối tắt: bấm Run (▶) để chạy J-K10 (19_JK10_tong_quat): chạy thử (có kiểm tra cài đặt) trước, rồi chạy chính."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
f = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "2_chan_doan_phu_theo_k", "JK10_tong_quat_mo_phong", "jk10.py"))
rc = subprocess.call([sys.executable, "-u", f, "--smoke"])
sys.exit(rc if rc else subprocess.call([sys.executable, "-u", f]))
