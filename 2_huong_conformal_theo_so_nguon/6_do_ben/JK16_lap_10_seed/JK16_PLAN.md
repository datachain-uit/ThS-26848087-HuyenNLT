# J-K16 — Độ lặp lại qua 10 seed (KHÓA TRƯỚC KHI CHẠY)

Khóa: 19/11/2026 ~14:40 (giờ VN), trước khi có kết quả. SHA file này và script ghi vào báo cáo.

## Mục đích
Các kết quả trước dùng 1 seed cho cách chia dữ liệu / bộ phân loại k / mô phỏng (50 lần chia cal–test).
J-K16 lặp lại toàn bộ đường ống với 10 seed để kiểm tra C1 (G thất bại theo k), C2 (KSU* hợp lệ) và C3 (giá ~ |K̂|) không phụ thuộc may rủi của một seed.
Thí nghiệm độ bền, không phải đóng góp mới → không kiểm tính mới.

## Thiết kế
- Seed s = 0..9. s = 0 trùng seed gốc → phải tái hiện đúng J-K12 (kiểm tra tính đúng).
- **Phần A (dữ liệu tác giả):** gọi đúng hàm `part_b` của J-K12 (9 cấu hình × 3 hàm điểm recall/prec/min, 50 lần chia), seed = 20261118 + 1000·s
  (đổi hoán vị ktr/kcal/rest và chuỗi chia cal/test). Backbone SD-STGCN.
- **Phần B (C3, mô phỏng lại):** gọi đúng `jk11.run` cho 18 thiết lập J-K12A (LFR 10k, μ 0,1/0,3, SI/IC/SIR, vùng nhiễm 25/100/300),
  si = 100 + i + 1000·s (mô phỏng mới, chia mới). |K̂| đo như J-K12A (`_kset`).
- Không đổi siêu tham số nào: α 0,10; α_k 0,02; α_s 0,08; pow 0,3.

## Tiêu chí
- A1: G (recall) phủ ở k xấu nhất < 0,85 ở ≥ 85/90 cặp (cấu hình, seed).
- A2: KSU* phủ ở k xấu nhất ≥ 0,88 ở ≥ 95% trong 270 bộ (cấu hình, hàm điểm, seed) VÀ không bộ nào < 0,86.
- B1: KSU* ≥ 0,88 ở ≥ 95% trong 180 bộ (thiết lập, seed) VÀ không bộ nào < 0,86; G < 0,85 ở ≥ 75% trong 180.
- B2 (C3): Spearman ρ(|K̂|, KSU*/WCP) tính riêng từng seed trên 18 thiết lập; trung vị ρ ≥ 0,7 VÀ p hoán vị một phía < 0,05 ở ≥ 8/10 seed.
- Kết luận: A1 ∧ A2 → "C1, C2 LẶP LẠI ĐƯỢC (dữ liệu tác giả)"; B1 → "C1, C2 LẶP LẠI ĐƯỢC (mô phỏng)"; B2 → "C3 LẶP LẠI ĐƯỢC". Trượt tiêu chí nào báo đúng như vậy.
- Kiểm tính đúng: seed 0 phải trùng J-K12 (phần A: kích thước, phủ; phần B: ρ = 0,89). Nếu không trùng → dừng, tìm lỗi trước khi đọc seed khác.

## Báo cáo
Trung bình ± độ lệch chuẩn qua 10 seed của: phủ k xấu nhất, kích thước (G, O, WCP, MDCP, KSU*); ρ từng seed.
