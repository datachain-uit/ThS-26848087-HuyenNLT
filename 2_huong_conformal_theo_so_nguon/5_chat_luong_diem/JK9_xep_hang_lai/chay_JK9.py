"""Lối tắt: bấm Run (▶) để chạy J-K9 (18_JK9_xep_hang_lai): chạy thử (có kiểm tra cài đặt) trước, rồi chạy chính."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
f = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "5_chat_luong_diem", "JK9_xep_hang_lai", "jk9.py"))
rc = subprocess.call([sys.executable, "-u", f, "--smoke"])
sys.exit(rc if rc else subprocess.call([sys.executable, "-u", f]))
