# Mục lục thí nghiệm và trạng thái (kiểm tra 20/11/2026, 23:10)

**Trạng thái chung:** mọi thí nghiệm đã đăng ký đều đã chạy xong và có báo cáo tự động, **trừ P6-F chính thức** (giao thức chưa khóa, đang chờ GVHD xác nhận nên chưa chạy).

Tài liệu trong `docs/`: `BAO_CAO_HUONG_DI.md` (báo cáo hướng đi), `DOI_CHIEU_SHA.md` (đối chiếu mã băm).

## Giai đoạn 1 — Hướng cộng đồng (P6), đã dừng

| Thí nghiệm | Thư mục | Câu hỏi | Kết luận | Báo cáo |
|---|---|---|---|---|
| H0 | `1_huong_cong_dong/1_P6_chon_phan_hoach/H0/` | Chọn phân hoạch cộng đồng có giúp định vị nguồn? | NO-GO (H-a đạt 0/16 đồ thị) | `BAO_CAO_H0.md` |
| H0b | `1_huong_cong_dong/1_P6_chon_phan_hoach/H0b/` | Thăm dò theo ô quan sát × số nguồn | Thăm dò, không có kết luận chính thức | `H0b_REPORT.md` |
| H0c, H0c_fix | `…/H0c/`, `…/H0c_fix/` | Như trên, sửa lỗi k-center | NO-GO mạnh | `H0c_REPORT.md`, `H0c_fix_REPORT.md` |
| H0p | `…/H0p/` | Như trên, mô hình quan sát mới | NO-GO | `H0p_REPORT.md` |
| P6-F hiệu chỉnh | `1_huong_cong_dong/4_P6F_hieu_chinh_ti_le_nhiem/` | Dư địa cho phương pháp cộng đồng | Chỉ 0,2–1,0 hop ở cascade chồng lấn | `HIEU_CHINH_F.md`, `CHAN_DOAN.md` |
| P6-F chính thức | `1_huong_cong_dong/4_P6F_hieu_chinh_ti_le_nhiem/` | — | **CHƯA CHẠY** (giao thức chưa khóa) | `P6F_PROTOCOL.md` |
| E0 | `1_huong_cong_dong/5_E0_ho_so_cong_dong_da_thang/` | Ước lượng k từ hồ sơ cộng đồng đa thang | Không khả quan | `results/E0_REPORT.md` |
| E0x | `1_huong_cong_dong/6_E0x_so_cum_theo_so_nguon/` | Số cụm phụ thuộc k? Vùng định danh k? | E0c xác nhận (24/24); E0a trượt (0/12) | `results/E0X_REPORT.md` (bản 8 seed chỉ là tạm, không có hiệu lực) |

## Giai đoạn 2 — Conformal theo số nguồn (hướng hiện tại)

| Thí nghiệm | Thư mục | Câu hỏi | Kết luận | Báo cáo |
|---|---|---|---|---|
| PK | `2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK_tap_du_doan_k/` | Tập dự đoán conformal cho k | GO | `results/PK_REPORT.md` |
| Tái lập | `2_huong_conformal_theo_so_nguon/0_tai_lap_Jian2026/` | Tái lập Jian et al. | Khớp đến 3 chữ số | `TAI_LAP_CONFORMAL.md` |
| J-K1 | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k/` | Phủ theo k | NO-GO (M1/M3) → mở hướng chẩn đoán | `results/JK_REPORT.md` |
| J-K2 | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK2_lap_lai/` | Lặp lại | Lặp lại 8/8 | `results/JK2_REPORT.md` |
| J-K3 | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK3_do_ben_theo_pow/` | Độ bền theo pow | Bền một phần (55/81) | `results/JK3_REPORT.md` |
| J-K4 | `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK4_KSU/` | KSU\* bảo đảm theo k | KSU\* hợp lệ | `results/JK4_REPORT.md` |
| J-K5 | `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP/` | So với MDCP | Một phần | `results/JK5_REPORT.md` |
| J-K6 | `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK6_lech_prior/` | Lệch prior k | KSU\* bền, WCP cũng bền; G sập | `results/JK6_REPORT.md` |
| J-K7 | `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP/` | KN-CP | NO-GO | `results/JK7_REPORT.md` |
| J-K8 | `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k/` | Điểm theo k | NO-GO | `results/JK8_REPORT.md` |
| J-K10 | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK10_tong_quat_mo_phong/` | Tổng quát hóa | Một phần | `results/JK10_REPORT.md` |
| J-K11 | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK11_do_thi_lon/` | Đồ thị 10k nút | Tổng quát hóa | `results/JK11_REPORT.md` |
| J-K12 | `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK12_gia_theo_K/` | Giá theo \|K̂\| | Xác nhận, ρ = 0,89 | `results/JK12_REPORT.md` |
| J-K13, J-K14 | `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK13_LDCP/`, `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK14_LDCP_v2/` | LD-CP | NO-GO | `results/JK13_REPORT.md`, `results/JK14_REPORT.md` |
| Kiểm tra độc lập | `2_huong_conformal_theo_so_nguon/8_kiem_tra_doc_lap/` | Tính lại số chính | Khớp toàn bộ | `V1/V2/V3_KET_QUA.txt` |
| J-K15 | `2_huong_conformal_theo_so_nguon/6_do_ben/JK15_backbone_do_thi_that_chia_alpha/` | Backbone GCN; đồ thị thật; chia α | A bền theo backbone; B tổng quát hóa; C mặc định α hợp lý (8/9) | `results/JK15A_REPORT.md` (gồm phần C), `results/JK15B_REPORT.md` |
| J-K16 | `2_huong_conformal_theo_so_nguon/6_do_ben/JK16_lap_10_seed/` | 10 seed | Đạt cả 4 tiêu chí | `results/JK16_REPORT.md` |
| J-K17 | `2_huong_conformal_theo_so_nguon/6_do_ben/JK17_18_lech_mo_hinh_thieu_nut/` | Lệch mô hình lan truyền | Bền tương đối, mất bảo đảm tuyệt đối (P2 trượt 17/32) | `results/JK17_18_REPORT.md` |
| J-K18 | như trên | Ảnh chụp thiếu nút | Q1 trượt (11/12), Q2 trượt (0/12), Q3 đạt | như trên |
| J-K19 | `2_huong_conformal_theo_so_nguon/7_KSU_mk_ho_co_che/JK19_JK19b/` | KSU\*-mk trên họ cơ chế | Cần xem lại (V1 trượt sát ngưỡng 0,855; oracle cũng 0,831) | `results/JK19_REPORT.md` |
| J-K19b | như trên | Chẩn đoán đi sau, khóa trước | Đạt: 36/36, thấp nhất 0,893; nhỏ hơn MD-mk ×1,8–3,3 | `results/JK19b_REPORT.md` |

## Còn mở
1. Chưa tính lại độc lập: J-K17/18, J-K19/19b (code mới), J-K7/8/14.
2. Đọc toàn văn MS-RLCP và Kandinsky CP để chốt tính mới.
3. Hình 1–5; §2 công trình liên quan; bản tiếng Anh/LaTeX.
4. P6-F chính thức: quyết định chạy hay đóng (báo cô).
