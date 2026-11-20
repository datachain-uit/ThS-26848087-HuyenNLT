"""Bấm Run (▶) trong VS Code. Chạy chẩn đoán trước khi khóa P6-F (chan_doan_truoc_khoa.py): D1 Đề xuất B,
D2 nguyên nhân V1 trượt, D3 lpsi_r. Chỉ bộ định vị KHÔNG cộng đồng, seed riêng 7171. KHÔNG phải P6-F chính thức.
Log: logs/chan_doan.log. Kết quả: results/chan_doan/, CHAN_DOAN.md. Dùng chung .venv của H0."""
import _venv; _venv.ensure()
import subprocess, sys
print("\n===== chan_doan_truoc_khoa.py =====", flush=True)
r = subprocess.call([sys.executable, "-u", "chan_doan_truoc_khoa.py"])
print(f"\n===== KẾT THÚC (mã {r}). Mở CHAN_DOAN.md để xem bảng. =====", flush=True)
sys.exit(r)
