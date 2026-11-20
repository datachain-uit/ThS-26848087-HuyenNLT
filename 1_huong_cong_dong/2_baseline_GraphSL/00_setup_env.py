"""Bước 0: tạo .venv, cài thư viện từ requirements.txt, ghi requirements.lock.txt (pin phiên bản).
Chỉ dùng thư viện chuẩn, chạy được bằng Python hệ thống (bấm Run trong VS Code)."""
import sys as _s
for _st in (_s.stdout, _s.stderr):
    try:
        _st.reconfigure(encoding="utf-8")
    except Exception:
        pass
import os
import subprocess
import sys
import venv

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
py = os.path.join(HERE, ".venv", "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")
print(f"Python hệ thống: {sys.version.split()[0]} ({sys.executable})", flush=True)
if sys.version_info < (3, 9):
    sys.exit("Cần Python >= 3.9")
if not os.path.exists(py):
    print("Tạo .venv ...", flush=True)
    venv.create(".venv", with_pip=True)
subprocess.check_call([py, "-m", "pip", "install", "--upgrade", "pip"])
subprocess.check_call([py, "-m", "pip", "install", "-r", "requirements.txt"])
frz = subprocess.check_output([py, "-m", "pip", "freeze"], text=True)
open("requirements.lock.txt", "w", encoding="utf-8").write(frz)
print(frz)
print("XONG: môi trường .venv đã sẵn sàng; phiên bản ghi trong requirements.lock.txt", flush=True)
