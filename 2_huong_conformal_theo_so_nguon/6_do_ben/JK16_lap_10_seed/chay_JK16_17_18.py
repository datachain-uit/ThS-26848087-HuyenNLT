"""Lối tắt: bấm Run (▶) để chạy nối tiếp J-K16 (10 seed) rồi J-K17 + J-K18 (lệch mô hình, ảnh chụp thiếu).
Mỗi bước tự bỏ qua phần đã xong; chạy lại được nếu bị dừng."""
import os, subprocess, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
here = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
for f in ("23_chay_JK16.py", "24_chay_JK17_18.py"):
    print(f"##### {f}", flush=True)
    rc = subprocess.call([sys.executable, "-u", os.path.join(here, f)], env=env)
    if rc != 0:
        print(f"LỖI ở {f} (mã {rc}) — dừng chuỗi.", flush=True); sys.exit(rc)
print("CHUỖI J-K16 → J-K18 HOÀN TẤT", flush=True)
