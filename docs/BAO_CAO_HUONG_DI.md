# Báo cáo hướng đi: conformal prediction theo số nguồn cho định vị đa nguồn lan truyền

*Lập ngày 20/11/2026. Mã thí nghiệm (J-K…) tra trong `docs/MUC_LUC_THI_NGHIEM.md` của repo luận văn.*

## 0. Kết quả hướng cũ và lý do đổi hướng

| Cổng / thí nghiệm | Kết quả | Hệ quả |
| --- | --- | --- |
| H0, H0c, H0p (P6) | NO-GO: phân hoạch cộng đồng không giải thích sai số định vị | — |
| Hiệu chỉnh P6-F | Dư địa cho phương pháp cộng đồng ở cascade chồng lấn chỉ 0,2–1,0 hop | P6-F chính thức chưa chạy (giao thức chưa khóa) |
| E0 (cổng G-E0 của D1) | Không khả quan | Theo kế hoạch cũ: dừng D1 |
| E0x | Số cụm vùng nhiễm tăng theo k (24/24 ô) nhưng không có vùng ước lượng điểm k đáng tin (0/12 ô) | Cấu trúc mang tín hiệu về k nhưng không đủ để đoán k |
| PK | Tập dự đoán conformal cho k: GO | Mở hướng lượng hóa bất định thay cho ước lượng điểm |

Kế hoạch cũ quy định: G-E0 không đạt thì quay về Hướng B. Em đề xuất chuyển sang hướng mới vì E0x và PK cho tín hiệu dương ở một bài toán khác (bất định của k), có tài liệu nền (Jian et al., AAAI 2026) và đã có kết quả sơ khởi đạt tiêu chí khóa trước. Hướng B vẫn giữ làm phương án dự phòng.

## 1. Bài toán

Cho đồ thị G = (V, E) và một snapshot tập nút nhiễm x sinh từ tập nguồn S chưa biết, với |S| = k chưa biết. Trả về tập nút C(x) ⊂ V sao cho C chứa ít nhất tỉ lệ pow của S với xác suất ≥ 1 − α. Bảo đảm cần đúng cho từng k (và cho từng cơ chế lan truyền), không chỉ trung bình trên mọi k.

## 2. Từ vấn đề tồn đọng đến câu hỏi nghiên cứu

| Vấn đề tồn đọng ở các bài đã khảo sát | Khoảng trống | Câu hỏi |
| --- | --- | --- |
| Jian et al. (AAAI 2026) chỉ bảo đảm biên theo k; bảng theo số nguồn của họ dùng k cố định (tức là biết k) | Chưa ai đo độ phủ có điều kiện theo k khi k ẩn | RQ1 |
| Conformal theo nhóm (Mondrian; Gibbs et al. 2025) cần nhóm quan sát được; WCP (ICLR 2026) chỉ bảo đảm biên; MDCP (2026) không dùng x để thu hẹp tập | Chưa có thủ tục hữu hạn mẫu theo nhóm ẩn cho định vị đa nguồn | RQ2 |
| Chưa ai định lượng giá của bảo đảm theo nhóm ẩn | Giá phụ thuộc vào đâu | RQ3 |
| Review GNN định vị nguồn (Sterchi et al.) và Jian et al. nêu độ bền với lệch mô hình lan truyền là vấn đề mở | Chưa đánh giá có hệ thống | RQ4 |
| Không phương pháp nào bảo đảm khi chưa biết cơ chế lan truyền | — | RQ5 |

## 3. Câu hỏi nghiên cứu

| RQ | Câu hỏi | Giả thuyết | Bị bác khi | Thành phần | Thí nghiệm | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| RQ1 | Bảo đảm biên của Jian et al. có đúng cho từng k không? | Không: phủ ở k xấu nhất < 0,85 | Phủ k xấu nhất ≥ 0,85 trên đa số thiết lập | Chẩn đoán (tiền đề) | Tái lập; J-K1–J-K3; J-K10–J-K12; J-K15; J-K16 | Xác nhận |
| RQ2 | Có thủ tục bảo đảm P(phủ ∣ k) ≥ 1 − α cho mọi k khi k ẩn không? | KSU* hợp lệ, tập nhỏ hơn MDCP | KSU* < 0,88 ở > 5% bộ, hoặc không nhỏ hơn MDCP | C1: KSU* | J-K4–J-K6; J-K12; J-K15; J-K16 | Đạt |
| RQ3 | Giá của bảo đảm theo k là bao nhiêu và phụ thuộc vào đâu? | Tăng theo độ mơ hồ của k | Spearman ρ không có ý nghĩa | Phân tích | J-K7; J-K8; J-K12–J-K14; J-K16 | Xác nhận |
| RQ4 | Bảo đảm còn đúng khi mô hình lan truyền hoặc quan sát bị lệch? | Chịu được lệch tham số, không chịu lệch loại mô hình | KSU* không hơn G ở đa số thiết lập lệch (phần còn lại là đánh giá mô tả) | Đánh giá độ bền | J-K17; J-K18 | Đã chạy |
| RQ5 | Lấy lại bảo đảm theo (cơ chế, k) khi chưa biết cơ chế? | KSU*-mk hợp lệ, nhỏ hơn MDCP trên nhóm | KSU*-mk < 0,88 hoặc không nhỏ hơn MD-mk | C2: KSU*-mk | J-K19; J-K19b | Đạt (sau chẩn đoán) |

