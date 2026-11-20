# J-K12 — kiểm định khóa trước: giá của bảo đảm theo k tăng theo độ mơ hồ của k; bảng chính kèm khoảng tin cậy

Khóa 18/11/2026 ~16:45, trước khi chạy.

## Phần A — xác nhận quan hệ giá ~ |K̂| (quan sát hậu kiểm ở J-K11)
- Thiết lập **mới** (chưa dùng ở J-K10/J-K11):
  - đồ thị lfr10k_mu0.1_1 và lfr10k_mu0.3_1 (bản thể khác);
  - vùng nhiễm 25, 100, 300 nút;
  - SI/IC/SIR → 18 thiết lập.
- Seed = 20261118 + 100 + chỉ số thiết lập.
- Code: hàm `run` của J-K11, không đổi (HGB cấu trúc, RF cho k, G/O/WCP/MDCP/KSU*, 50 lần lặp).
- Biến: x = |K̂| trung bình (tập k của KSU*); y = kích thước KSU* / kích thước WCP.
- **H1:** Spearman ρ(x, y) ≥ 0,6 và p một phía < 0,05 (hoán vị 10 000 lần, seed 7).
- **H2:** KSU* phủ theo k thấp nhất ≥ 0,88 ở ≥ 17/18.
- Kết luận: H1 ∧ H2 → "XÁC NHẬN: giá tăng theo |K̂|"; H2 mà không H1 → "KHÔNG XÁC NHẬN"; trượt H2 → xem lại.
- Mô tả kèm: ρ(|K̂|, KSU*/O).

## Phần B — bảng chính trên dữ liệu tác giả kèm khoảng tin cậy (mô tả, không tiêu chí mới)
- 9 cấu hình × 3 hàm điểm của tác giả, pow 0,3, α 0,10, 50 lần lặp, chia mẫu như J-K5 (seed 20261118).
- Phương pháp G, O, WCP, MDCP, KSU*.
- Báo phủ biên, phủ theo k thấp nhất kèm cận dưới Wilson 95% và k xấu nhất, kích thước ± nửa khoảng 95%.

Không đổi tiêu chí sau khi xem kết quả. Smoke: A — 1 thiết lập nhỏ (hàm run của J-K11 ở chế độ smoke); B — 1 cấu hình, 2 lần lặp; chỉ in "smoke ok".
