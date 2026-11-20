# J-K — pilot: hiệu chỉnh tập nguồn conformal (Jian et al., AAAI 2026) có điều kiện theo tập dự đoán số nguồn

Viết 18/11/2026, **trước khi chạy**. Người quyết định: học viên. Seed 20261118.

## Căn cứ
- Jian et al. (AAAI 2026) ghi hướng tương lai: ảnh hưởng của lệch mô hình SIR với số nguồn khác nhau. Log trong repo của họ (thí nghiệm `main_mismatch.py`, không có trong bài): hiệu chỉnh trên 10–15 nguồn, kiểm 5–10 nguồn → độ phủ set_recall 0,837 ở α = 0,10; hiệu chỉnh trên 1–5 nguồn → tập phình tới 774 nút ở α = 0,05.
- Tái lập phần conformal của họ khớp hoàn toàn (18/11).
- P-K2: tập dự đoán k hẹp ở vùng nhiễm ≈ 2% (1,8–2,1 giá trị trên LFR); dữ liệu của Jian có vùng nhiễm trung bình 20,7 nút / 774 (≈ 2,7%).
- Kỹ thuật gần nhất: conformal thích nghi với dịch chuyển nhóm con chưa biết (arXiv 2506.05583, 2025) — đánh trọng số dữ liệu hiệu chỉnh theo xác suất nhóm dự đoán. Ở đây nhóm = số nguồn k.

## Dữ liệu
`8_tai_lap_paper/cnsd/SD-STGCN/output/test_res/highSchool/SIR_nsrc1-15_Rzero1-15_gamma0.1-0.4_ls8000_nf16/res.pickle`: 8000 mẫu, k đều trên 1..15, đầu ra SD-STGCN của tác giả (xác suất là nguồn cho từng nút), snapshot trạng thái S/I/R, nguồn thật.

## Thiết lập
- Đặc trưng cho k: 19 đặc trưng của P-K2 (comp, k-center ρ1..6, 12 hình học) trên đồ thị con từng nhiễm của highSchool.
- Chia cố định: 2000 mẫu cho mô hình k (1400 huấn luyện RF, 600 hiệu chỉnh tập k với α_k = 0,05); 6000 mẫu còn lại cho conformal tập nguồn, lặp 50 lần chia ngẫu nhiên 5600 hiệu chỉnh / 400 kiểm tra (như bài gốc).
- Điểm conformal: `recall_score` của tác giả, pow_expected = 0,3, mô hình SIR, α = 0,10. "Phủ" = tỉ lệ nguồn thật nằm trong tập ≥ 0,3 (định nghĩa của tác giả).
- Phương pháp (ngưỡng = phân vị (1 − α)(1 + 1/n) của điểm trên tập hiệu chỉnh con):
  - `G`: toàn bộ tập hiệu chỉnh (phương pháp gốc).
  - `O`: chỉ mẫu hiệu chỉnh có cùng k thật (cận trên, không dùng được thực tế).
  - `KS`: mẫu hiệu chỉnh có k thuộc tập dự đoán k của mẫu kiểm tra (đề xuất). Tập con rỗng → dùng `G`.
  - `KP`: mẫu hiệu chỉnh có k = k̂ (ước lượng điểm).
- Nhóm k để đo độ phủ có điều kiện: {1–3, 4–7, 8–11, 12–15}.
- Kịch bản mô tả (lặp lại log lệch của tác giả bằng một mô hình duy nhất): `G` với hiệu chỉnh chỉ từ k ∈ 10–15 hoặc 1–5, kiểm trên k ∈ 5–10; so với `G` và `KS` dùng hiệu chỉnh đủ 1–15.

## Tiêu chí (khóa)
- **S (kiểm tra):** độ phủ biên của `G` trong [0,87; 0,93] (tác giả: 0,898).
- **M2 (vấn đề có thật):** độ phủ thấp nhất theo nhóm k của `G` < 0,85.
- **M1 (đề xuất sửa được):** độ phủ thấp nhất theo nhóm k của `KS` ≥ 0,85.
- **M3 (không trả giá quá đắt):** kích thước tập trung bình của `KS` ≤ 1,2 × của `G`.
- **Kết luận:** S, M1, M2, M3 cùng đạt → GO. M2 trượt → NO-GO ("hiệu chỉnh có điều kiện là không cần thiết với dữ liệu này"). M1 hoặc M3 trượt → NO-GO.

## Giới hạn
- Một đồ thị (highSchool), một cấu hình SIR, một mô hình GNN của tác giả.
- Chọn tập hiệu chỉnh con theo tập k của mẫu kiểm tra làm yếu giả định trao đổi được; bảo đảm lý thuyết chưa chứng minh — pilot chỉ đo thực nghiệm.
- Mọi kết quả đều báo cáo, kể cả khi âm.

## Ghi chú minh bạch (18/11, trước lần chạy chính)
- Lần chạy thử trên máy ảo (seed 999, 2 lần lặp, để sửa lỗi import) in ra dòng kết luận "NO-GO (M1 hoặc M3 trượt)"; người chạy đã thấy dòng đó nhưng không mở bảng. Tiêu chí ở trên viết trước lần chạy thử và không sửa. Lần chạy chính dùng seed 20261118, 50 lần lặp.
