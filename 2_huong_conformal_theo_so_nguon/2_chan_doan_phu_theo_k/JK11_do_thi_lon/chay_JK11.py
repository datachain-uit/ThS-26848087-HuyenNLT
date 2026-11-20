"""Lối tắt: bấm Run (▶) để chạy J-K11 (20_JK11_do_thi_lon): chạy thử (có kiểm tra cài đặt) trước, rồi chạy chính."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
f = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "2_chan_doan_phu_theo_k", "JK11_do_thi_lon", "jk11.py"))
rc = subprocess.call([sys.executable, "-u", f, "--smoke"])
sys.exit(rc if rc else subprocess.call([sys.executable, "-u", f]))
