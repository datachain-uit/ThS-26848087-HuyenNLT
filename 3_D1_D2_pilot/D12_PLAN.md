# Pilot D1 + D2 — giao thức (khóa SHA-256 trước khi chạy chính thức)

Ngày viết: 07/11/2026. Seed cascade: 6060 (H0 2026, H0b 3030, H0c 4040, H0p 5050). Chạy thử: 6161.
Căn cứ: Review 30/10 Mục 7.6 (NO-GO → D1 ước lượng số nguồn bằng cộng đồng, hoặc D2 đặt monitor theo cộng đồng); H0p NO-GO (07/11).

**Mục đích:** pilot chỉ trả lời "có tín hiệu đo được không", **không** trả lời "có mới không".
Rủi ro tính mới đã biết: D1 gần KBS 2020 (số nguồn = số vùng thế cao); D2 gần CSOL (CIKM 2025, đặt observer theo phân hoạch cộng đồng, 1 nguồn). Phải đối chiếu PDF trước khi đề xuất.

## 1. Giữ nguyên từ H0p
- Đồ thị + phân hoạch: 4/16 đồ thị của H0 (`lfr_mu0.1_0`, `lfr_mu0.3_0`, `lfr_mu0.5_0`, `email_eu`), 50 Louvain + 5 ngẫu nhiên, mặc định γ = 1 seed 0. Cộng đồng thật chỉ làm tham chiếu.
- Mô hình quan sát: `si_t` (SI β = 0,3, chụp khi nhiễm U(10%, 20%)) và `ic_T` (IC dừng sau T = 4 bước, p hiệu chỉnh theo (đồ thị, k)). Tỉ lệ nhiễm 10–20%.
- k-center: `h0b.kcenter_seq` bản đã sửa (H0c_fix/BUGFIX.md). LPSI α = 0,5.

## 2. D1 — ước lượng số nguồn k
- k ∈ {1, 2, 3, 5, 8}, nguồn chọn đều. Mỗi (đồ thị, quan sát, k): 40 cascade val + 100 test. **Tham số mỗi bộ ước lượng chọn trên val, gộp mọi k** (lúc test không biết k).
- Bộ ước lượng không dùng cộng đồng (họ N):
  - `comp`: số thành phần liên thông của đồ thị con nhiễm.
  - `lpsi`: số cực đại cục bộ của LPSI (Wang et al., AAAI 2017).
  - `elbow0`: k nhỏ nhất mà bán kính k-center không giảm khi thêm tâm (tương tự quy tắc T(k) = T(k+1) của Jiang et al. 2018); trần K_max = 15.
  - `rhoG_ρ`: k nhỏ nhất mà bán kính k-center toàn tập nhiễm ≤ ρ, ρ ∈ {1..6}.
- Bộ ước lượng dùng cộng đồng (họ C), phân hoạch mặc định:
  - `tauD_τ`: số cộng đồng có tỉ lệ nhiễm |I∩c|/|c| ≥ τ, τ ∈ {0,02; 0,05; 0,1; 0,15; 0,2; 0,3; 0,4; 0,5; 0,6}.
  - `tauS_τ`: trung vị của `tau_τ` qua 50 phân hoạch Louvain (ước lượng ổn định qua nhiều phân hoạch).
  - `rhoD_ρ`: B2 của H0 (tổng số tâm k-center mỗi cộng đồng đến bán kính ≤ ρ), nhưng ρ chọn theo sai số k, không theo ED.
- Tham chiếu (không tính kết luận): `tauT_τ`, `rhoT_ρ` với cộng đồng thật; hằng số c ∈ {1,2,3,5,8}.
- Mọi k̂ cắt dưới ở 1.
- Metric chính: MAE = |k̂ − k| trên test. Phụ: tỉ lệ đúng, độ lệch k̂ − k, F1@1 của CommJordan (phân hoạch mặc định) khi dùng k̂ thay k.
- **Chọn đại diện họ trên val** (MAE nhỏ nhất trong họ), so trên test.
- Một đồ thị **đạt D1** khi: MAE_C ≤ 0,8 × MAE_N **và** Wilcoxon một phía trên |sai số| từng cascade p < 0,01 **và** MAE_C < MAE hằng số tốt nhất.
- **Kết luận D1:** đạt ở ≥ 3/4 đồ thị ở cả hai mô hình quan sát → GO; ≤ 1/4 ở cả hai → NO-GO; còn lại → trình GVHD.
- Thăm dò (không dùng kết luận): `tauS` so với `tauD`; độ nhạy MAE của `tau_τ*` qua 50 phân hoạch Louvain.

