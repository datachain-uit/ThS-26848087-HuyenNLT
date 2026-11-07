# H0c — Báo cáo (sinh tự động từ CSV thô trên máy chạy)

03/11/2026 14:41. Seed 4040. Kế hoạch khóa: xem `logs/h0c.log` (SHA-256 của H0c_PLAN.md và h0c.py).

Tổ hợp đạt một điều kiện khi V2 đúng và ≥ 4/6 cặp (đồ thị × k) đạt. Ngưỡng: η² ≥ 0,20 và Δcf ≥ max(0,3 hop; 10%); Đ3 dùng tiêu chí chính `q_inf`.

| Quan sát | Đặt nguồn | Bộ định vị | V2 | Đ1 (cặp) | Đ2 (cặp) | Đ3 (cặp) | ED mặc định | ED chọn q_inf | ED Jordan | ED LPSI | ED cộng đồng thật | ED oracle | η² toàn / hợp lý | Δcf toàn / hợp lý |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ic_T | random | commjordan | ✗ | ✗ 0/6 | ✗ 0/6 | ✗ 0/6 | 2.28 | 2.26 | 2.37 | 2.32 | 2.23 | 1.71 | 0.03 / 0.02 | 0.01 / 0.01 |
| ic_T | random | commlpsi | ✗ | ✗ 0/6 | ✗ 0/6 | ✗ 0/6 | 2.26 | 2.23 | 2.37 | 2.32 | 2.25 | 1.72 | 0.01 / 0.00 | 0.04 / 0.02 |
| ic_T | spread | commjordan | ✗ | ✗ 0/6 | ✗ 0/6 | ✗ 0/6 | 2.30 | 2.28 | 2.31 | 2.39 | 2.29 | 1.67 | 0.02 / 0.02 | 0.08 / 0.08 |
| ic_T | spread | commlpsi | ✗ | ✗ 0/6 | ✗ 0/6 | ✗ 0/6 | 2.29 | 2.29 | 2.31 | 2.39 | 2.33 | 1.76 | 0.01 / 0.01 | 0.02 / 0.02 |
| si_t | random | commjordan | ✓ | ✗ 0/6 | ✗ 0/6 | ✗ 0/6 | 2.01 | 1.98 | 2.17 | 1.62 | 1.97 | 1.44 | 0.08 / 0.05 | 0.03 / 0.03 |
| si_t | random | commlpsi | ✓ | ✗ 0/6 | ✗ 0/6 | ✗ 0/6 | 1.59 | 1.56 | 2.17 | 1.62 | 1.64 | 0.97 | 0.11 / 0.03 | 0.09 / 0.14 |
| si_t | spread | commjordan | ✗ | ✗ 0/6 | ✗ 0/6 | ✗ 0/6 | 2.04 | 2.00 | 2.20 | 1.69 | 1.99 | 1.43 | 0.10 / 0.04 | 0.08 / 0.08 |
| si_t | spread | commlpsi | ✓ | ✗ 0/6 | ✗ 0/6 | ✗ 0/6 | 1.60 | 1.61 | 2.20 | 1.69 | 1.66 | 1.00 | 0.11 / 0.02 | 0.07 / 0.11 |

## Tiêu chí không nhãn (thăm dò): ED khi chọn theo từng tiêu chí, trung bình mọi cặp

| Quan sát | Đặt nguồn | Bộ định vị | mặc định | q_inf | q_full | conc | fitk | cons | Spearman trung vị (q_inf, q_full, conc, fitk, cons) |
|---|---|---|---|---|---|---|---|---|---|
| ic_T | random | commjordan | 2.28 | 2.26 | 2.27 | 2.39 | 2.30 | 2.23 | 0.25, 0.24, -0.35, 0.11, 0.25 |
| ic_T | random | commlpsi | 2.26 | 2.23 | 2.24 | 2.26 | 2.24 | 2.25 | 0.08, 0.05, -0.06, 0.04, 0.05 |
| ic_T | spread | commjordan | 2.30 | 2.28 | 2.29 | 2.35 | 2.31 | 2.25 | 0.06, 0.06, -0.07, 0.02, 0.07 |
| ic_T | spread | commlpsi | 2.29 | 2.29 | 2.29 | 2.30 | 2.29 | 2.28 | 0.06, 0.08, -0.10, -0.04, 0.08 |
| si_t | random | commjordan | 2.01 | 1.98 | 1.98 | 2.19 | 2.04 | 1.89 | 0.38, 0.41, -0.45, 0.27, 0.46 |
| si_t | random | commlpsi | 1.59 | 1.56 | 1.60 | 1.52 | 1.57 | 1.62 | -0.08, -0.10, 0.30, 0.16, -0.13 |
| si_t | spread | commjordan | 2.04 | 2.00 | 2.00 | 2.20 | 2.05 | 1.90 | 0.38, 0.40, -0.48, 0.13, 0.45 |
| si_t | spread | commlpsi | 1.60 | 1.61 | 1.62 | 1.58 | 1.56 | 1.64 | -0.04, -0.05, 0.13, 0.13, -0.04 |

**Kết luận theo quy tắc định trước:** NO-GO mạnh: không tổ hợp hợp lệ nào đạt Đ2.

