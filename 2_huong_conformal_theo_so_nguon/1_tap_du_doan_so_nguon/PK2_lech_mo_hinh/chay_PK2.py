"""Lối tắt: bấm Run (▶) để chạy P-K2 (9_PK2_lech_mo_hinh). Chạy lại được nếu bị ngắt."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.exit(subprocess.call([sys.executable, "-u", os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "1_tap_du_doan_so_nguon", "PK2_lech_mo_hinh", "pk2.py"))] + sys.argv[1:]))
