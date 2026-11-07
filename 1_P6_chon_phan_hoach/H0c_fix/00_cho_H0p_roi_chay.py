"""Bấm Run một lần rồi để máy chạy qua đêm.
Chờ H0p xong (log có dòng '=== H0p XONG ===') rồi tự chạy 01_chay_H0c_fix.py.
Nếu log H0p không cập nhật quá 45 phút (H0p bị dừng/lỗi), vẫn chạy tiếp H0c_fix.
Nhật ký: logs/cho_H0p.log"""
import _venv; _venv.ensure()
import os, sys, time, subprocess, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
H0P_LOG = os.path.join(HERE, "..", "H0p", "logs", "h0p.log")
os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)

def log(m):
    line = f"[{dt.datetime.now():%H:%M:%S}] {m}"
    print(line, flush=True)
    open(os.path.join(HERE, "logs", "cho_H0p.log"), "a", encoding="utf-8").write(line + "\n")

log("Bắt đầu chờ H0p...")
while True:
    txt = open(H0P_LOG, encoding="utf-8").read() if os.path.exists(H0P_LOG) else ""
    if "=== H0p XONG ===" in txt:
        log("H0p đã xong.")
        break
    idle = (time.time() - os.path.getmtime(H0P_LOG)) / 60 if os.path.exists(H0P_LOG) else 0
    if idle > 45:
        log(f"CẢNH BÁO: log H0p không đổi {idle:.0f} phút (có thể đã dừng). Vẫn chạy H0c_fix.")
        break
    time.sleep(60)
time.sleep(30)
log("Chạy 01_chay_H0c_fix.py ...")
r = subprocess.call([sys.executable, "-u", os.path.join(HERE, "01_chay_H0c_fix.py")])
log(f"H0c_fix kết thúc, mã trả về {r}.")
