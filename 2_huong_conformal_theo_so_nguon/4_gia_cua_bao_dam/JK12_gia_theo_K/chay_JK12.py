"""Lối tắt: bấm Run (▶) để chạy J-K12 (21_JK12_gia_theo_K): chạy thử trước, rồi chạy chính."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
f = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "4_gia_cua_bao_dam", "JK12_gia_theo_K", "jk12.py"))
rc = subprocess.call([sys.executable, "-u", f, "--smoke"])
sys.exit(rc if rc else subprocess.call([sys.executable, "-u", f]))
