"""Bảo đảm script chạy bằng Python trong .venv của thư mục này.
Bấm Run trong VS Code bằng Python nào cũng được: nếu chưa ở .venv, script tự chạy lại bằng .venv
và log vẫn hiện trong cùng terminal."""
import sys as _s
for _st in (_s.stdout, _s.stderr):
    try:
        _st.reconfigure(encoding="utf-8")
    except Exception:
        pass
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENV_PY = os.path.join(HERE, ".venv", "Scripts" if os.name == "nt" else "bin",
                       "python.exe" if os.name == "nt" else "python")


def ensure():
    os.chdir(HERE)
    if os.path.abspath(sys.executable).lower() == os.path.abspath(VENV_PY).lower():
        return
    if not os.path.exists(VENV_PY):
        print("Chưa có môi trường .venv. Hãy chạy 00_setup_env.py trước.", flush=True)
        sys.exit(1)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    sys.exit(subprocess.call([VENV_PY, "-u", os.path.abspath(sys.argv[0])] + sys.argv[1:], env=env))
