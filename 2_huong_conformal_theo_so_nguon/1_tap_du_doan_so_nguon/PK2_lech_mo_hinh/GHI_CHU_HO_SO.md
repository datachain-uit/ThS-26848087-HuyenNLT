# P-K2 — ghi chú hồ sơ (viết 24/11/2026, theo QĐ25 kỳ đánh giá 21/11)

**Trạng thái:** thăm dò (QĐ22). Chạy xong 18/11/2026 lúc 10:37, kết luận theo tiêu chí trong `PK2_PLAN.md`: **NO-GO** (V 16/16, U2 3/8, R 25/32, RM 42/48). Báo cáo sinh tự động: `results/PK2_REPORT.md`; dữ liệu từng phần: `results/chunks/` (160 tệp); nhật ký chạy: `logs/pk2.log`.

## Vì sao thư mục này không có trong commit ngày 21/11
Khi sắp xếp lại repo ngày 21/11, thư mục P-K2 bị để lại trên máy, không đưa lên GitHub. Đây là sơ suất: `pk2.py` chứa hàm mô phỏng IC và SIR (`ic_fixed`, `sir_fixed`) mà J-K10, J-K11 import, và qua đó J-K15B, J-K16, J-K17 → J-K19b và bước V2, V3 của kiểm tra độc lập đều phụ thuộc. Commit này bổ sung đủ giao thức, code, nhật ký, báo cáo và dữ liệu từng phần.

## Các tệp đã bị sửa sau khi chạy
| Tệp | SHA-256 (16 ký tự) lúc chạy, ghi trong báo cáo | SHA-256 hiện tại | Nội dung sửa |
|---|---|---|---|
| `PK2_PLAN.md` | ef7450b953e97898 | d897831edc77a595 | Sửa lúc 22:55 ngày 20/11 phần chữ nêu người thực hiện, công cụ hỗ trợ và đường dẫn ghi chú ngoài repo (xem `docs/DOI_CHIEU_SHA.md`). Bản trước khi sửa không được lưu |
| `pk2.py` | 673b193456799010 | 894293c3b903c517 | Sửa lúc 00:28 ngày 21/11 khi đổi tên thư mục: chỉ đường dẫn import module E0 (`5_E0_ho_so_da_thang` → `1_huong_cong_dong/5_E0_ho_so_cong_dong_da_thang`) |
| `chay_PK2.py`, `_venv.py` | — | — | Sửa lúc 00:28 ngày 21/11 khi đổi tên thư mục (đường dẫn) |

**Bằng chứng cho dòng `pk2.py`:** so sánh bytecode của `__pycache__/pk2.cpython-310.pyc` (biên dịch 18/11/2026 21:07 giờ Việt Nam, trước lần sửa lúc 00:28 ngày 21/11) với bản biên dịch của `pk2.py` hiện tại: mọi hàm trùng khớp; khác biệt duy nhất nằm ở hằng chuỗi đường dẫn thư mục E0 trong phần module. Bản `.pyc` này được tạo sau lần chạy P-K2, nên phép so sánh không loại trừ được thay đổi giữa 10:37 và 21:07 ngày 18/11.

Đường dẫn trong `logs/pk2.log` và `results/PK2_REPORT.md` là đường dẫn cũ (`9_PK2_lech_mo_hinh`) trước khi đổi tên thư mục.

## Chạy lại
```
python 2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK2_lech_mo_hinh/pk2.py                 # chạy đầy đủ (~150 phút, CPU)
python 2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK2_lech_mo_hinh/pk2.py --analyze-only  # dựng lại báo cáo từ results/chunks/
```
