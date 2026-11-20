# J-K19b — Chẩn đoán sau J-K19: đánh giá trong họ bằng xoay vòng hiệu chỉnh/kiểm tra — KHÓA TRƯỚC KHI CHẠY

Khóa: 20/11/2026 ~19:10 (giờ VN). ĐÂY LÀ THÍ NGHIỆM THEO SAU một kết quả trượt (J-K19: "CẦN XEM LẠI"); kết luận J-K19 giữ nguyên, không bị thay.

## Lý do
Ở J-K19, oracle O (bảo đảm lý thuyết 0,90 theo nhóm) chỉ có phủ k xấu nhất trung vị 0,87, thấp nhất 0,82; ca KSU*-mk trượt (0,855) trùng ô với O 0,831.
Giả thuyết: thiết kế đánh giá dùng tập hiệu chỉnh gần cố định (5 600/6 000 mẫu cùng kho) và kho kiểm tra riêng → đo phủ CÓ ĐIỀU KIỆN theo tập hiệu chỉnh;
min trên 15 giá trị k của đại lượng này kỳ vọng ≈ 0,87 dù phương pháp hợp lệ. Lý thuyết conformal chỉ bảo đảm trung bình trên tập hiệu chỉnh.

## Thiết kế
Giữ nguyên J-K19 (cùng seed, cùng dữ liệu hiệu chỉnh mô phỏng, cùng mô hình, cùng 8 phương pháp, cùng α), chỉ đổi đánh giá TRONG HỌ:
mỗi lần lặp, với từng cơ chế, hoán vị kho 6 000 mẫu → 5 600 hiệu chỉnh + 400 kiểm tra (như J-K11/J-K16). Bỏ kiểm tra ngoài họ (đã có ở J-K19).

## Tiêu chí
- Kiểm thiết kế: O ≥ 0,88 ở k xấu nhất ở ≥ 34/36 bộ. Trượt → "KHÔNG KẾT LUẬN ĐƯỢC" (giả thuyết thiết kế sai).
- V1, V2: giống hệt J-K19 (KSU*-mk ≥ 0,88 ở ≥ 34/36 và không bộ nào < 0,86; nhỏ hơn MD-mk ở ≥ 27/36).
- Kết luận: O đạt ∧ V1 ∧ V2 → "ĐẠT (chẩn đoán)"; báo kèm J-K19 đầy đủ trong bài.

## Ghi chú minh bạch
- Chạy thử trên shell phụ (19:04): `_tmp_smoke_test_b.py` là bản sao chỉ đổi đường dẫn lưu thử; không dùng cho chạy chính.
