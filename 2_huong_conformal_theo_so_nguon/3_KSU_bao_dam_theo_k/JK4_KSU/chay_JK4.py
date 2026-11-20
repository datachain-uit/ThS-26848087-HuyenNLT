"""Lối tắt: bấm Run (▶) để chạy J-K4 (13_JK4_bao_dam)."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.exit(subprocess.call([sys.executable, "-u", os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "3_KSU_bao_dam_theo_k", "JK4_KSU", "jk4.py"))]))
