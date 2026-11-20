"""Lối tắt: bấm Run (▶) để chạy J-K3 (12_JK3_do_ben)."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.exit(subprocess.call([sys.executable, "-u", os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "2_chan_doan_phu_theo_k", "JK3_do_ben_theo_pow", "jk3.py"))]))
