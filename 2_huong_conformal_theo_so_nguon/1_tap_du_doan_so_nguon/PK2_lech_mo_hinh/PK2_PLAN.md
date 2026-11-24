# P-K2 — tập dự đoán cho số nguồn k khi mô hình lan truyền bị lệch

Viết 18/11/2026, **trước khi chạy**. Người quyết định: học viên. Seed gốc 20261118 (chưa dùng ở các thí nghiệm trước).

## Căn cứ
- P-K (18/11): GO trong điều kiện thuận lợi (cùng đồ thị, cùng SI, lưới k thưa). Độ phủ 0,88–0,91 là tất yếu của conformal khi trao đổi được (exchangeable), chưa phải phát hiện.
- Jian et al. (AAAI 2026) nêu ảnh hưởng của lệch prior/mô hình là việc tương lai; bài của họ không ước lượng k. Tái lập phần conformal của họ khớp hoàn toàn (18/11); thí nghiệm của họ có vùng nhiễm trung bình ≈ 2,7% số nút.
- E0c: số cụm không mang thông tin về k → bỏ Louvain khỏi đặc trưng (tiết kiệm thời gian, không mất tín hiệu).

## Câu hỏi
1. Hiệu chỉnh trên SI rồi áp cho cascade IC hoặc SIR thì độ phủ giảm bao nhiêu?
2. Hiệu chỉnh trên hỗn hợp SI + IC + SIR có giữ được độ phủ ở cả ba mô hình không?
3. Với lưới k dày (1..10), tập có còn hữu dụng ở vùng nhiễm nhỏ không?

## Thiết lập
- Đồ thị: `lfr_mu0.1_0`, `lfr_mu0.3_0`, `lfr_mu0.5_0`, `email_eu`. f ∈ {2, 5, 10, 25%}. Ô = (đồ thị, f): 16 ô. k ∈ {1, …, 10}.
- Mô hình lan truyền, đều dừng khi tập từng nhiễm đúng round(f·n) nút (bước cuối lấy ngẫu nhiên đủ số):
  - SI: β = 0,3 (giống E0/E0x).
  - IC: mỗi nút mới nhiễm có một lần thử lây cho từng hàng xóm, p = 0,2; tắt trước khi đủ kích thước thì sinh lại.
  - SIR: β = 0,3, hồi phục γ = 0,3 mỗi bước; quan sát = tập từng nhiễm (I ∪ R).
- Mỗi seed, mỗi ô: SI 60 cascade/k; IC 30/k; SIR 30/k. 10 seed: 0–3 huấn luyện, 4–6 hiệu chỉnh, 7–9 kiểm tra.
- Đặc trưng (19): `comp`, `rho_1..6` (k-center), 12 đặc trưng hình học như E0x. Không dùng Louvain.
- Bộ phân loại: RandomForestClassifier(300 cây, min_samples_leaf = 5, random_state = 0).
- Phương pháp tập (α = 0,1, điểm 1 − p̂(y)):
  - `CP-SI`: huấn luyện và hiệu chỉnh trên SI (thực hành phổ biến: chỉ mô phỏng một mô hình).
  - `CP-MIX`: huấn luyện và hiệu chỉnh trên hỗn hợp SI + IC + SIR.
- Đối chứng: `pt` = {k̂}; `pm1` = [k̂ − 1, k̂ + 1] (k̂ từ RF trên SI); `kc` = quy tắc k-center (chọn bán kính ρ trên train SI, kiểu Jiang T(k)), báo MAE.

## Tiêu chí (khóa)
- **V (kiểm tra cài đặt):** độ phủ `CP-SI` trên test SI trong [0,85; 0,95] ở ≥ 14/16 ô. Trượt → kiểm code, không diễn giải.
- **U2 (hữu dụng, lưới dày):** kích thước tập `CP-SI` trên test SI ≤ 3,0 ở ≥ 6/8 ô có f ≤ 5%.
- **R (bền với lệch, hiệu chỉnh SI):** độ phủ `CP-SI` ≥ 0,80 trên test IC và trên test SIR ở ≥ 24/32 cặp (ô × mô hình lệch).
- **RM (bền nhờ hiệu chỉnh hỗn hợp):** độ phủ `CP-MIX` ≥ 0,85 trên mỗi mô hình ở ≥ 42/48 cặp (ô × {SI, IC, SIR}).
- **Kết luận:** V và U2 đạt, và (R hoặc RM) đạt → GO. Ghi rõ GO nhờ R hay chỉ nhờ RM. Ngược lại → NO-GO.
- Mô tả kèm: độ phủ theo từng k; kích thước tập của `CP-MIX` so với `CP-SI` (cái giá của bền vững); độ phủ của `pm1`; MAE của `kc` và `pt`.

## Giới hạn
- Một bản đồ thị mỗi mức μ; ba mô hình lan truyền với một bộ tham số; lệch mô hình trong hỗn hợp vẫn nằm trong họ mô hình đã thấy (chưa kiểm mô hình ngoài hỗn hợp).
- Chưa có baseline BP (`sib` cần biên dịch C++) và NetSleuth; để P-K3.
- Mọi kết quả đều báo cáo, kể cả khi âm.
