# Sai lệch so với hồ sơ đã khóa (DEVIATIONS)

Lập 24/11/2026 theo quy tắc 7.7 và QĐ25 của kỳ đánh giá 21/11/2026. Toàn bộ thí nghiệm liệt kê dưới đây là **thăm dò** (QĐ22).

## 1. Tệp có SHA-256 hiện tại khác SHA ghi trong báo cáo sinh tự động

Bảng do script tự đối chiếu: với mỗi báo cáo `*_REPORT.md` có ghi SHA, tính lại SHA-256 (cùng số ký tự) của tệp hiện tại. Trong 53 tệp có SHA ghi trong báo cáo, 18 tệp khớp, các tệp còn lại như bảng.

**Nguyên nhân chung:** đêm 20/11/2026 (các tệp code sửa lúc 00:28 ngày 21/11) repo được đổi tên và gom thư mục (ví dụ `14_JK5_MDCP` → `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP`); đường dẫn import trong code được sửa theo. Tối 20/11, 5 tệp kế hoạch được sửa phần chữ nêu người thực hiện và công cụ hỗ trợ (`DOI_CHIEU_SHA.md` chỉ ghi 5 tệp kế hoạch này, chưa ghi các tệp code).

**Cách kiểm chứng cho tệp code:** khi còn bản `__pycache__/*.cpython-310.pyc` biên dịch trước lần sửa, so sánh bytecode, hằng số và tên biến của từng hàm giữa bản `.pyc` cũ và bản biên dịch từ mã hiện tại. Giới hạn: `.pyc` có thể được tạo sau lần chạy chính, nên phép so sánh chỉ chứng minh mã không đổi giữa thời điểm biên dịch `.pyc` và nay, trừ đường dẫn.

