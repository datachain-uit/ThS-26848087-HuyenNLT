# H0' (H0p)

H0 theo thiết kế Review 30/10 Mục 7.3, giữ nguyên 16 đồ thị, 55 phân hoạch, k ∈ {1, 3, 5}, 200 cascade, ngưỡng H-a/H-b; chỉ sửa hai lỗi đo (IC chạy đến hết; ρ chọn theo ED thưởng đoán thừa). Chi tiết: `H0p_PROTOCOL.md`.

| Tệp | Vai trò |
|---|---|
| `H0p_PROTOCOL.md` | Giao thức, khóa SHA-256 lúc bắt đầu chạy (`H0p_lock.json`, `logs/h0p.log`) |
| `01_chay_H0p.py` | Bấm Run: chạy test → identifiability_v2 → h0p |
| `h0p.py` | Sinh cascade, định vị, chấm điểm, phân tích, viết `H0p_REPORT.md` |
| `h0b.py` | Hàm lan truyền và k-center **đã sửa** (giống `H0c_fix/h0b.py`) |
| `h0lib.py`, `config.py` | Giống hệt `H0/` |
| `identifiability_v2.py` | Kiểm tra định danh nguồn: (A) cùng p, đổi thời điểm dừng; (B) cùng kích thước nhiễm 10–20% |
| `test_kcenter.py` | Kiểm tra bản sửa k-center |
| `data/` | Chép nguyên từ `H0/data/` (đồ thị, phân hoạch, cộng đồng thật, manifest) |

Dùng chung `.venv` của `H0/`. Chạy lại được: việc đã có CSV trong `results/raw/` sẽ bỏ qua. Chỉ phân tích lại: `python h0p.py --analyze`.
