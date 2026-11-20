"""Lối tắt: bấm Run (▶) để chạy J-K6 (15_JK6_lech_prior): chạy thử trước, rồi chạy chính."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
f = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "3_KSU_bao_dam_theo_k", "JK6_lech_prior", "jk6.py"))
rc = subprocess.call([sys.executable, "-u", f, "--smoke"])
sys.exit(rc if rc else subprocess.call([sys.executable, "-u", f]))
