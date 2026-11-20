# Coding_KLTN

Code và kết quả thực nghiệm luận văn thạc sĩ: **conformal prediction cho định vị đa nguồn lan truyền, với bảo đảm theo số nguồn và theo cơ chế lan truyền**. Mọi kết quả chạy trên máy cá nhân (Windows, VS Code, CPU). Mỗi thí nghiệm có kế hoạch và tiêu chí khóa SHA-256 **trước** khi chạy chính thức.

- Báo cáo hướng đi: [`docs/BAO_CAO_HUONG_DI.md`](docs/BAO_CAO_HUONG_DI.md)
- Mục lục thí nghiệm (mã J-K…, câu hỏi, kết luận, báo cáo): [`docs/MUC_LUC_THI_NGHIEM.md`](docs/MUC_LUC_THI_NGHIEM.md)
- Đối chiếu SHA các file kế hoạch đã sửa chữ: [`docs/DOI_CHIEU_SHA.md`](docs/DOI_CHIEU_SHA.md)

## Cấu trúc

```
1_huong_cong_dong/                     Giai đoạn 1 — hướng cộng đồng (đã dừng, kết quả âm)
  1_P6_chon_phan_hoach/          H0, H0b, H0c, H0c_fix, H0p
  2_baseline_GraphSL/
  3_D1_D2_uoc_luong_so_nguon/
  4_P6F_hieu_chinh_ti_le_nhiem/
  5_E0_ho_so_cong_dong_da_thang/
  6_E0x_so_cum_theo_so_nguon/
2_huong_conformal_theo_so_nguon/        Giai đoạn 2 — hướng hiện tại
  0_tai_lap_Jian2026/            tái lập Jian et al. (AAAI 2026)
  1_tap_du_doan_so_nguon/        PK
  2_chan_doan_phu_theo_k/        RQ1: JK1, JK2, JK3, JK10, JK11
  3_KSU_bao_dam_theo_k/          RQ2 (C1): JK4, JK5, JK6
  4_gia_cua_bao_dam/             RQ3: JK7, JK8, JK12, JK13, JK14
  6_do_ben/                      RQ4: JK15, JK16, JK17–18
  7_KSU_mk_ho_co_che/            RQ5 (C2): JK19, JK19b
  8_kiem_tra_doc_lap/            tính lại độc lập các số chính
docs/
```

Mỗi thư mục thí nghiệm theo cùng khuôn: `*_PLAN.md` (khóa trước) → code `*.py` → `results/*_REPORT.md`. Bấm Run file `chay_*.py` trong thư mục để chạy.

## Môi trường

- `1_huong_cong_dong/1_P6_chon_phan_hoach/H0/.venv` dùng chung cho hầu hết thí nghiệm. Tạo bằng `H0/00_setup_env.py`; phiên bản ghim trong `H0/requirements.lock.txt`.
- `1_huong_cong_dong/2_baseline_GraphSL/.venv` dùng cho GraphSL và backbone GCN (JK15).
- `_venv.py` trong mỗi thư mục tự chuyển sang đúng `.venv`.

## Không có trên Git

- Repo và dữ liệu của tác giả Jian et al. (~1 GB): nguồn và commit ghi trong `2_huong_conformal_theo_so_nguon/0_tai_lap_Jian2026/COMMITS.txt`; giải nén bằng `giai_nen.py`.
- `results/raw/` của `1_P6_chon_phan_hoach` (~200 MB CSV thô).

## Tên thư mục cũ → mới (21/11/2026)

Kế hoạch và báo cáo viết trước ngày này (đã khóa SHA) còn ghi tên cũ:

| Tên cũ | Tên mới |
|---|---|
| `1_P6_chon_phan_hoach` | `1_huong_cong_dong/1_P6_chon_phan_hoach` |
| `2_GraphSL_baselines` | `1_huong_cong_dong/2_baseline_GraphSL` |
| `3_D1_D2_pilot` | `1_huong_cong_dong/3_D1_D2_uoc_luong_so_nguon` |
| `4_P6F` | `1_huong_cong_dong/4_P6F_hieu_chinh_ti_le_nhiem` |
| `5_E0_ho_so_da_thang` | `1_huong_cong_dong/5_E0_ho_so_cong_dong_da_thang` |
| `6_E0x_so_cum_va_vung_dinh_danh` | `1_huong_cong_dong/6_E0x_so_cum_theo_so_nguon` |
| `8_tai_lap_paper` | `2_huong_conformal_theo_so_nguon/0_tai_lap_Jian2026` |
| `7_PK_tap_du_doan_k` | `2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK_tap_du_doan_k` |
| `10_JK_dieu_kien_theo_k` | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k` |
| `11_JK2_lap_lai` | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK2_lap_lai` |
| `12_JK3_do_ben` | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK3_do_ben_theo_pow` |
| `19_JK10_tong_quat` | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK10_tong_quat_mo_phong` |
| `20_JK11_do_thi_lon` | `2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK11_do_thi_lon` |
| `13_JK4_bao_dam` | `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK4_KSU` |
| `14_JK5_MDCP` | `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP` |
| `15_JK6_lech_prior` | `2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK6_lech_prior` |
| `16_JK7_KNCP` | `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP` |
| `17_JK8_diem_theo_k` | `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k` |
| `21_JK12_gia_theo_K` | `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK12_gia_theo_K` |
| `22_JK13_LD` | `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK13_LDCP` |
| `23_JK14_LD2` | `2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK14_LDCP_v2` |
| `25_JK15_do_ben` | `2_huong_conformal_theo_so_nguon/6_do_ben/JK15_backbone_do_thi_that_chia_alpha` |
| `26_JK16_10_seed` | `2_huong_conformal_theo_so_nguon/6_do_ben/JK16_lap_10_seed` |
| `27_JK17_18_lech_va_nhieu` | `2_huong_conformal_theo_so_nguon/6_do_ben/JK17_18_lech_mo_hinh_thieu_nut` |
| `28_JK19_tron_co_che` | `2_huong_conformal_theo_so_nguon/7_KSU_mk_ho_co_che/JK19_JK19b` |
| `24_KIEM_TRA` | `2_huong_conformal_theo_so_nguon/8_kiem_tra_doc_lap` |
