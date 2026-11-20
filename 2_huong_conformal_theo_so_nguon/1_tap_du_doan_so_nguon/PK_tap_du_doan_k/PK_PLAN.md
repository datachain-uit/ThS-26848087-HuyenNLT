# P-K — pilot: tập dự đoán có bảo đảm độ phủ cho số nguồn k

Viết 18/11/2026, **trước khi chạy**. Người quyết định: học viên. Không cần mô phỏng mới: dùng lại cascade của E0x (`../6_E0x_so_cum_va_vung_dinh_danh/results/chunks`, chỉ phần `rand`, đủ 10 seed). Chưa ai xem kết quả conformal trên dữ liệu này.

## Căn cứ (kiểm tính mới 18/11, xem `kiem_tinh_moi_HuongB_va_k_18_11.md`)
- Conformal cho định vị đa nguồn (Jian et al., AAAI 2026) chỉ cho tập **nút nguồn** với bảo đảm recall; không ước lượng, không cho bất định về **số** nguồn; không đánh giá lệch mô hình.
- BP (Altarelli et al.) cho hậu nghiệm từng nút với prior xác suất làm nguồn đã biết; không suy luận số nguồn.
- Các bộ ước lượng k (NetSleuth, Jiang T(k), SLBNE, TP, TP-MDV, Luo–Tay–Leng) chỉ cho ước lượng điểm.
- E0a (8 seed, tạm): đặc trưng không cộng đồng có tín hiệu mạnh ở f nhỏ (skill 0,84–0,89 ở 2%) và mất dần khi f tăng → hình dạng phù hợp cho một bộ ước lượng dạng tập.

## Thiết lập
- Ô = (đồ thị, f): 4 × 6 = 24 ô. Nhãn k ∈ {1, 2, 3, 5, 8}.
- Chia theo seed (tránh rò rỉ): seed 0–3 huấn luyện, seed 4–6 hiệu chỉnh, seed 7–9 kiểm tra; train và test của E0x đều dùng.
- Bộ phân loại: RandomForestClassifier(300 cây, min_samples_leaf = 5, random_state = 0) trên đặc trưng họ U của E0x (N + Louvain + hình học).
- Tập dự đoán, α = 0,1:
  - `CP`: split conformal, điểm không phù hợp 1 − p̂(y).
  - `CP-M`: Mondrian (hiệu chỉnh riêng từng k), cho độ phủ theo từng k.
- Đối chứng: `pt` = {k̂} (k̂ = argmax p̂); `pm1` = các nhãn trong [k̂ − 1, k̂ + 1].

## Tiêu chí (khóa)
- **S (kiểm tra cài đặt):** độ phủ biên của `CP` trong [0,85; 0,95] ở ≥ 20/24 ô. Trượt → nghi lỗi cài đặt, dừng và kiểm code, không diễn giải.
- **U (hữu dụng):** kích thước tập trung bình của `CP` ≤ 2,0 ở ≥ 6/8 ô có f ≤ 5%.
- **A (thích nghi theo độ khó):** kích thước tập trung bình của `CP` ở f = 40% ≥ 1,5 × ở f = 2%, ở ≥ 3/4 đồ thị.
- **Kết luận:** S, U, A cùng đạt → GO (sang bước lệch mô hình và tái lập baseline). S đạt, U hoặc A trượt → NO-GO cho hướng tập dự đoán k.
- Mô tả kèm, không dùng kết luận: độ phủ theo từng k (đặc biệt k = 8) của `CP` và `CP-M`; độ phủ và kích thước của `pt`, `pm1`.

## Giới hạn
- Hiệu chỉnh và kiểm tra cùng đồ thị, cùng mô hình SI: độ phủ được bảo đảm theo lý thuyết; pilot chỉ kiểm tính hữu dụng và thích nghi. Lệch mô hình (hiệu chỉnh SI, kiểm IC/SIR) là bước sau, cần mô phỏng mới.
- Lưới k thưa (5 giá trị); kích thước tập đo trên lưới này.
- Mọi kết quả đều báo cáo, kể cả khi âm.
