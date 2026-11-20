# J-K14 — LD-CP bản sửa duy nhất (LD2), dữ liệu đánh giá mới — giao thức khóa trước

Khóa 18/11/2026 ~21:15, trước khi chạy. Đây là lần sửa DUY NHẤT sau J-K13 (NO-GO). Nếu trượt thì dừng hướng LD-CP.

## Thay đổi so với J-K13 (cố định, không tinh chỉnh thêm)
1. **Cross-fitting:** hai bộ xếp hạng lại trên A1 và A2. Độ sâu của A1 lấy từ bộ học trên A2 và ngược lại. Mô hình độ sâu học trên cả 1400 mẫu ktr (gấp đôi J-K13). Cal/test dùng bộ xếp hạng học trên A1, như J-K13.
2. **Mô hình độ sâu = hồi quy phân vị** cho log(độ sâu): HistGradientBoostingRegressor(loss="quantile") ở 14 mức (0,02 … 0,99). CDF tại mép m = nội suy tuyến tính theo log m giữa các phân vị đã sắp; dưới phân vị thấp nhất = 0, trên cao nhất = 1.
3. **Làm trơn:** F̃ = 0,8·F̂ + 0,1·F_emp,c + 0,1·G, với F_emp,c là CDF thực nghiệm độ sâu lớp c trên ktr và G(m) = log(1+m)/log(1+n). Bảo đảm h < 1 với mọi m < n (tránh suy biến).
4. **λ = 1** (J-K13: tìm λ không có tác dụng). Trọng số w_c ∝ p̂(c|x) (RF trên ktr).
- Phần còn lại giữ như J-K13: r = h(x, D − 1); τ* = max_c phân vị conformal mức 0,10 theo lớp; m(x) = mép nhỏ nhất có h > τ*.
- Bảo đảm theo từng k chính xác (gộp max-p).

## Dữ liệu đánh giá (chưa dùng ở bất kỳ thí nghiệm nào)
- 18 thiết lập: lfr10k_mu0.1_2, lfr10k_mu0.3_2 × SI/IC/SIR × vùng nhiễm 25/100/300; seed = 20261118 + 200 + chỉ số. Xếp hạng chỉ cấu trúc.
- 9 cấu hình tác giả với phép chia mẫu mới (seed 20261119), xếp hạng GNN + cấu trúc.
- 50 lần lặp, cal 5600 / test 400.

## Phương pháp so sánh
G, O, WCP, MDCP, KSU* (như J-K13); LD13 (bản J-K13 với λ = 1, để đo tác dụng của bản sửa); **LD2 (chính)**.

## Tiêu chí (27 tập)
- V: LD2 phủ theo k thấp nhất ≥ 0,88 ở ≥ 25/27; lệch prior ≥ 0,88 ở ≥ 103/108.
- E1: trung bình LD2/KSU* ≤ 0,85 và LD2 < KSU* ở ≥ 20/27.
- E2: trung bình LD2/WCP ≤ 1,10.
- S (không suy biến): LD2 ≤ 2 × KSU* ở 27/27.

## Kết luận định trước
- V ∧ E1 ∧ E2 ∧ S → GO (phương pháp mới).
- V ∧ E1 ∧ S → MỘT PHẦN.
- Còn lại → NO-GO, dừng LD-CP.
Không đổi tiêu chí sau khi xem kết quả. Smoke: 1 thiết lập nhỏ + 1 cấu hình tác giả, 2 lần lặp, seed 900. Kiểm tra: h không giảm; h < 1 trước n; phủ ⇔ r ≤ τ; chỉ in "smoke ok".
