"""Lối tắt: bấm Run (▶) để chạy chuỗi kiểm tra độc lập (24_KIEM_TRA): V1 -> V2 -> V3. Bước nào đã có kết quả thì bỏ qua."""
import os, subprocess, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
D = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "2_huong_conformal_theo_so_nguon", "8_kiem_tra_doc_lap"))
def has(f, key):
    p = os.path.join(D, f); return os.path.exists(p) and key in open(p, encoding="utf-8").read()
steps = [("v1_tac_gia.py", "V1_KET_QUA.txt", "bkFratB"), ("v2_mo_phong.py", "V2_KET_QUA.txt", "KSU*"), ("v3_K_gop.py", "V3_KET_QUA.txt", "Spearman")]
for script, out, key in steps:
    if has(out, key):
        print(f"bỏ qua {script} (đã có kết quả)", flush=True); continue
    if os.path.exists(os.path.join(D, out)):
        os.remove(os.path.join(D, out))  # kết quả dở dang: chạy lại từ đầu bước này
    print(f"chạy {script} ...", flush=True)
    rc = subprocess.call([sys.executable, "-u", os.path.join(D, script)], cwd=D, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if rc:
        print(f"LỖI ở {script} (mã {rc})", flush=True); sys.exit(rc)
open(os.path.join(D, "CHUOI_XONG.txt"), "w", encoding="utf-8").write("hoan tat\n")
print("HOÀN TẤT CHUỖI KIỂM TRA", flush=True)
