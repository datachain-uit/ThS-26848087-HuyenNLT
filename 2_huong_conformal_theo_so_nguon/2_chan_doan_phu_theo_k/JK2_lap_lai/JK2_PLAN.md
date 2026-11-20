# J-K2 — kiểm lặp lại: phương pháp conformal của Jian et al. (AAAI 2026) có phủ kém ở dịch ít nguồn không?

Viết 18/11/2026, **trước khi chạy**. Seed 20261118. Dùng lại đúng thiết lập của J-K (`../10_JK_dieu_kien_theo_k/JK_PLAN.md`): điểm `recall_score`, pow 0,3, α = 0,10, 50 lần lặp 5600/400, tập k với α_k = 0,05.

## Phát hiện cần kiểm (F1, từ J-K trên highSchool R0 1–15)
Hiệu chỉnh gốc (G) đạt độ phủ biên 0,898 nhưng chỉ 0,664 ở nhóm k 1–3 (phủ thừa 0,99 ở k ≥ 8).

## Dữ liệu
8 cấu hình mới của tác giả, đầu ra SD-STGCN đã tính sẵn: {highSchool, sfhh, bkFratB} × R0 {1–15, 11–25, 21–35}, trừ highSchool 1–15 (đã dùng ở J-K, chỉ báo cáo kèm). Mỗi cấu hình 8000 mẫu, k đều trên 1..15.

## Tiêu chí (khóa)
- Kiểm tra: độ phủ biên của G trong [0,87; 0,93] ở ≥ 6/8 cấu hình mới; nếu không → xem lại trước khi diễn giải.
- **F1 LẶP LẠI** nếu G phủ < 0,85 ở nhóm k 1–3 trong ≥ 6/8 cấu hình mới; **KHÔNG LẶP LẠI** nếu ≤ 2/8; còn lại **LẶP LẠI MỘT PHẦN**.
- Mô tả kèm: độ phủ G theo 4 nhóm k; O (biết k thật) và KS (theo tập k) — độ phủ, kích thước, độ phủ nhóm thấp nhất.

## Giới hạn
- Chỉ một hàm điểm (recall), một mức pow (0,3), một α; đầu ra GNN của tác giả, không huấn luyện lại.
- Mọi kết quả đều báo cáo, kể cả khi âm.
