# E0x — số cụm của vùng nhiễm có phụ thuộc số nguồn k không (E0c), và đặc trưng hình học có cứu được vùng nhiễm lớn không (E0a)

Ngày viết: 17/11/2026, **trước khi chạy**. Người quyết định: học viên. Seed gốc 20261117 (chưa dùng ở H0/H0b/H0c/H0p/D12/P6-F/E0).
Thay cho `ke_hoach_dem_17_11_E0x.md` bản 11:30 (đã sửa theo lượt tìm tài liệu chiều 17/11).

## Căn cứ
- E0 (14/11, seed 9191, chạy thử): số cộng đồng Louvain γ = 1 của đồ thị con nhiễm gần như phẳng theo k; đoán thừa tăng theo f và μ. **Dữ liệu seed 9191 không gộp vào E0x.**
- Tài liệu: Wang et al. (KBS 2021) giả định đồ thị nhiễm đa nguồn tự mang cấu trúc cộng đồng theo nguồn. Frąszczak (SNAM 2023) báo cáo đoán thừa, không đổi resolution, không có mô hình đối chứng (đọc ~100k/158k ký tự). Chưa thấy bài kiểm giả định này bằng đối chứng. Tín hiệu `comp` khi f nhỏ là ý đã có (OJC, Zhu–Chen–Ying), không tính là phát hiện. Ngưỡng bất khả theo thời gian đã có lý thuyết cho **vị trí** nguồn (Zhu & Ying), chưa thấy cho **số** nguồn.
- P6 đóng: H0c_fix cho η² ≤ 0,11 và 0/6 cặp đạt Đ2 ở mọi tổ hợp; chỉ mở lại nếu E0c bị BÁC.

## Thiết lập
- Đồ thị: `lfr_mu0.1_0`, `lfr_mu0.3_0`, `lfr_mu0.5_0`, `email_eu` (từ `../3_D1_D2_pilot/data`). Dùng lại nguyên hàm của `../5_E0_ho_so_da_thang/e0.py` (SI β = 0,3 kích thước cố định, k-center, Louvain seed 0).
- f ∈ {2, 5, 10, 15, 25, 40%}; k ∈ {1, 2, 3, 5, 8}. Ô = (đồ thị, f): 24 ô.
- Mỗi seed s, mỗi ô:
  - `rand`: nguồn chọn đều; 60 train + 60 test cascade mỗi k.
  - `btw`: k nguồn có betweenness cao nhất trong G (như Frąszczak); 30 cascade mỗi k; chỉ dùng cho E0c (mô tả).
  - `bfs`: đối chứng không có lan truyền đa nguồn — quả cầu BFS từ 1 node ngẫu nhiên, lớp cuối lấy ngẫu nhiên cho đủ round(f·n); 60 mẫu; chỉ mô tả.
- Số seed: mục tiêu 30, tối thiểu 10. Script ngừng nhận seed mới khi dự báo không kịp hạn `--deadline`. Dưới 10 seed: báo cáo ghi "THIẾU SEED", kết luận không có hiệu lực.

## E0c — tiêu chí (khóa)
Đại lượng chính c = số cộng đồng Louvain γ = 1 kích thước ≥ 3 (các γ khác chỉ báo cáo). Dữ liệu `rand`, gộp train + test, mọi seed.
- **Hc1 (c không bám theo k):** độ dốc OLS của c theo k; khoảng tin cậy 95% bootstrap theo cụm seed (2000 lần). Đạt ô khi cận trên < 0,25. Lý do: nếu "k̂ = số cụm" đúng thì độ dốc ≈ 1; 0,25 nghĩa là thêm 4 nguồn chưa làm tăng 1 cụm.
- **Hc2 (k = 8 tương đương k = 1):** TOST Welch trên c, biên ±1 cộng đồng (k̂ nguyên), α = 0,01 hiệu chỉnh Bonferroni theo 24 ô. Đạt ô khi cả hai phía p < 0,01/24.
- **Kết luận E0c:** Hc1 và Hc2 cùng đạt ≥ 20/24 ô → XÁC NHẬN (số cụm của vùng nhiễm không mang thông tin về k). Cả hai ≤ 9/24 → BÁC. Còn lại → CHƯA RÕ, báo cáo theo μ và f.
- Mô tả kèm, không dùng kết luận: c trung bình ở k = 1; độ dốc với nguồn `btw`; c của `bfs` so với k = 1; độ dốc của `comp`.

