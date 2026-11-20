"""Lối tắt: bấm Run (▶) để chạy J-K5 (14_JK5_MDCP): chạy thử trước, rồi chạy chính."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
f = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "3_KSU_bao_dam_theo_k", "JK5_so_sanh_MDCP", "jk5.py"))
rc = subprocess.call([sys.executable, "-u", f, "--smoke"])
sys.exit(rc if rc else subprocess.call([sys.executable, "-u", f]))
