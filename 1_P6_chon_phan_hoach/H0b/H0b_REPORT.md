# H0b — Báo cáo thăm dò (không phải H0 chính thức)

Sinh tự động 03/11/2026 11:07 từ CSV thô trong `results/raw/` (máy chạy). Seed 3030. 3 đồ thị LFR (μ ∈ {0,1; 0,3; 0,5}), 50 phân hoạch Louvain + 5 ngẫu nhiên, k ∈ {1, 3, 5}, 50 cascade test.

**Quy tắc đọc:** chỉ ô **hợp lệ** (V1 cây ED ≤ 1, V2 phân hoạch ngẫu nhiên kém hơn Louvain, V3 |k̂−k| ≤ 1) mới được xem η². Thiết lập không được chọn theo η².

| Ô (quan sát \| số nguồn) | Cây ED (đoán trúng %) | ED Louvain | ED ngẫu nhiên | \|k̂−k\| | Hợp lệ | F1@1 | η² trung vị | η² max | Δ cf trung vị | cặp η² ≥ 0,20 |
|---|---|---|---|---|---|---|---|---|---|---|
| ic_T|known_k | 0.00 (100%) | 2.14 | 2.57 | 0.0 | ✓ | 0.25 | 0.10 | 0.43 | 0.07 | 3/9 |
| ic_T|rho_ed | 0.00 (100%) | 0.52 | 0.15 | 67.4 | ✗ | 0.15 | 0.04 | 0.13 | 0.05 | 0/9 |
| ic_T|rho_f1 | 0.00 (100%) | 0.59 | 0.16 | 62.8 | ✗ | 0.16 | 0.04 | 0.45 | 0.05 | 1/9 |
| ic_full|known_k | 0.31 (70%) | 2.53 | 2.73 | 0.0 | ✓ | 0.13 | 0.03 | 0.06 | -0.00 | 0/9 |
| ic_full|rho_ed | 0.31 (70%) | 0.45 | 0.13 | 65.2 | ✗ | 0.14 | 0.01 | 0.10 | 0.02 | 0/9 |
| ic_full|rho_f1 | 0.31 (70%) | 0.97 | 0.14 | 35.2 | ✗ | 0.15 | 0.20 | 0.68 | 0.04 | 4/9 |
| si_t|known_k | 0.07 (93%) | 1.92 | 2.39 | 0.0 | ✓ | 0.33 | 0.16 | 0.43 | 0.15 | 4/9 |
| si_t|rho_ed | 0.07 (93%) | 0.63 | 0.23 | 74.9 | ✗ | 0.20 | 0.06 | 0.35 | 0.06 | 1/9 |
| si_t|rho_f1 | 0.07 (93%) | 0.67 | 0.23 | 70.8 | ✗ | 0.20 | 0.06 | 0.42 | 0.09 | 2/9 |

## Ghi chú thiết kế
- ic_T: IC dừng sau T = 4 bước (cây: 12 bước), p hiệu chỉnh để tập nhiễm 10–20%.
- si_t: SI rời rạc, β = 0.3, chụp snapshot ngay khi tập nhiễm đạt kích thước mục tiêu ~ U(10%, 20%).
- known_k: tổng k biết trước; CommJordan phân bổ k tâm cho các cộng đồng nhiễm lớn nhất, tâm dư cấp cho cộng đồng có bán kính lớn nhất; Jordan: greedy k-center đúng k tâm; LPSI: top-k điểm.
- rho_f1: ngưỡng ρ chọn trên val theo F1@1 (phạt đoán thừa).
- Kiểm tra cây (V1): cây tam phân cân bằng sâu 7, nguồn ở gốc, tập nhiễm 100–200 node (xấp xỉ cây đều vô hạn). Lưu ý: với nguồn ở gốc, cây đối xứng nên V1 kém nhạy với vấn đề định danh của ic_full; vấn đề này xem ở identifiability_check của H0.
- Mọi ô dùng cùng đồ thị và phân hoạch; trong cùng mô hình quan sát, các ô dùng cùng cascade.
