"""Lối tắt: bấm Run (▶) để chạy pilot J-K (10_JK_dieu_kien_theo_k)."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.exit(subprocess.call([sys.executable, "-u", os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "2_chan_doan_phu_theo_k", "JK1_phu_theo_k", "jk.py"))]))