**Quan hệ giữa các câu hỏi:** RQ1 âm tính thì cả hướng mất nghĩa; RQ1 đã được xác nhận. Guidance yêu cầu phương pháp đề xuất có ít nhất 2 đóng góp: C1 (KSU*) và C2 (KSU*-mk). Mức mới về kỹ thuật của cả hai ở mức thấp–vừa (ghép Mondrian CP và union bound), nên bài dựa thêm vào RQ1, RQ3, RQ4.

**Phân giai đoạn công bố:** RQ1–RQ3 (chẩn đoán, C1, phân tích giá) cho bài hội nghị; RQ4–RQ5 (độ bền, C2) bổ sung cho bài tạp chí.

**Phạm vi không làm:** quan sát kiểu monitor hoặc nhiều snapshot; mạng động; huấn luyện lại GNN dò nguồn (dùng đầu ra có sẵn của tác giả và một backbone GCN thứ hai).

## 4. Kết quả sơ khởi (10 seed, tiêu chí khóa trước)

| Thành phần | Kết quả chính | Thí nghiệm |
| --- | --- | --- |
| Tái lập Jian et al. | Khớp đến 3 chữ số (phủ 0,898; kích thước 6,570) | Tái lập |
| RQ1 | Phủ biên 0,90 nhưng ở k xấu nhất (thường k = 1) chỉ 0,19–0,44; lặp lại với backbone GCN (0,24–0,48) và ở 45/49 thiết lập mô phỏng | J-K12B, J-K15, J-K16 |
| RQ2 – C1 | KSU* hợp lệ 270/270 bộ (dữ liệu tác giả), 179/180 bộ (mô phỏng); nhỏ hơn MDCP trên dữ liệu tác giả và đồ thị thật | J-K15B, J-K16 |
| RQ3 | Giá ×1,07–1,98 so với WCP; ρ = 0,89–0,95, p < 0,05 ở 10/10 seed. Bỏ union bound hay dùng điểm theo k không giảm được giá | J-K7, J-K8, J-K12, J-K14, J-K16 |
| RQ4 | Lệch tham số: chịu được (0,91–0,98). Lệch loại mô hình: mọi phương pháp mất bảo đảm, kể cả oracle (ví dụ SI → IC: 0,23). Ảnh chụp thiếu nút chỉ ở lúc triển khai: mất bảo đảm | J-K17, J-K18 |
| RQ5 – C2 | J-K19 trượt sát ngưỡng (0,855; oracle cũng chỉ 0,831 ở cùng ô). J-K19b (chẩn đoán, khóa trước): hợp lệ 36/36 bộ, thấp nhất 0,893; nhỏ hơn MD-mk ×1,8–3,3 | J-K19, J-K19b |
| Kiểm tra độc lập | Các số chính được tính lại bằng code độc lập: khớp | Kiểm tra |

**Hạn chế hiện tại:**
- Mới có 10 seed, chưa đạt quy ước của nhóm (≥ 30 seed mỗi ô, kèm Wilcoxon–Holm, bootstrap CI và effect size).
- Chỉ dùng dữ liệu mô phỏng; ảnh chụp thiếu nút lúc triển khai chưa được xử lý.
- KSU* phủ dư (khoảng 0,92) do dùng union bound.
- Baseline MDCP mới là preprint.

## 5. Kế hoạch 2 tuần tới (24/11–07/12)

| Việc | Mục tiêu | Đầu ra | Task (Quy trình NC) |
| --- | --- | --- | --- |
| Mở rộng KSU*-mk cho thiếu quan sát | Đưa tỉ lệ che nút vào họ hiệu chỉnh, để lấy lại bảo đảm khi ảnh chụp triển khai thiếu nút | Phương pháp và kết quả thí nghiệm | 7, 6 |
| Giảm phủ dư của KSU* | Phân bổ α thích nghi theo độ mơ hồ của k, thay cho chia cố định, để thu nhỏ tập mà vẫn giữ bảo đảm | Kết quả so sánh với KSU* | 7, 6 |
| Dữ liệu bán thật | Thử trên cascade tin đồn có gốc đã biết (Twitter15/16, PHEME) | Kịch bản và kết quả bước đầu | 5, 6 |
| Tăng độ tin cậy thống kê | Chạy các thí nghiệm chính với ≥ 30 seed, kèm Wilcoxon–Holm, bootstrap CI và effect size | Bảng kết quả 30 seed | 6 |

Em sẽ báo cáo cô kết quả vào ngày 07/12/2026.

*[Tên học viên]*
