# J-K6 — lệch prior số nguồn k và đo lại độ phủ của K̂ — giao thức khóa trước

Khóa 18/11/2026 13:15, trước khi chạy. Dữ liệu và 9 cấu hình × 3 hàm điểm như J-K5; pow 0,3; α = 0,10; 50 lần lặp.

## Câu hỏi
1. Khi phân phối k ở tập kiểm tra khác lúc hiệu chỉnh (lệch prior, P(dữ liệu | k) giữ nguyên), phương pháp nào giữ được độ phủ ≥ 0,90 mà không cần dữ liệu đích?
   Về lý thuyết: KSU* và MDCP có bảo đảm theo từng k nên phủ mọi prior; G và WCP chỉ có bảo đảm biên dưới prior hiệu chỉnh.
2. Độ phủ theo lớp của K̂ (J-K5 đo được 0,91–0,93, mục tiêu 0,98) có phải do cách đo không?

## Thiết kế
- Mỗi lần lặp: cal = 4000 mẫu từ phần còn lại, test = 2000 mẫu còn lại (đổi so với J-K5 để có đủ điểm kiểm cho từng k).
- Độ phủ và kích thước theo từng k được gộp qua 50 lần lặp. Độ phủ/kích thước dưới prior đích π' = Σ_k π'(k) · giá trị theo k (chính xác, không lấy mẫu lại).
- Kịch bản π': S0 = prior tự nhiên của dữ liệu; S1 = đều trên k 1–3; S2 = đều trên k 11–15; S3 ∝ (16 − k)²; S4 ∝ k².
- Phương pháp: G, O (biết k), WCP, MD (MDCP), KSU* (α_k 0,02, α_s 0,08, K̂ hiệu chỉnh trên kcal ∪ cal). Code dùng lại `cq`, `wcp_thresholds` từ J-K5.
- K̂: độ phủ theo lớp = tỉ lệ gộp qua mọi lần lặp của sự kiện c ∈ K̂ với điểm kiểm có k = c.

## Tiêu chí (108 ô = 27 tổ hợp × 4 kịch bản lệch S1–S4)
- P1: KSU* phủ ≥ 0,88 ở ≥ 103/108 ô.
- P2: WCP phủ < 0,85 ở ≥ 27/108 ô (lệch prior làm WCP hỏng đáng kể).
- P3: K̂ phủ lớp thấp nhất (gộp) ≥ 0,96 ở ≥ 8/9 cấu hình (xác nhận J-K5 chỉ là thiên lệch đo).

## Kết luận định trước
- P1 ∧ P2 → "BẢO ĐẢM THEO k CÓ GIÁ TRỊ DƯỚI LỆCH PRIOR".
- P1, trượt P2 → "KSU* BỀN NHƯNG WCP CŨNG BỀN" (lợi thế chỉ còn trên lý thuyết).
- Trượt P1 → "KSU* KHÔNG BỀN" (xem lại giả định).
- P3 báo cáo riêng. Nếu trượt P3 thì ghi nhận nghi vấn vi phạm và kiểm lại code K̂.
Không đổi tiêu chí sau khi xem kết quả. Chạy thử `--smoke` (seed 900, 2 lần lặp, 1 cấu hình) chỉ in "smoke ok".
