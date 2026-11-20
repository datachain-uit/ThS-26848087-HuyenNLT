# J-K17 (lệch mô hình lan truyền) và J-K18 (ảnh chụp thiếu nút) — KHÓA TRƯỚC KHI CHẠY

Khóa: 19/11/2026 ~15:10 (giờ VN), trước khi có kết quả. SHA file này và script ghi vào báo cáo.

## Mục đích
Bảo đảm conformal chỉ đúng khi dữ liệu hiệu chỉnh (phải mô phỏng) và dữ liệu triển khai cùng cơ chế.
Hai thí nghiệm đo điều gì xảy ra khi giả định đó sai — câu hỏi chính của reviewer về "kết quả mô phỏng":
- J-K17: hiệu chỉnh trên mô hình lan truyền A, triển khai trên mô hình B (khác loại hoặc khác tham số).
- J-K18: ảnh chụp triển khai thiếu một phần nút nhiễm (bị quan sát là không nhiễm), có thể gồm cả nguồn.
Không có phương pháp nào được bảo đảm dưới lệch; câu hỏi là KSU* suy giảm bao nhiêu so với G và WCP.
Thí nghiệm độ bền/giới hạn, không phải đóng góp phương pháp mới → không kiểm tính mới.

## Đường ống chung (giống J-K11, chỉ tách nguồn dữ liệu hiệu chỉnh và kiểm tra)
- Đồ thị: lfr10k_mu0.1_0 (10 000 nút, tổng hợp) và cora_ml (2 810 nút, cấu trúc thật). Vùng nhiễm cố định 50 hoặc 200.
- Dữ liệu hiệu chỉnh: 8 000 mẫu từ cơ chế A → ktr 1 400 (RF cho k, HGB điểm nút cấu trúc), kcal 600, kho 6 000 (rút 5 600 mỗi lần).
- Dữ liệu kiểm tra: 4 000 mẫu từ cơ chế B (seed riêng) → rút 400 mỗi lần. 50 lần lặp.
- Phương pháp G, O, WCP, MDCP, KSU* (α 0,10; α_k 0,02; α_s 0,08; pow 0,3), luật phủ và kích thước như J-K11.
- Mô hình: SI (β 0,3), IC (p 0,2), SIR (β 0,3, γ 0,3) như cũ; thêm SIR-nhanh (β 0,5, γ 0,3) và SIR-dài (β 0,3, γ 0,1) cho lệch tham số.

## J-K17 — thiết lập
- Lệch loại mô hình: (A, B) ∈ {SI, IC, SIR}², 9 cặp (3 cặp trùng = đối chứng) × 2 đồ thị × 2 kích thước = 36.
- Lệch tham số: SIR → SIR-nhanh, SIR → SIR-dài × 2 đồ thị × 2 kích thước = 8.
- Thiết lập không đủ mẫu sau 400 000 lần thử (như J-K15B) bị loại và ghi rõ.
- Tiêu chí (trên các thiết lập LỆCH mô phỏng được, gồm 6 cặp lệch loại + 2 lệch tham số):
  - Đối chứng: KSU* ≥ 0,88 ở k xấu nhất ở mọi thiết lập trùng (kiểm cài đặt; trượt → dừng tìm lỗi).
  - P1 (bền tương đối): KSU* phủ k xấu nhất > G ở ≥ 90% VÀ ≥ WCP ở ≥ 75% thiết lập lệch.
  - P2 (bền tuyệt đối): KSU* phủ k xấu nhất ≥ 0,85 ở ≥ 75% thiết lập lệch.
  - Kết luận: P1 ∧ P2 → "KSU* BỀN TRƯỚC LỆCH MÔ HÌNH"; chỉ P1 → "BỀN TƯƠNG ĐỐI, MẤT BẢO ĐẢM TUYỆT ĐỐI"; không P1 → "KHÔNG BỀN".
  - Mô tả kèm: cặp nào gây suy giảm lớn nhất; phủ biên; kích thước.

## J-K18 — thiết lập
- Che ngẫu nhiên tỉ lệ q ∈ {0,05; 0,15} nút nhiễm (kể cả nguồn) khỏi ảnh chụp. Nguồn bị che không thể nằm trong tập dự đoán trừ khi tập là cả đồ thị.
- Hai chế độ: "chỉ kiểm tra bị che" (hiệu chỉnh sạch — lệch) và "cả hai bị che" (hiệu chỉnh cùng cơ chế che — không lệch).
- SI/IC/SIR × 2 đồ thị × vùng nhiễm 50 × 2 q × 2 chế độ = 24 thiết lập.
- Tiêu chí:
  - Q1 (lý thuyết, "cả hai bị che"): KSU* ≥ 0,88 ở k xấu nhất ở 12/12.
  - Q2 ("chỉ kiểm tra bị che"): KSU* ≥ 0,85 ở k xấu nhất ở ≥ 75% của 12; Q3: KSU* > G ở ≥ 90% của 12.
  - Báo kích thước tăng bao nhiêu khi "cả hai bị che" (giá của quan sát thiếu).

## Ghi chú minh bạch
- 15:45: chạy thử trên shell phụ của máy (Linux, NO_VENV) để bắt lỗi sớm trong lúc J-K16 chiếm VS Code; file `_tmp_smoke_test.py` là bản sao jk17.py chỉ đổi đường dẫn lưu kết quả thử, không xóa được (không có quyền xóa), không dùng cho chạy chính.

## Không thay đổi sau khi xem kết quả
Mọi tham số, đồ thị, tỉ lệ che, ngưỡng tiêu chí cố định ở đây. Chạy thử chỉ để kiểm cài đặt.
