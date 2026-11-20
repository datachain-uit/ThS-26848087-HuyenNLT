# J-K11 — đồ thị lớn (10 000 nút) và khoảng tin cậy — giao thức khóa trước

Khóa 18/11/2026 ~16:00, trước khi chạy. Tiếp J-K10 (MỘT PHẦN: Q1 5/9, Q2 7/9, Q3 đạt). Kiểm hai giới hạn còn lại: kích thước đồ thị và độ bất định của các con số.

## Thiết lập
- Đồ thị: lfr10k_mu0.1_0, lfr10k_mu0.3_0 (10 000 nút, `4_P6F/data`).
- Mô hình: SI, IC, SIR như J-K10. Vùng nhiễm: 50 nút (0,5%) và 200 nút (2%) → 2 × 3 × 2 = 12 thiết lập.
- k đều 1..15; 8000 mẫu mỗi thiết lập; seed gốc 20261118 + chỉ số thiết lập.
- Bộ chấm điểm nút: HGB chỉ đặc trưng cấu trúc (như J-K10). Bộ phân loại k: RF trên `jk.feats`. Chia mẫu, phương pháp (G, O, WCP, MDCP, KSU*) và độ đo như J-K10.
- Khoảng tin cậy:
  - Phủ theo k: khoảng Wilson 95% trên số điểm kiểm gộp của từng k (~1300); báo cận dưới tại k xấu nhất.
  - Kích thước: trung bình ± 1,96 × sai số chuẩn qua 50 lần lặp.

## Tiêu chí
- Q1: G phủ theo k thấp nhất < 0,85 ở ≥ 6/12.
- Q2: WCP phủ theo k thấp nhất < 0,85 ở ≥ 6/12.
- Q3: KSU* phủ theo k thấp nhất ≥ 0,88 ở ≥ 11/12 và lệch prior ≥ 0,88 ở ≥ 46/48 ô.
- Q4 (mô tả): KSU*/WCP, KSU*/O; hướng thiếu phủ của G (k nhỏ hay k lớn) theo mô hình lan truyền.

## Kết luận định trước
- Q1 ∧ Q2 ∧ Q3 → "TỔNG QUÁT HÓA SANG ĐỒ THỊ LỚN".
- Q3 đạt, Q1 hoặc Q2 trượt → "MỘT PHẦN".
- Q3 trượt → xem lại.
Không đổi tiêu chí sau khi xem kết quả. Smoke: 1 thiết lập, 600 mẫu, seed 900; kiểm tra mô phỏng và luật phủ; chỉ in "smoke ok".
