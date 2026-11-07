"""Bước 2 (chạy trên máy, sau khi DỪNG 01 lúc nó bắt đầu IVGD trên NetScience):
  (1) SL-VAE trên NetScience (01 chưa kịp chạy vì IVGD đứng trước);
  (2) GCNSI các chế độ chọn tập nguồn trên Karate, Jazz, NetScience (gcnsi_modes.py).
IVGD trên NetScience chạy trên Colab GPU (colab/IVGD_netscience_colab.ipynb)."""
import _venv; _venv.ensure()
import subprocess, sys
for cmd in [["run_baselines.py", "--datasets", "netscience", "--methods", "SLVAE"], ["gcnsi_modes.py"]]:
    print("\n>>> python " + " ".join(cmd), flush=True)
    r = subprocess.call([sys.executable, "-u"] + cmd)
    if r != 0:
        sys.exit(f"Dừng: lệnh trả mã lỗi {r}")
print("\n=== XONG ===", flush=True)
