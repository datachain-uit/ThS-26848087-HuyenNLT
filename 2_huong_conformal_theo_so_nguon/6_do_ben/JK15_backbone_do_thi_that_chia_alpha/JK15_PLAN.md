# J-K15 — Độ bền theo backbone, đồ thị thật, và cách chia α (KHÓA TRƯỚC KHI CHẠY)

Khóa: 19/11/2026 ~08:45 (giờ VN), trước khi có bất kỳ kết quả nào. SHA của file này và script được ghi vào báo cáo.

## Mục đích
Kiểm tra độ bền của các đóng góp C1 (G thất bại theo k), C2 (KSU* hợp lệ mọi k) trước các câu hỏi reviewer dễ hỏi.
Đây là thí nghiệm độ bền, không phải đóng góp mới → không cần kiểm tính mới trong tài liệu.

## Phần A — backbone GNN thứ hai (dữ liệu tác giả, 9 cấu hình, hàm điểm recall như J-K12B)
- Backbone mới: GCN 3 lớp (ẩn 64, ReLU, dropout 0,1) trên đồ thị gốc, chuẩn hóa D^-1/2(A+I)D^-1/2.
  Đặc trưng nút (5 kênh, kiểu GCNSI/LPSI): d∈{+1 nhiễm, −1 không}; M·d; M·max(d,0) với M = 0,5·(I − 0,5·S)^-1, S = D^-1/2 A D^-1/2;
  log(1+bậc)/max; tỉ lệ hàng xóm nhiễm.
- Huấn luyện CHỈ trên ktr (1 400 mẫu, cùng hoán vị seed 20261118 như J-K12B). Loss BCE có pos_weight, chỉ trên nút nhiễm.
  60 epoch, batch 32, Adam lr 3e-3, weight decay 1e-4, torch seed 0. Xác suất nút không nhiễm = 0.
- Cùng bộ phân loại k (RF), cùng chia cal/test, 50 lần lặp, seed như J-K12B. Phương pháp: G, O, WCP, MDCP, KSU* (α_k 0,02, α_s 0,08).
- Kiểm chất lượng (đọc kèm, không quyết định): AUC nguồn trong nút nhiễm trên rest; so kích thước O với SD-STGCN.
- Tiêu chí:
  - A1: phủ ở k xấu nhất của G < 0,85 ở ≥ 7/9 cấu hình.
  - A2: KSU* phủ ở k xấu nhất ≥ 0,88 ở 9/9 cấu hình VÀ phủ dưới lệch prior S1–S4 ≥ 0,88 ở 36/36.
  - Kết luận: A1 ∧ A2 → "BỀN THEO BACKBONE"; chỉ A2 → "MỘT PHẦN (C2 bền, C1 phụ thuộc backbone)"; A2 trượt → "CẦN XEM LẠI".

## Phần B — đồ thị thật ngoài LFR (mô phỏng như J-K11)
- Đồ thị: power_grid (4 941 nút), cora_ml (2 810 nút) từ GraphSL 0.15. Chuyển về vô hướng, nhãn nút 0..n−1.
- SI/IC/SIR × vùng nhiễm 50 và 200 → 12 thiết lập. Mọi thứ khác y hệt J-K11 (điểm nút HGB cấu trúc, 8 000 mẫu, 50 lần lặp).
- Quy tắc loại (khóa trước): nếu sau 400 000 lần thử chưa đủ 8 000 mẫu (lan truyền tắt trước khi đạt kích thước), thiết lập được ghi "không mô phỏng được" và loại.
- Tiêu chí:
  - B1: G < 0,85 ở k xấu nhất ở ≥ một nửa số thiết lập mô phỏng được.
  - B2: KSU* ≥ 0,88 ở k xấu nhất ở mọi thiết lập mô phỏng được.
  - Kết luận: B1 ∧ B2 → "TỔNG QUÁT HÓA"; chỉ B2 → "MỘT PHẦN"; B2 trượt → "CẦN XEM LẠI".

## Phần C — độ nhạy cách chia α (dữ liệu tác giả, cả hai backbone, recall)
- α_k ∈ {0,005; 0,01; 0,02; 0,03; 0,05}, α_s = 0,10 − α_k.
- Tiêu chí C1: kích thước KSU* ở α_k = 0,02 ≤ 1,10 × kích thước nhỏ nhất trong 5 cách chia, ở ≥ 7/9 cấu hình (mỗi backbone).
  Đạt → "mặc định 0,02 hợp lý"; trượt → báo cách chia tốt nhất và đề xuất quy tắc chọn (KHÔNG đổi mặc định trong bài chính sau khi xem).
- Mọi cách chia đều có bảo đảm 0,90 theo lý thuyết; báo kèm phủ ở k xấu nhất.

## Không thay đổi sau khi xem kết quả
Ngưỡng, siêu tham số GCN, đồ thị, quy tắc loại đều cố định ở đây. Chạy thử (--smoke) chỉ để kiểm cài đặt, không đọc số.

## Ghi chú minh bạch (sau khi khóa, trước khi có kết quả)
- 09:00: chạy thử dừng vì .venv có torch thiếu pandas (module `data_utils` của tác giả import pandas nhưng hàm điểm không dùng). Thêm module pandas rỗng lúc import code tác giả rồi gỡ ngay (để sklearn không nhầm). Tương tự gỡ module tensorflow giả do jk.py chèn (torch không chịu). Không đổi gì về phương pháp/tiêu chí.
