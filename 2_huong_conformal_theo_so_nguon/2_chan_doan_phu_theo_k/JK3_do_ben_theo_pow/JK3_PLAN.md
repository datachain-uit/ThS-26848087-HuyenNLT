# J-K3 — độ bền của phát hiện F1 theo hàm điểm và mức pow

Viết 18/11/2026, **trước khi chạy**. Seed 20261118 (chia k-model) và 20261119 (lặp hiệu chỉnh). Thiết lập như J-K/J-K2 (α = 0,10, 50 lần lặp 5600/400, tập k α_k = 0,05), trên 9 cấu hình {highSchool, sfhh, bkFratB} × R0 {1–15, 11–25, 21–35}.

## Câu hỏi
F1 (phương pháp gốc phủ kém ở dịch ít nguồn, k 1–3) có phụ thuộc vào hàm điểm `recall` và mức pow 0,3 không?

## Biến thể
- Hàm điểm của tác giả: `recall` (recall_score), `prec` (avg_score), `min` (min_score) — đúng cặp hàm hiệu chỉnh / kiểm tra mà `main.py` dùng cho set_recall, set_prec, set_min.
- pow_expected ∈ {0,3; 0,5; 0,7}; "phủ" = tỉ lệ nguồn thật trong tập ≥ pow (định nghĩa của tác giả).
- 9 × 3 × 3 = 81 tổ hợp.

## Tiêu chí (khóa)
- Tổ hợp hợp lệ: độ phủ biên của G trong [0,87; 0,93].
- **F1 BỀN** nếu G phủ < 0,85 ở nhóm k 1–3 trong ≥ 80% tổ hợp hợp lệ; **KHÔNG BỀN** nếu ≤ 40%; còn lại **BỀN MỘT PHẦN**.
- Mô tả kèm: KS và O (độ phủ nhóm thấp nhất, kích thước) theo hàm điểm × pow.

## Giới hạn
- Đầu ra GNN của tác giả; một α. Mọi kết quả đều báo cáo.
