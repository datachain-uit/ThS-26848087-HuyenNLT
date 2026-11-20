# E0 — chạy thử: hồ sơ cộng đồng đa thang của đồ thị con nhiễm có mang tín hiệu về số nguồn k không?

Ngày viết: 14/11/2026. Viết **trước khi chạy**. Seed chạy thử: 9191 (chưa dùng ở H0/H0b/H0c/H0p/D12/P6-F).
Tính chất: **chạy thử thăm dò**, không phải thí nghiệm chính thức, chưa được GVHD duyệt. Kết quả chỉ dùng để quyết định có đáng viết giao thức chính thức hay không.

Bối cảnh: pilot D1 (07/11, `3_D1_D2_pilot`) đã NO-GO với bộ ước lượng đếm cộng đồng **của cả đồ thị** theo tỉ lệ nhiễm (tauD/tauS). E0 thử một biến thể khác: chạy Louvain **trên đồ thị con nhiễm** ở nhiều resolution và dùng cả hồ sơ làm đặc trưng. Đây là lần thử thứ hai trên cùng hướng, phải đọc kết quả với mức thận trọng tương ứng.

## Thiết lập
- Đồ thị: 4 đồ thị của pilot D1 (`lfr_mu0.1_0`, `lfr_mu0.3_0`, `lfr_mu0.5_0`, `email_eu`), đọc từ `../3_D1_D2_pilot/data`.
- Lan truyền: SI rời rạc β = 0,3, nguồn chọn đều. **Kích thước vùng nhiễm cố định** đúng bằng round(f·n), f ∈ {5%, 15%} (bước cuối chỉ nhận ngẫu nhiên đủ số node còn thiếu). Mục đích: loại ảnh hưởng của kích thước vùng nhiễm.
- k ∈ {1, 2, 3, 5, 8}. Mỗi (đồ thị, f, k): 60 cascade train + 60 test.
- Đặc trưng mỗi cascade:
  - Họ N (không cộng đồng): `comp` (số thành phần liên thông của đồ thị con nhiễm); `rho_1..6` (số tâm k-center cần để bán kính ≤ ρ, K_max = 15, dùng `kcenter_seq` bản đã sửa).
  - Họ S1 (một thang): số cộng đồng Louvain kích thước ≥ 3 ở γ = 1.
  - Họ P (hồ sơ đa thang): số cộng đồng Louvain kích thước ≥ 3 ở γ ∈ {0,1; 0,25; 0,5; 1; 2; 4} và modularity ở γ = 1. Louvain seed 0.
- Bộ ước lượng (fit trên train gộp mọi k, lúc test không biết k):
  - `const`: hằng số tốt nhất trên train.
  - `N_rule`: quy tắc tốt nhất trong {comp, rho_1..6} chọn trên train (giống họ N của pilot D1).
  - `N_reg`, `S1_reg`, `P_reg`, `PN_reg`: RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=0) trên đặc trưng họ N / S1 / P / P+N; dự đoán làm tròn, cắt về [1, 15].
- Metric: MAE = |k̂ − k| trên test. Kiểm định: Wilcoxon một phía trên |sai số| từng cascade.

## Tiêu chí (khóa trước khi chạy, không sửa sau khi xem kết quả)
Một ô = (đồ thị, f). Có 8 ô.
- **T0 (có tín hiệu):** MAE(P_reg) < MAE(const) và p < 0,01.
- **Qa (đa thang hơn một thang):** MAE(P_reg) ≤ 0,8 × MAE(S1_reg) và p < 0,01.
- **Qb (cộng đồng thêm thông tin ngoài đặc trưng không cộng đồng):** MAE(PN_reg) ≤ 0,8 × MAE(N_reg) và p < 0,01. Đây là tiêu chí quyết định, vì pilot D1 đã cho thấy họ N mạnh.
- **Kết luận:** Qb đạt ≥ 6/8 ô → KHẢ QUAN (đáng viết giao thức chính thức). Qb đạt ≤ 2/8 ô → KHÔNG KHẢ QUAN. Còn lại → CHƯA RÕ.
- T0 và Qa báo cáo kèm, không dùng để kết luận.

## Giới hạn đã biết
- 4 đồ thị n ≈ 1000, một mô hình lan truyền (SI), chỉ Louvain, một bộ hồi quy, một seed.
- Kích thước vùng nhiễm bị ép cố định nên phân phối cascade khác nhẹ so với SI thuần.
- Bộ hồi quy được huấn luyện và kiểm trên **cùng đồ thị**; chưa kiểm chuyển sang đồ thị khác.
- Mọi kết quả đều báo cáo, kể cả khi âm.
