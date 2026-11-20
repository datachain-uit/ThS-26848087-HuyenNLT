"""Lối tắt: bấm Run (▶) để chạy J-K17 + J-K18 (27_JK17_18_lech_va_nhieu): chạy thử rồi chạy chính. Chạy lại được nếu bị dừng."""
import os, subprocess, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
here = os.path.dirname(os.path.abspath(__file__))
d = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "6_do_ben", "JK17_18_lech_mo_hinh_thieu_nut"))
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
res = os.path.join(d, "results")
def call(*args):
    print("=== jk17.py", *args, flush=True)
    rc = subprocess.call([sys.executable, "-u", os.path.join(d, "jk17.py"), *args], env=env)
    if rc != 0:
        print(f"LỖI (mã {rc}) — dừng.", flush=True); sys.exit(rc)
if not os.path.exists(os.path.join(res, "JK17_smoke.pkl")):
    call("--smoke")
if not os.path.exists(os.path.join(res, "JK17_18_REPORT.md")):
    call()
open(os.path.join(res, "JK17_18_XONG.txt"), "w").write("hoan tat\n")
print("J-K17 + J-K18 HOÀN TẤT", flush=True)
