"""Lối tắt: bấm Run (▶) để chạy J-K19b (2_huong_conformal_theo_so_nguon/7_KSU_mk_ho_co_che/JK19_JK19b/jk19b.py): chạy thử rồi chạy chính."""
import os, subprocess, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
here = os.path.dirname(os.path.abspath(__file__))
d = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "7_KSU_mk_ho_co_che", "JK19_JK19b"))
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
res = os.path.join(d, "results")
def call(*args):
    print("=== jk19b.py", *args, flush=True)
    rc = subprocess.call([sys.executable, "-u", os.path.join(d, "jk19b.py"), *args], env=env)
    if rc != 0:
        print(f"LỖI (mã {rc}) — dừng.", flush=True); sys.exit(rc)
if not os.path.exists(os.path.join(res, "JK19b_smoke.pkl")):
    call("--smoke")
if not os.path.exists(os.path.join(res, "JK19b_REPORT.md")):
    call()
open(os.path.join(res, "JK19b_XONG.txt"), "w").write("hoan tat\n")
print("J-K19b HOÀN TẤT", flush=True)