## 3. D2 — đặt monitor (observer)
- k = 1. Mỗi (đồ thị, quan sát): 80 cascade val + 150 test; mọi chiến lược dùng chung cascade (so sánh cặp).
- Quan sát: chỉ thấy thời điểm nhiễm (bước) của observer đã nhiễm.
- Bộ định vị (giống nhau cho mọi chiến lược), dạng Pinto-lite: với ứng viên s, hồi quy bình phương nhỏ nhất t_o = t0 + c·d(s,o) trên observer đã nhiễm (t0, c ước lượng tự do, c ≥ 0); điểm = tổng bình phương phần dư. Với ic_T loại ứng viên vi phạm t_o ≥ d(s,o). Hòa → gần observer nhiễm sớm nhất. Không observer nào nhiễm → đoán node bậc cao nhất (ghi lại tỉ lệ). *(Sửa sau chạy thử 07/11, trước khi khóa: bản λ = 1/β cố định trượt V-D2 với si_t, ED full = 2,88, vì độ trễ thực mỗi hop trên đồ thị nhiều chu trình nhỏ hơn 1/β.)*
- Ngân sách b ∈ {5%, 10%} số node.
- Chiến lược không dùng cộng đồng (họ N): `rand` (trung bình 3 lần rút), `deg`, `btw` (betweenness), `spread` (farthest-first, bắt đầu từ node bậc cao nhất).
- Chiến lược dùng cộng đồng (họ C), phân hoạch mặc định: `cprop_def` (chia b theo D'Hondt trên kích thước cộng đồng, trong cộng đồng lấy bậc cao), `cbound_def` (cùng cách chia, trong cộng đồng lấy node có nhiều cạnh sang cộng đồng khác).
- Tham chiếu: `cprop_truth`, `cbound_truth`; `full` (mọi node là observer).
- **Kiểm tra hợp lệ V-D2:** ED trung bình của `full` ≤ 1,0 hop (tính riêng từng mô hình quan sát). Trượt → kết quả D2 của mô hình đó không đọc được.
- Metric chính: ED (hop) của nguồn dự đoán; phụ: hạng phần trăm của nguồn thật, tỉ lệ không observer nào nhiễm.
- Chọn đại diện họ trên val, so trên test. Một (đồ thị, b) đạt khi ED_N − ED_C ≥ min(0,3; 10% ED_N) **và** Wilcoxon một phía p < 0,01. Đồ thị đạt khi đạt ở ≥ 1 ngân sách.
- **Kết luận D2:** như D1 (≥ 3/4 ở cả hai quan sát hợp lệ → GO; ≤ 1/4 ở cả hai → NO-GO; còn lại → trình GVHD).

## 4. Giới hạn đã biết
- 4 đồ thị, 1 đồ thị/μ: pilot, không phải thí nghiệm chính thức. GO ở pilot → viết giao thức chính thức 16 đồ thị, seed mới.
- Chỉ Louvain. NetSleuth (MDL) chưa có: bản GraphSL 0.15 nhận k cho trước, không ước lượng k.
- D2 chỉ k = 1; bộ định vị chỉ dùng thời điểm của observer đã nhiễm, không dùng thông tin observer chưa nhiễm.
- F1@1 khi k̂ ≠ k: dùng thay ED vì ED Hungarian ghép min(|Ŝ|,|S|) cặp thưởng đoán thừa (lỗi đo của H0).

Không đổi ngưỡng, tiêu chí, quy tắc sau khi xem kết quả. Mọi kết quả đều báo cáo.
