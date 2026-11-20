# J-K10 — tổng quát hóa các kết luận của bài phân tích sang SI/IC/SIR tự mô phỏng — giao thức khóa trước

Khóa 18/11/2026 ~15:35, trước khi chạy. Lý do: mọi kết quả J-K → J-K9 dùng đầu ra GNN của tác giả, chỉ SIR, đồ thị 58–774 nút. Reviewer sẽ hỏi về mô hình lan truyền khác và đồ thị khác.

## Thiết lập
- Đồ thị (1000 nút, từ `3_D1_D2_pilot/data`): lfr_mu0.1_0, lfr_mu0.5_0, email_eu (986 nút).
- Mô hình: SI (β 0,3, `e0.si_fixed`), IC (p 0,2), SIR (β 0,3, γ 0,3) (`pk2.ic_fixed`, `pk2.sir_fixed`); vùng nhiễm cố định 5% số nút (≈ 50).
- k đều trên 1..15, nguồn chọn ngẫu nhiên đều; mô phỏng tắt sớm thì lấy lại nguồn. 8000 mẫu mỗi thiết lập (9 thiết lập), seed gốc 20261118 + chỉ số thiết lập.
- Không có GNN: bộ chấm điểm nút = HGB chỉ đặc trưng cấu trúc (xếp hạng "s" của J-K9), học trên ktr. Bộ phân loại k = RF trên `jk.feats`, như J-K.
- Chia mẫu như J-K5: ktr 1400, kcal 600, cal 5600, test 400, 50 lần lặp. Không gian độ sâu, phủ = recall ≥ 0,3.
- Phương pháp: G, O, WCP, MDCP, KSU* (như J-K9). Phủ theo k gộp; lệch prior S1–S4.

## Tiêu chí
- Q1 (chẩn đoán tổng quát hóa): G phủ theo k thấp nhất < 0,80 ở ≥ 6/9 thiết lập.
- Q2 (WCP thiếu phủ theo k): WCP phủ theo k thấp nhất < 0,85 ở ≥ 6/9.
- Q3 (KSU* hợp lệ): phủ theo k thấp nhất ≥ 0,88 ở ≥ 8/9 và lệch prior ≥ 0,88 ở ≥ 34/36 ô.
- Q4 (mô tả, không quyết định): tỉ số kích thước KSU*/WCP và KSU*/O; dự kiến 1,2–2.

## Kết luận định trước
- Q1 ∧ Q2 ∧ Q3 → "TỔNG QUÁT HÓA": các kết luận chính đứng ngoài dữ liệu tác giả.
- Q3 đạt, Q1 hoặc Q2 trượt → "MỘT PHẦN": bảo đảm đứng; mức độ thất bại của G/WCP phụ thuộc thiết lập (ghi rõ thiết lập nào).
- Q3 trượt → xem lại giả định hoán đổi hoặc cài đặt.
Không đổi tiêu chí sau khi xem kết quả. Smoke: 1 thiết lập, 600 mẫu, seed 900, 2 lần lặp; kiểm tra mô phỏng (đúng số nút nhiễm, nguồn ⊂ vùng nhiễm) và luật phủ độ sâu; chỉ in "smoke ok".
