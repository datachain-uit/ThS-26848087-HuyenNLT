# J-K8 — xếp hạng nút có điều kiện theo k (KC) — giao thức khóa trước

Khóa 18/11/2026 trước khi chạy. 9 cấu hình của Jian et al. (SIR), pow 0,3, α = 0,10, 50 lần lặp; chia mẫu như J-K5 (ktr 1400, kcal 600, cal 5600, test 400).

## Kiểm tính mới
- GNN định vị nguồn dùng k đã biết làm đầu vào đã có (GCNSI, Dong et al. 2019; xem tổng quan arXiv 2512.20657). Xếp hạng có điều kiện theo k **không mới**.
- Chưa thấy: dùng nhiều xếp hạng theo giả thuyết k và lấy hợp có bảo đảm conformal theo từng k khi k chưa biết. MDCP (Yang & Jin 2026) có học điểm theo nguồn nhưng cần mật độ trên không gian nhãn; ở đây thay bằng xếp hạng theo giả thuyết.
- J-K7: với một xếp hạng chung, hợp các tập theo k = tập lớn nhất (MDCP chứng minh gộp max-p tối ưu khi điểm cố định). Đòn bẩy còn lại là để xếp hạng phụ thuộc k.
- Ba hàm điểm của tác giả đều là biến đổi đơn điệu của thứ hạng xác suất GNN trong vùng nhiễm → mọi tập là "top-m nút". J-K8 làm việc trực tiếp trong không gian độ sâu m.

## Bộ xếp hạng lại (proxy rẻ, không huấn luyện lại GNN)
- Dòng = (mẫu, nút nhiễm v). Nhãn: v là nguồn. Huấn luyện **chỉ trên ktr** (độc lập với cal/test).
- Đặc trưng chung: logit xác suất GNN, thứ hạng và thứ hạng tương đối trong vùng nhiễm I, khoảng cách tới tâm Jordan của I, độ lệch tâm, bậc trong G và trong I, tỉ lệ hàng xóm nhiễm, |I|.
- KC thêm: c, c/|I|, khoảng cách tới c tâm k-center đầu tiên (thô và chuẩn hóa theo bán kính). Huấn luyện với c = k thật; dự đoán cho mọi c = 1..15.
- Bản đối chứng phẳng (F): chỉ đặc trưng chung, để tách hiệu ứng "xếp hạng lại" khỏi hiệu ứng "điều kiện theo k".
- Mô hình: HistGradientBoostingClassifier (max_iter 300, lr 0,05, random_state 0).

## Phương pháp (không gian độ sâu; phủ = recall ≥ pow)
- Độ sâu của một mẫu dưới xếp hạng π: m nhỏ nhất để top-m chứa q nguồn (q nhỏ nhất với q/k ≥ pow). Nguồn ngoài I → m = n (cả đồ thị).
- Dg-O, KC-O: biết k thật (oracle), ngưỡng độ sâu theo k ở α = 0,10, xếp hạng GNN / xếp hạng theo k.
- Dg-KSU, Df-KSU: khung KSU* (K̂ α_k 0,02 hiệu chỉnh trên kcal ∪ cal, ngưỡng theo k α_s 0,08), xếp hạng chung GNN / phẳng → top-(max_{c∈K̂} m_c).
- **KC (chính):** khung KSU*, tập = ∪_{c∈K̂(x)} top-m_c theo π_c(x); m_c hiệu chỉnh trên độ sâu của mẫu cal lớp c dưới π_c. Bảo đảm P(phủ | k) ≥ 1 − 0,02 − 0,08.
- KC-MD: K̂ = cả 15, m_c ở α = 0,10 (MDCP, bảo đảm chính xác).
- Tham chiếu điểm tác giả, cùng phép chia: WCP-a và KSU*-a cho 3 hàm điểm; "tốt nhất" = kích thước nhỏ nhất trong 3.

## Kiểm tra cài đặt (smoke, không in số liệu)
Trên 300 mẫu: top-độ sâu chứa ≥ q nguồn và top-(độ sâu − 1) chứa < q nguồn (khi độ sâu ≤ |I|). Sai thì dừng.

## Tiêu chí (9 cấu hình)
- V: KC phủ theo k thấp nhất (gộp) ≥ 0,88 ở ≥ 8/9.
- K1 (điều kiện theo k có tác dụng): cỡ KC ≤ 0,85 × Df-KSU ở ≥ 7/9.
- K2 (hơn phương pháp có bảo đảm trước): cỡ KC ≤ 0,85 × KSU*-a tốt nhất ở ≥ 7/9.
- K3 (chạm WCP): trung bình cỡ KC / WCP-a tốt nhất ≤ 1,10.

## Kết luận định trước
- V ∧ K1 ∧ K2 ∧ K3 → GO (phương pháp mới: có bảo đảm theo k, kích thước ngang WCP).
- V ∧ K1 ∧ K2 → MỘT PHẦN (hơn mọi phương pháp có bảo đảm, chưa tới WCP).
- V ∧ K1 → "ĐIỀU KIỆN THEO k CÓ TÁC DỤNG, CHƯA ĐỦ".
- Còn lại → NO-GO.
Không đổi tiêu chí sau khi xem kết quả.
