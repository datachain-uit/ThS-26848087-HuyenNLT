"""Lối tắt: bấm Run (▶) trong VS Code để (1) giải nén repo đã clone trong 8_tai_lap_paper, (2) chạy pilot P-K (7_PK_tap_du_doan_k)."""
import os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.join(here, "..", "..", "..")
subprocess.call([sys.executable, "-u", os.path.abspath(os.path.join(root, "2_huong_conformal_theo_so_nguon/0_tai_lap_Jian2026", "giai_nen.py"))])
if not os.path.exists(os.path.join(root, "2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK_tap_du_doan_k", "results", "PK_REPORT.md")):
    sys.exit(subprocess.call([sys.executable, "-u", os.path.abspath(os.path.join(root, "2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK_tap_du_doan_k", "pk.py"))]))
