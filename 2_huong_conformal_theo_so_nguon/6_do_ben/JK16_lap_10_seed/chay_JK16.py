"""Lối tắt: bấm Run (▶) để chạy J-K16 (26_JK16_10_seed): chạy thử rồi chạy chính. Chạy lại được nếu bị dừng (tự bỏ qua phần đã xong)."""
import os, subprocess, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
here = os.path.dirname(os.path.abspath(__file__))
d = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "6_do_ben", "JK16_lap_10_seed"))
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
res = os.path.join(d, "results")
def call(*args):
    print("=== jk16.py", *args, flush=True)
    rc = subprocess.call([sys.executable, "-u", os.path.join(d, "jk16.py"), *args], env=env)
    if rc != 0:
        print(f"LỖI (mã {rc}) — dừng.", flush=True); sys.exit(rc)
if not os.path.exists(os.path.join(res, "JK16_smoke.pkl")):
    call("--smoke")
if not os.path.exists(os.path.join(res, "JK16_REPORT.md")):
    call()
open(os.path.join(res, "JK16_XONG.txt"), "w").write("hoan tat\n")
print("J-K16 HOÀN TẤT", flush=True)
