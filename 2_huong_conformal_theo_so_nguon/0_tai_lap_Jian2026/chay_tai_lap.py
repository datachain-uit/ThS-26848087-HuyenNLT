"""Lối tắt: bấm Run (▶) để tái lập phần conformal của Jian et al. (AAAI 2026) trên highSchool, cấu hình randomSIR 'Slow', pow_expected 0.3,
50 lần lặp, các phương pháp set_recall / set_prec / set_min (bỏ ArbiTree vì ~270 s mỗi lần lặp).
So với log của tác giả: logfiles/runCPhighSchoolSlowpow3.log (trong logfiles_tacgia.tgz). Kết quả: 2_huong_conformal_theo_so_nguon/0_tai_lap_Jian2026/TAI_LAP_CONFORMAL.md"""
import os, re, subprocess, sys, tarfile
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, "..", ".."))
cn = os.path.join(root, "2_huong_conformal_theo_so_nguon/0_tai_lap_Jian2026", "cnsd")
py = os.path.join(root, "1_huong_cong_dong/1_P6_chon_phan_hoach", "H0", ".venv", "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")
for m in ("pandas", "matplotlib", "networkx", "scipy", "sklearn"):
    if subprocess.call([py, "-c", f"import {m}"]) != 0:
        subprocess.call([py, "-m", "pip", "install", "scikit-learn" if m == "sklearn" else m])
if not os.path.exists(os.path.join(cn, "logfiles")):
    with tarfile.open(os.path.join(cn, "logfiles_tacgia.tgz")) as t:
        t.extractall(cn)
os.makedirs(os.path.join(cn, "logfiles_repro"), exist_ok=True)
log = os.path.join(cn, "logfiles_repro", "runCPhighSchoolSlowpow3_repro.log")
args = ["--graph", "highSchool", "--train_exp_name", "SIR_nsrc1-15_Rzero1-15_gamma0.1-0.4_ls21200_nf16",
        "--test_exp_name", "SIR_nsrc1-15_Rzero1-15_gamma0.1-0.4_ls8000_nf16", "--pow_expected", "0.3", "--prop_model", "SIR",
        "--set_recall", "1", "--set_prec", "1", "--set_min", "1", "--mc_runs", "50"]
print("running reproduction (a few minutes)...", flush=True)
with open(log, "w", encoding="utf-8") as fh:
    rc = subprocess.call([py, "-u", os.path.join(cn, "repro_runner.py")] + args, stdout=fh, stderr=subprocess.STDOUT,
                         env=dict(os.environ, PYTHONIOENCODING="utf-8"))
def table(path):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    out = {}
    for sec in ("Coverage", "Set Size"):
        blk = txt.split(sec + " Results:")[-1].split("Results:")[0]
        for m in ("set_recall", "set_prec", "set_min"):
            r = re.search(m + r"\s*([\d.]+ ± [\d.]+)\s+([\d.]+ ± [\d.]+)\s+([\d.]+ ± [\d.]+)", blk)
            if r:
                out[(sec, m)] = r.group(3)  # cột α = 0,10
    return out
A = table(os.path.join(cn, "logfiles", "runCPhighSchoolSlowpow3.log"))
B = table(log) if rc == 0 else {}
L = ["# Tái lập Jian et al. (AAAI 2026) — conformal multi-source detection", "",
     "highSchool, randomSIR 'Slow' (R0 1–15, γ 0,1–0,4, 1–15 nguồn), pow_expected 0,3, 50 lần lặp, α = 0,10. "
     "Dùng đầu ra GNN (SD-STGCN) tác giả đã tính sẵn; chỉ tái lập phần conformal. Commit repo: xem COMMITS.txt.", "",
     f"Mã thoát: {rc}. Log: `cnsd/logfiles_repro/runCPhighSchoolSlowpow3_repro.log`", "",
     "| Phương pháp | Độ phủ (tác giả) | Độ phủ (tái lập) | Kích thước tập (tác giả) | Kích thước tập (tái lập) |", "|---|---|---|---|---|"]
for m in ("set_recall", "set_prec", "set_min"):
    L.append(f"| {m} | {A.get(('Coverage', m), '—')} | {B.get(('Coverage', m), '—')} | {A.get(('Set Size', m), '—')} | {B.get(('Set Size', m), '—')} |")
open(os.path.join(root, "2_huong_conformal_theo_so_nguon/0_tai_lap_Jian2026", "TAI_LAP_CONFORMAL.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("done: 2_huong_conformal_theo_so_nguon/0_tai_lap_Jian2026/TAI_LAP_CONFORMAL.md", flush=True)