| Tệp | SHA trong báo cáo | SHA hiện tại | Đối chiếu |
|---|---|---|---|
| `2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK2_lech_mo_hinh/PK2_PLAN.md` | ef7450b953e97898 | d897831edc77a595 | sửa phần chữ người thực hiện, công cụ hỗ trợ, đường dẫn ghi chú (xem DOI_CHIEU_SHA.md); bản gốc không được lưu |
| `2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK2_lech_mo_hinh/pk2.py` | 673b193456799010 | 894293c3b903c517 | .pyc biên dịch 18/11 21:07 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK_tap_du_doan_k/PK_PLAN.md` | 16c3365acb8d8c64 | f68297e3e0cc8f9d | sửa phần chữ người thực hiện, công cụ hỗ trợ, đường dẫn ghi chú (xem DOI_CHIEU_SHA.md); bản gốc không được lưu |
| `2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK_tap_du_doan_k/pk.py` | 89031bb511722d75 | dc6c7578a041a07a | .pyc biên dịch 18/11 08:41 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK10_tong_quat_mo_phong/jk10.py` | 1e1a3ebf008848ab | 673a915bb93d0c52 | .pyc biên dịch 18/11 15:30 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK11_do_thi_lon/jk11.py` | 13da6dc064575c30 | 928b83ac678454b9 | .pyc biên dịch 18/11 15:55 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k/JK_PLAN.md` | 893a6642076ac3e9 | ecd91de602de902f | sửa phần chữ người thực hiện, công cụ hỗ trợ, đường dẫn ghi chú (xem DOI_CHIEU_SHA.md); bản gốc không được lưu |
| `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k/jk.py` | 005ba64d7e7aef4d | 9497490622531407 | .pyc biên dịch 18/11 18:09 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK2_lap_lai/jk2.py` | 1a327ff38f8079b3 | a0de0815ed32084c | không có bản .pyc cũ để đối chiếu |
| `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK3_do_ben_theo_pow/jk3.py` | e6c37655df379acb | 8a2ec84acc17a519 | không có bản .pyc cũ để đối chiếu |
| `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK4_KSU/jk4.py` | f9da392ac07daf97 | 7fb4d07dadbb1e61 | không có bản .pyc cũ để đối chiếu |
| `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP/jk5.py` | 13784f8982d1f565 | d6ca2e5472464432 | .pyc biên dịch 18/11 12:44 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK6_lech_prior/jk6.py` | 924b432260fe3b84 | 3f807d521a206062 | .pyc biên dịch 18/11 13:10 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK12_gia_theo_K/jk12.py` | d59235332e324411 | 4eacf04c9a13d4fa | .pyc biên dịch 18/11 16:39 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK13_LDCP/jk13.py` | 909fad1389ec6f63 | facd446948e0b481 | .pyc biên dịch 18/11 18:09 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK14_LDCP_v2/jk14.py` | 7db91c0a8113316e | 5b3b5026a96fd430 | .pyc biên dịch 18/11 21:07 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP/jk7.py` | 366f9f5701cf898d | 8cb2c09952918e47 | .pyc biên dịch 18/11 13:56 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k/jk8.py` | 56f5af0dd9764088 | d1bb43c8f59e9853 | .pyc biên dịch 18/11 14:11 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/5_chat_luong_diem/JK9_xep_hang_lai/jk9.py` | f2b869529a963e68 | 1a728af3ac851a1f | .pyc biên dịch 18/11 15:03 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/6_do_ben/JK15_backbone_do_thi_that_chia_alpha/jk15a.py` | e9a9741ed317e33f | 13d9350347733aea | không có bản .pyc cũ để đối chiếu |
| `2_huong_conformal_theo_so_nguon/6_do_ben/JK15_backbone_do_thi_that_chia_alpha/jk15b.py` | e3d276f023663a40 | e617244f57711b4a | không có bản .pyc cũ để đối chiếu |
| `2_huong_conformal_theo_so_nguon/6_do_ben/JK16_lap_10_seed/jk16.py` | 9a51b7cf7665be2c | 5bfd5feb2de88077 | không có bản .pyc cũ để đối chiếu |
| `2_huong_conformal_theo_so_nguon/6_do_ben/JK17_18_lech_mo_hinh_thieu_nut/jk17.py` | af42612bbd60930b | 1d24288be812579b | .pyc biên dịch 20/11 15:53 (giờ VN): mọi hàm trùng, chỉ khác hằng chuỗi đường dẫn thư mục |
| `2_huong_conformal_theo_so_nguon/7_KSU_mk_ho_co_che/JK19_JK19b/JK19_PLAN.md` | 5564ecf25a4427dd | 68de0722dbbb3f3e | sửa phần chữ người thực hiện, công cụ hỗ trợ, đường dẫn ghi chú (xem DOI_CHIEU_SHA.md); bản gốc không được lưu |
| `2_huong_conformal_theo_so_nguon/7_KSU_mk_ho_co_che/JK19_JK19b/jk19.py` | 8cdc914e6b441992 | 70b2f469a0395959 | không có bản .pyc cũ để đối chiếu |
| `2_huong_conformal_theo_so_nguon/7_KSU_mk_ho_co_che/JK19_JK19b/jk19b.py` | 91804ce4806a5220 | 78b69ddd7e5152ae | không có bản .pyc cũ để đối chiếu |

Các tệp ghi "không có bản .pyc cũ" chưa được kiểm chứng; sẽ kiểm bằng cách chạy lại và so số liệu với báo cáo (yêu cầu tái lập QĐ25).

## 2. Thư mục không được đưa lên trong commit ngày 21/11
- `2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK2_lech_mo_hinh/` (P-K2, NO-GO; chứa `pk2.py` mà J-K10, J-K11 và các thí nghiệm sau phụ thuộc): bổ sung 24/11, xem `GHI_CHU_HO_SO.md` trong thư mục.
- `2_huong_conformal_theo_so_nguon/5_chat_luong_diem/JK9_xep_hang_lai/` (J-K9): bổ sung 24/11.
