# Coding_KLTN

Code và kết quả thực nghiệm luận văn. Mọi kết quả chạy trên máy cá nhân (VS Code, CPU). Mỗi thí nghiệm có giao thức/kế hoạch khóa SHA-256 **trước** khi chạy chính thức: xem `*_lock.json`, `*.sha256` và dòng khóa trong `logs/*.log`.

## Cấu trúc

| Thư mục | Hướng | Câu hỏi | Kết luận | Ngày |
|---|---|---|---|---|
| `1_P6_chon_phan_hoach/H0` | P6 | Chọn phân hoạch cộng đồng có làm khác kết quả định vị nguồn? (Review 30/10 Mục 7.1–7.3) | NO-GO, nhưng có 2 lỗi đo | 03/11 |
| `1_P6_chon_phan_hoach/H0b` | P6 | Thăm dò: thiết lập đo nào hợp lệ? | Chỉ "biết trước k" hợp lệ | 03/11 |
| `1_P6_chon_phan_hoach/H0c` | P6 | Tiêu chí không nhãn chọn phân hoạch | **Bỏ**: lỗi k-center; giữ để đối chiếu | 03/11 |
| `1_P6_chon_phan_hoach/H0c_fix` | P6 | H0c sau khi sửa k-center (`BUGFIX.md`) | NO-GO mạnh | 07/11 |
| `1_P6_chon_phan_hoach/H0p` | P6 | H0 chạy lại sau khi sửa 2 lỗi đo | NO-GO | 07/11 |
| `2_GraphSL_baselines` | Baseline | 5 baseline GraphSL (Review 30/10 Mục 7.4, O3) | Phát hiện 2 lỗi GraphSL 0.15; benchmark mặc định chủ yếu đo phân phối nguồn | 03–04/11 |
| `3_D1_D2_pilot` | D1, D2 | D1 ước lượng số nguồn bằng cộng đồng; D2 đặt monitor theo cộng đồng (Review 30/10 Mục 7.6) | D1 NO-GO, D2 NO-GO | 07/11 |

Báo cáo trong từng thư mục: `BAO_CAO_H0.md`, `*_REPORT.md`, `results/BANG_NOP_GraphSL_10-11.md`.

## Môi trường
- `1_P6_chon_phan_hoach/H0/.venv` dùng chung cho H0, H0b, H0c, H0c_fix, H0p và `3_D1_D2_pilot`. Tạo bằng `H0/00_setup_env.py`; phiên bản ghim trong `H0/requirements.lock.txt`.
- `2_GraphSL_baselines/.venv` riêng (`00_setup_env.py`, `requirements.lock.txt`).
- Chạy bằng file `01_chay_*.py` (bấm Run trong VS Code); `_venv.py` tự chuyển sang `.venv` đúng.

## Dữ liệu không có trên Git
`results/raw/` của các thư mục trong `1_P6_chon_phan_hoach` (~200 MB CSV thô) lưu trên Drive: [link].
