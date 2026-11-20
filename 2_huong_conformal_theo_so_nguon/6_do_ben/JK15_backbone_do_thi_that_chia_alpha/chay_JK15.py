"""Lối tắt: bấm Run (▶) để chạy J-K15 (25_JK15_do_ben): chạy thử A, B (kiểm cài đặt) rồi chạy chính A, B.
Bước nào đã có báo cáo thì bỏ qua; chạy lại được nếu bị dừng giữa chừng (kết quả từng cấu hình đã lưu)."""
import os, subprocess, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
here = os.path.dirname(os.path.abspath(__file__))
d = os.path.abspath(os.path.join(here, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "6_do_ben", "JK15_backbone_do_thi_that_chia_alpha"))
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
def call(script, *a):
    print(f"=== {script} {' '.join(a)}", flush=True)
    rc = subprocess.call([sys.executable, "-u", os.path.join(d, script), *a], env=env)
    if rc != 0:
        print(f"LỖI ở {script} {a} (mã {rc}) — dừng.", flush=True); sys.exit(rc)
res = os.path.join(d, "results")
if not os.path.exists(os.path.join(res, "JK15A_smoke.txt")):
    call("jk15a.py", "--smoke")
if not os.path.exists(os.path.join(res, "JK15B_smoke.txt")):
    call("jk15b.py", "--smoke")
if not os.path.exists(os.path.join(res, "JK15A_REPORT.md")):
    call("jk15a.py")
if not os.path.exists(os.path.join(res, "JK15B_REPORT.md")):
    call("jk15b.py")
open(os.path.join(res, "JK15_XONG.txt"), "w").write("hoan tat\n")
print("J-K15 HOÀN TẤT", flush=True)
