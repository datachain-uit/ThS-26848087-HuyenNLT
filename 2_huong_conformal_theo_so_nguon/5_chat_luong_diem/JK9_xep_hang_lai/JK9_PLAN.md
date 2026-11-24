# J-K9 — xếp hạng lại theo cấu trúc: so sánh công bằng — giao thức khóa trước

Khóa 18/11/2026 15:10, trước khi chạy. Khẳng định lại quan sát hậu kiểm của J-K8 (Df-KSU 11,9 so với Dg-KSU 41,9). Cùng seed, cấu hình và chia mẫu như J-K8.

## Kiểm tính mới
- Sterchi et al. (arXiv 2512.20657, 2026), benchmark GNN định vị nguồn: GNN vượt Jordan center, betweenness, SME, MCMF, MLP trên phần lớn chỉ số. Không bàn xếp hạng lại hay hiệu chỉnh hậu kiểm; chỉ đơn nguồn; không có conformal.
- → Xếp hạng lại đầu ra GNN bằng cấu trúc trong bối cảnh đa nguồn, kèm conformal: chưa thấy. Benchmark trên ngược chiều với J-K8, nên cần đối chứng "chỉ cấu trúc" và "heuristic Jordan".

## Bốn xếp hạng (cùng định nghĩa độ sâu như J-K8)
- g: xác suất GNN (SD-STGCN của tác giả).
- f: HGB trên đặc trưng chung J-K8 (GNN + cấu trúc), học trên ktr.
- s: HGB chỉ đặc trưng cấu trúc (bỏ logit/thứ hạng GNN), học trên ktr.
- j: heuristic, khoảng cách tới tâm Jordan của I tăng dần (hòa: bậc trong I lớn hơn trước). Không học.

## Phương pháp (mỗi xếp hạng; không gian độ sâu; phủ = recall ≥ pow)
G (ngưỡng chung α 0,10), O (biết k), WCP (Wang et al., trọng số P̂(k|x) trên độ sâu), MD (MDCP), KSU* (α_k 0,02 trên kcal ∪ cal, α_s 0,08). Ngưỡng > |I| → cả đồ thị.

## Đo
Phủ theo từng k gộp qua 50 lần lặp; kích thước trung bình; phủ dưới lệch prior S1–S4 (như J-K6).

## Tiêu chí (9 cấu hình)
- A (xếp hạng lại có tác dụng): với cả WCP và KSU*, cỡ(f) ≤ 0,5 × cỡ(g) ở ≥ 7/9 cấu hình.
- B (giá của bảo đảm): trung bình cỡ KSU*-f / WCP-f ≤ 1,15.
- C (hợp lệ): KSU*-f phủ theo k thấp nhất ≥ 0,88 ở ≥ 8/9; phủ lệch prior ≥ 0,88 ở ≥ 34/36 ô.
- D (đọc kèm, không quyết định): nếu cỡ KSU*-s ≤ 1,1 × KSU*-f ở ≥ 7/9 → "GNN không thêm giá trị so với cấu trúc".

## Kết luận định trước
- A ∧ B ∧ C → GO: phương pháp hai tầng (xếp hạng lại + hiệu chỉnh theo k).
- A ∧ C, trượt B → PHÁT HIỆN: xếp hạng lại là đóng góp chính; hiệu chỉnh theo k là phân tích kèm.
- Trượt A → quay về bài phân tích.
Không đổi tiêu chí sau khi xem kết quả. Smoke: seed 900, 2 lần lặp, 1 cấu hình; kiểm tra quy tắc phủ (độ sâu ≤ M) khớp phép đếm trực tiếp trên 300 mẫu.
