# J-K4 — biến thể có bảo đảm (KS-U) và so với baseline cùng họ (WCP)

Viết 18/11/2026, **trước khi chạy**. Seed 20261118 / 20261119. Dữ liệu, điểm, chia mẫu như J-K3; pow = 0,3; 9 cấu hình × 3 hàm điểm (recall, prec, min) = 27 tổ hợp.

## Lý thuyết (biến thể KS-U)
Ký hiệu Y = tập nguồn, k = |Y|. Biến nhóm g(X, Y) = |Y| là hàm của nhãn, nên dùng được Mondrian conformal theo k (Vovk et al.).
1. **Tập k có bảo đảm theo từng lớp:** hiệu chỉnh riêng ngưỡng q_c cho từng k = c trên tập hiệu chỉnh của mô hình k (Mondrian/label-conditional): K̂(x) = {c : 1 − p̂_c(x) ≤ q_c}. Khi đó P(k ∈ K̂(X) | k = c) ≥ 1 − α_k với mọi c.
2. **Ngưỡng tập nguồn theo từng k:** t_c = ngưỡng conformal mức α_s trên các mẫu hiệu chỉnh có k = c. Khi đó P(cover với ngưỡng t_c | k = c) ≥ 1 − α_s.
3. **KS-U:** C(x) = {v : s(x, v) ≤ max_{c ∈ K̂(x)} t_c} (hợp các tập Mondrian của mọi k trong K̂). Nếu k ∈ K̂(x) thì C(x) ⊇ tập dùng t_k.
4. **Mệnh đề:** với mọi c, P(cover | k = c) ≥ 1 − α_s − α_k (bất đẳng thức hợp, hai tập hiệu chỉnh độc lập, trao đổi được trong từng lớp k). Chọn α_s = α_k = 0,05 → bảo đảm ≥ 0,90 cho **từng** k.
- KS (gộp tập hiệu chỉnh theo K̂) dùng ở J-K/J-K2/J-K3 **không** có bảo đảm này; KS-U là phiên bản có bảo đảm, có thể bảo thủ hơn.

## Baseline cùng họ
- **WCP** (Wang et al., arXiv 2506.05583, 2025): ngưỡng q̂ nhỏ nhất thỏa Σ_c λ̂_c(x) · m_c(q̂)/(n_c + 1) ≥ 1 − α, với λ̂ = xác suất k từ mô hình k, m_c(q) = số mẫu hiệu chỉnh lớp c có điểm ≤ q. Bảo đảm của họ là độ phủ **biên** (khi mô hình nhóm Bayes-optimal / multicalibrated). α = 0,10.
- G (gốc), O (biết k, Mondrian mức 0,10), KS (gộp, mức 0,10).

## Tiêu chí (khóa)
- **T1 (bảo đảm đúng trên thực nghiệm):** độ phủ thấp nhất theo nhóm k {1–3, 4–7, 8–11, 12–15} của KS-U ≥ 0,88 ở ≥ 90% tổ hợp (≥ 25/27).
- **T2 (baseline cùng họ không giải quyết):** độ phủ nhóm thấp nhất của WCP < 0,85 ở ≥ 50% tổ hợp (≥ 14/27).
- Kết luận: T1 đạt → "KS-U CÓ BẢO ĐẢM, KIỂM CHỨNG". T2 đạt → "WCP KHÔNG THAY ĐƯỢC". Báo cáo kích thước tập của mọi phương pháp, đặc biệt KS-U so với O và G.

## Giới hạn
- Bảo đảm KS-U giả định trao đổi được trong từng lớp k; với đầu ra GNN của tác giả, chưa có lệch mô hình. Mọi kết quả đều báo cáo.
