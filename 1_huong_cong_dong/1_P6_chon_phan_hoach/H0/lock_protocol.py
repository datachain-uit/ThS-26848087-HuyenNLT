"""Khóa giao thức: ghi SHA-256 của H0_PROTOCOL.md và config.py trước khi sinh dữ liệu lượt chính."""
import _venv; _venv.ensure()
import datetime as dt
import h0lib as L

lines = [f"{L.sha256_file(f)}  {f}" for f in ["H0_PROTOCOL.md", "config.py", "h0lib.py", "run_h0.py", "analyze_h0.py", "sanity_checks.py"]]
with open("H0_PROTOCOL.sha256", "w", encoding="utf-8") as f:
    f.write(f"# Khóa lúc {dt.datetime.now().isoformat(timespec='seconds')}\n" + "\n".join(lines) + "\n")
print("\n".join(lines))
print("Đã khóa giao thức -> H0_PROTOCOL.sha256")
