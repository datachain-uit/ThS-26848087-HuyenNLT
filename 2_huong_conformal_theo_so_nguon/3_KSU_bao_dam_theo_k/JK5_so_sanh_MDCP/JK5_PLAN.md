# J-K5 — KS-U so với MDCP (Yang & Jin, ICML 2026) — giao thức khóa trước

Khóa 18/11/2026 trước khi chạy. Dữ liệu, cấu hình, pow 0,3, α = 0,10, 50 lần lặp, chia mẫu: giống J-K4.

## Câu hỏi
MDCP (arXiv 2601.02998) cho độ phủ đồng đều theo nhóm mà không cần biết nhóm khi kiểm tra: tập = hợp các tập conformal theo từng nhóm, mỗi tập ở mức α. Với một hàm điểm chung cho mọi k, điều này thành ngưỡng max_c t_c(α) trên cả 15 giá trị k.
KS-U chỉ lấy max trên tập k ước lượng K̂, trả α_k cho việc này. Câu hỏi: K̂ có làm tập nhỏ hơn MDCP mà vẫn giữ bảo đảm theo từng k không?

## Phương pháp
- G (Jian et al.), O (biết k thật), WCP (Wang et al., ICLR 2026, arXiv 2506.05583): như J-K4. WCP được vector hóa, công thức không đổi.
- MD: MDCP, ngưỡng max_c t_c(0,10) trên 15 k. Bảo đảm P(phủ | k) ≥ 0,90. Phần học điểm (learned score) của MDCP không áp dụng được vì không gian nhãn là tập con nút; ghi rõ là giới hạn.
- KSU*: **phương pháp chính**. α_k = 0,02, α_s = 0,08. K̂ Mondrian hiệu chỉnh trên kcal ∪ cal (dùng chung cal là hợp lệ vì union bound không cần độc lập).
- Phụ: KSUa (0,05 / 0,05, chung), KSUc (0,01 / 0,09, chung), KSU4 (0,05 / 0,05, chỉ kcal, như J-K4).
- Mọi bản KS-U và MD: bảo đảm P(phủ | k = c) ≥ 0,90 với mọi c.
- Sửa lỗi: quantile conformal trả +∞ khi mức ⌈(1−a)(n+1)⌉ > n (hàm `cpquantile` của tác giả trả max).

## Tiêu chí (27 tổ hợp = 9 cấu hình × 3 hàm điểm)
- C1 (hợp lệ): KSU* và MD phủ nhóm thấp nhất ≥ 0,88 ở ≥ 25/27.
- C2 (K̂ có giá trị): cỡ KSU* < cỡ MD ở ≥ 20/27 và trung bình tỉ số cỡ KSU*/MD ≤ 0,85.
- C3 (giá của bảo đảm): trung bình tỉ số cỡ KSU*/WCP ≤ 1,25.

## Kết luận định trước
- C1 ∧ C2 ∧ C3 → GO: KSU* là đóng góp phương pháp có bảo đảm, tập gần WCP.
- C1 ∧ C2, trượt C3 → MỘT PHẦN: K̂ thêm giá trị so với MDCP nhưng bảo đảm vẫn đắt; hợp với bài phân tích.
- Trượt C1 hoặc C2 → NO-GO cho KS-U như đóng góp phương pháp.
Chỉ báo cáo; không đổi tiêu chí hay phương pháp chính sau khi xem kết quả.

## Chạy thử
Launcher chạy chế độ `--smoke` trước (1 cấu hình, 2 lần lặp, seed 900), chỉ in "smoke ok", không in số liệu.
