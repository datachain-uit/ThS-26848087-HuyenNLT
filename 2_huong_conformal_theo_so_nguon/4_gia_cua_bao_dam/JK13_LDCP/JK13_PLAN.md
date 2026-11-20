# J-K13 — LD-CP: điểm độ sâu học được, trọng số hậu nghiệm k, bảo đảm theo từng k — giao thức khóa trước

Khóa 18/11/2026 ~18:00, trước khi chạy.

## Kiểm tính mới
- MDCP (Yang & Jin 2026): học điểm h(x,y) = Σ λ_k(x) p_k(y|x) cho nhãn đơn; không xử lý nhãn dạng tập, phủ một phần hay tập top-m; λ không dùng xác suất thuộc nhóm; không có đồ thị.
- CRC/LTT (Angelopoulos et al.): kiểm soát recall cho đa nhãn, chỉ biên.
- CF-GNN (Huang et al. 2023): sửa điểm theo topology cho phân loại nút, chỉ biên.
- → Chưa thấy: hàm điểm học được trong không gian độ sâu cho tập nguồn với phủ một phần, trọng số theo hậu nghiệm k, hiệu chỉnh đồng đều theo k.

## Phương pháp LD-CP
1. Chia ktr (1400) thành A1 (700) và A2 (700). Bộ xếp hạng lại học trên A1: GNN + cấu trúc (f) cho dữ liệu tác giả; chỉ cấu trúc (s) cho dữ liệu tự mô phỏng.
2. Mô hình phân phối độ sâu F̂(m | x, c): HGB đa lớp trên các ngăn độ sâu (mép 1,2,…,8,10,12,15,20,25,30,40,50,70,100,150,200,300,500,1000,2000,5000,n), học trên A2 với c = k thật.
   - Đặc trưng: 19 đặc trưng hình học của vùng nhiễm, |I|, 10 xác suất lớn nhất của bộ xếp hạng lại, tổng và entropy; cộng c, c/|I|, ⌈pow·c⌉.
3. Điểm h(x, m) = Σ_c w_c(x) F̂(m | x, c), với w_c ∝ λ_c · p̂(c | x).
   - p̂ trên A2: RF học trên A1 (ngoài mẫu). Trên cal/test: RF học trên cả ktr (như các baseline).
4. Điểm không phù hợp r = h(x, D − 1) (D = độ sâu thật). τ_c = phân vị conformal mức α = 0,10 của r trên cal lớp c; τ* = max_c τ_c (gộp max-p của MDCP).
5. Độ sâu dự đoán m(x) = mép nhỏ nhất có h > τ*; nếu m > |I| thì lấy cả đồ thị.
   - Bảo đảm: phủ ⇔ r ≤ τ*; P(phủ | k = c) ≥ 1 − α với mọi c, chính xác, không union bound.
6. λ (chỉ ảnh hưởng hiệu quả, không ảnh hưởng tính hợp lệ): tìm ngẫu nhiên 60 vector log λ ~ N(0; 0,7²) cộng λ = 1. Hiệu chỉnh τ* trên nửa đầu A2, đo kích thước trên nửa sau A2; chọn nhỏ nhất. Seed 13.

**Biến thể:**
- LD (chính): λ tìm như bước 6.
- LD-1: λ = 1 (bóc tách vai trò của λ).
- LD-u: w đều trên 15 k (bóc tách vai trò của hậu nghiệm k).

**Baseline cùng xếp hạng (không gian độ sâu, như J-K9/J-K12):** G, O, WCP, MDCP (độ sâu thô), KSU* (α_k 0,02, α_s 0,08).

## Dữ liệu
- (a) 9 cấu hình của tác giả, xếp hạng f.
- (b) 18 thiết lập J-K12A (cùng seed → cùng dữ liệu), xếp hạng s.
- 50 lần lặp, cal 5600 / test 400. Phủ theo k gộp kèm cận Wilson; lệch prior S1–S4.

## Tiêu chí (27 tập dữ liệu)
- V: LD phủ theo k thấp nhất ≥ 0,88 ở ≥ 25/27 và lệch prior ≥ 0,88 ở ≥ 103/108 ô.
- E1: trung bình tỉ số kích thước LD/KSU* ≤ 0,85 và LD < KSU* ở ≥ 20/27.
- E2: trung bình tỉ số LD/WCP ≤ 1,10.

## Kết luận định trước
- V ∧ E1 ∧ E2 → GO: phương pháp mới có bảo đảm theo k, kích thước ngang WCP.
- V ∧ E1 → MỘT PHẦN: cải thiện rõ so với phương pháp có bảo đảm.
- Còn lại → NO-GO.
Không đổi tiêu chí sau khi xem kết quả. Smoke: 1 thiết lập tự mô phỏng nhỏ + 1 cấu hình tác giả, 2 lần lặp, seed 900. Kiểm tra trong smoke: (i) h không giảm theo m; (ii) phủ ⇔ r ≤ τ* trên 300 điểm; chỉ in "smoke ok".

## Ghi chú minh bạch (18:20, trước lần chạy chính)
Lần chạy thử đầu bị dừng vì quá chậm (gọi HGB từng mẫu). Đã gộp các lời gọi dự đoán thành lô; kết quả số học không đổi. Phương pháp, dữ liệu và tiêu chí không đổi. Lần chạy thử đó chưa in số liệu nào.
