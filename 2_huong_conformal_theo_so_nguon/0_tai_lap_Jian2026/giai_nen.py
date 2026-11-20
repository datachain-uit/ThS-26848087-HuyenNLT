"""Bấm Run (▶) trong VS Code: giải nén các repo đã clone (cnsd = Conformalized-Network-Source-Detection, sib) vào thư mục này.
Clone ngày 18/11/2026; commit hash ghi trong COMMITS.txt. cnsd chỉ có code (bỏ ~20 GB dữ liệu/kết quả của repo)."""
import os, tarfile
here = os.path.dirname(os.path.abspath(__file__))
for f in ("cnsd.tgz", "sib.tgz"):
    p = os.path.join(here, f)
    if os.path.exists(p):
        with tarfile.open(p) as t:
            t.extractall(here)
        print("extracted", f)
