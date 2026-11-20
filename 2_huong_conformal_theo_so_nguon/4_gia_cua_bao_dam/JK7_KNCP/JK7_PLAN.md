# J-K7 — KN-CP (k-nested conformal) — giao thức khóa trước

Khóa 18/11/2026 trước khi chạy. Dữ liệu, 9 cấu hình × 3 hàm điểm, pow 0,3, α = 0,10, 50 lần lặp, cal 5600 / test 400 như J-K5.

## Kiểm tính mới trước khi chạy
- MOPI (Bao et al., arXiv 2603.23374, 2026): Z dùng lúc hiệu chỉnh, ẩn lúc kiểm tra. Bảo đảm chỉ xấp xỉ (cận MSCE). Khi Z không phải hàm của X, cận có số hạng không triệt tiêu, nên không có bảo đảm chính xác theo nhóm. Ở bài toán này k không phải hàm của X → MOPI không có bảo đảm chính xác theo k. Không chạy MOPI ở pilot (tối ưu không lồi, cần cài lại); để làm baseline nếu pilot GO.
- **Nhận xét tự kiểm:** KN-CP = MDCP (Yang & Jin 2026) áp lên một hàm điểm thiết kế riêng r(x, y) (chỉ số tập lồng nhau, có cổng K̂). Bảo đảm chính xác theo từng k suy ra trực tiếp từ định lý của MDCP. Phần mới là thiết kế điểm, không phải định lý. J-K5 cho thấy MDCP với điểm thô suy biến (cả đồ thị với `recall`), nên thiết kế điểm là chỗ quyết định.

## Phương pháp KN-CP
- Chia cal thành A (2800) và B (2800). RF dự đoán k và kcal như J-K5 (độc lập với A, B).
- K̂(x) = {c : 1 − P̂(c|x) ≤ q_c}, q_c là ngưỡng Mondrian mức α_k trên kcal; nếu rỗng thì lấy cả 15 k.
- t_c(β) = phân vị mức β của điểm lớp c trên A (thứ ⌈β(n_c+1)⌉, +∞ nếu vượt). Lưới β = 0,50; 0,505; …; 1,00.
- Họ lồng nhau C_β(x) = {v : s(v) ≤ max_{c∈K̂(x)} t_c(β)}. Trên B: r_i = β nhỏ nhất trong lưới để C_β phủ (recall ≥ pow).
- β_c = phân vị conformal mức 1 − α của {r_i : k_i = c}; β* = max_c β_c. Tập kiểm tra: C_{β*}(x).
- Bảo đảm: P(phủ | k = c) ≥ 1 − α với mọi c (Mondrian trên B, rồi β* ≥ β_c, tập lồng nhau).
- Bản chính KN: α_k = 0,05. Phụ: KN2 (α_k = 0,02), KN0 (K̂ = cả 15 k; kiểm tra tính nhất quán, kỳ vọng gần MD).
- So sánh: G, O, WCP, MD, KSU* (như J-K5).

## Kiểm tra cài đặt (trong chế độ smoke, không in số liệu)
Phủ được tính bằng ngưỡng tối thiểu m_i (số nguồn có điểm ≤ t đạt pow). Smoke so m_i với cách tính trực tiếp trên 300 mẫu × 5 ngưỡng; sai thì dừng.

## Đo
Độ phủ theo từng k gộp qua 50 lần lặp (≈ 1300 điểm mỗi k). Độ phủ lệch prior S1–S4 như J-K6, tính từ phủ theo k.

## Tiêu chí
- V1 (hợp lệ): KN phủ theo k thấp nhất ≥ 0,88 ở ≥ 25/27 tổ hợp, và ≥ 0,88 ở ≥ 103/108 ô lệch prior.
- E1 (hơn KSU*): trung bình tỉ số cỡ KN/KSU* ≤ 0,85 và KN nhỏ hơn ở ≥ 20/27.
- E2 (gần WCP): trung bình tỉ số cỡ KN/WCP ≤ 1,15.

## Kết luận định trước
- V1 ∧ E1 ∧ E2 → GO: phương pháp có bảo đảm, kích thước ngang phương pháp không bảo đảm.
- V1 ∧ E1 → MỘT PHẦN: cải thiện KSU*, chưa tới WCP.
- Trượt V1 hoặc E1 → NO-GO; dùng KSU* cho bài phân tích.
Không đổi tiêu chí sau khi xem kết quả.