## E0a — tiêu chí (khóa)
Mỗi (seed, ô): RandomForestRegressor(300 cây, min_samples_leaf = 5) fit trên train, dự đoán làm tròn, cắt [1, 15].
- `const`, `N_reg` (comp, rho_1..6), `PN_reg` (+ c_γ, q_1.0), `U_reg` (+ hình học: đường kính, bán kính, phân vị 25/50/75/90 khoảng cách cặp, số cạnh biên, bậc trung bình và max trong G, bậc trung bình trong đồ thị con, tỉ lệ lá, số node có độ lệch tâm cực tiểu địa phương).
- **Ha2 (đặc trưng giàu hơn cứu vùng f lớn):** trên các ô f ∈ {15, 25, 40%} (12 ô), gộp sai số test mọi seed: MAE(`U_reg`) ≤ 0,8 × MAE(`N_reg`) và Wilcoxon một phía p < 0,01. Đạt khi ≥ 9/12 ô.
- Mô tả: skill = 1 − MAE/MAE(`const`) theo f, khoảng tin cậy bootstrap theo seed; MAE theo tam phân vị khoảng cách trung bình giữa các nguồn (k ≥ 2).
- Không gọi `U_reg` là "trần": nó không phải cận trên lý thuyết.

## Quyết định sau khi chạy
| E0c | Ha2 | Việc tiếp |
|---|---|---|
| XÁC NHẬN | đạt | D1 theo cơ chế mới (hình học, không phải cộng đồng); E0c làm động cơ. Kiểm tính mới: TP-MDV 2026, Luo–Tay–Leng 2013, graph-signal cover |
| XÁC NHẬN | trượt | Bài phân tích: giả định "cụm ↔ nguồn" không đứng + đường cong định danh. Đọc PDF Frąszczak đầy đủ, TP, TP-MDV |
| BÁC / CHƯA RÕ | bất kỳ | Phân tích vì sao lệch E0 trước khi làm gì thêm; mở lại câu hỏi P6 |

## Giới hạn đã biết
- Một bản đồ thị mỗi mức μ, n ≈ 1000: seed chỉ đổi cascade, suy luận có điều kiện theo 4 đồ thị này.
- Chỉ SI, kích thước vùng nhiễm ép cố định; chưa có IC/SIR.
- Huấn luyện và kiểm trên cùng đồ thị.
- Tính mới chưa xác minh trên Scholar/Scopus; TP-MDV 2026 chưa đọc.
- Mọi kết quả đều báo cáo, kể cả khi âm.

## Ghi chú minh bạch (thêm 17/11 23:05, sau khi lần chạy chính đã bắt đầu; phần tiêu chí ở trên không đổi)
- Lần chạy chính bắt đầu 22:58:40 trên Windows, 21 tiến trình, với plan SHA `f282386b350d729e` và e0x.py SHA `e23a58076297f443` (ghi trong logs/e0x.log). Bản này không đặt hạn: chạy đủ 30 seed rồi mới phân tích.
- Lần smoke đầu trên máy ảo vô tình dùng chỉ số seed 0–1 (6 cascade mỗi k), trùng phần đầu dòng ngẫu nhiên của seed 0–1 trong lần chạy chính; người chạy đã thấy bảng smoke đó. Tiêu chí viết trước smoke và không sửa. Script đã sửa để smoke dùng seed từ 900; bản smoke cũ ở `_ban_chay_thu_may_ao/`.
- 18/11 06:10: lần chạy đêm dừng ở 8 seed (dưới tối thiểu 10). Quyết định bù đến 10 seed đã đặt lúc 00:30, trước khi có kết quả. 08:13 bắt đầu chạy bù seed 8–9 (`--seeds 10`, e0x.py không đổi). 08:20 học viên yêu cầu đọc báo cáo tạm 8 seed (lưu ở `results/E0X_REPORT_tam_8seed.md`); kết luận chính thức lấy từ báo cáo 10 seed, không dừng sớm dựa trên báo cáo tạm.
