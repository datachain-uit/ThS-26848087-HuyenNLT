"""Lối tắt: bấm Run (▶) để chạy J-K7 (16_JK7_KNCP): chạy thử (có kiểm tra cài đặt) trước, rồi chạy chính."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
f = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "4_gia_cua_bao_dam", "JK7_KNCP", "jk7.py"))
rc = subprocess.call([sys.executable, "-u", f, "--smoke"])
sys.exit(rc if rc else subprocess.call([sys.executable, "-u", f]))
