# H0' (H0p) — Thí nghiệm tiền đề H0, sửa hai lỗi đo

Viết và khóa (SHA-256 ghi trong `logs/h0p.log` và `H0p_lock.json` lúc bắt đầu chạy) **trước khi** có bất kỳ kết quả nào. Seed cascade mới: 5050.

## 1. Vì sao có H0'

H0 (03/11, seed 2026) chạy đúng thiết kế Review 30/10 Mục 7.3 nhưng không đọc được, vì hai lỗi đo (không phải lỗi code):

1. **IC chạy đến hết làm mất thông tin về nguồn.** Kiểm tra cây trượt (Jordan center ED 6,82 hop; tiêu chí ≤ 1).
2. **ED ghép min(|Ŝ|, |S|) cặp + ρ chọn theo ED thưởng cho đoán thừa.** ρ = 1 ở 48/48 cấu hình; CommJordan đoán trung bình 68 nguồn khi thật có 1–5; Spearman(ED, k̂) qua các phân hoạch có trung vị −0,80. Phân hoạch ngẫu nhiên vì thế "tốt hơn" Louvain.

H0' giữ nguyên mọi thứ khác của H0 và chỉ sửa đúng hai điểm này.

## 2. Giữ nguyên từ H0

| Thành phần | Giá trị |
|---|---|
| Đồ thị | **Đúng 16 đồ thị của H0** (15 LFR n = 1.000, μ ∈ {0,1; 0,3; 0,5}, 5/μ; email-Eu-core), tệp `data/` chép từ `H0/data/` |
| Phân hoạch | **Đúng 55 phân hoạch của H0**: Louvain 10 γ × 5 seed (mặc định γ = 1, seed 0) + 5 ngẫu nhiên giữ phân bố kích thước |
| Số nguồn | k ∈ {1, 3, 5}, nguồn chọn ngẫu nhiên đều |
| Tỉ lệ nhiễm | 10–20% số node (lấy mẫu loại bỏ) |
| Số cascade | 200 test mỗi (đồ thị, mô hình quan sát, k) |
| Metric | ED (Hungarian), F1@h, h ∈ {0, 1, 2} |
| Ngưỡng H-a, H-b | Như Review 30/10 Mục 7.2 (Mục 6 dưới) |

## 3. Sửa lỗi 1 — mô hình quan sát định danh được

Hai mô hình, cả hai đã qua kiểm tra cây ở H0b (cây tam phân sâu 7, nguồn ở gốc, tập nhiễm 100–200 node):

- `ic_T`: IC dừng sau T = 4 bước; p hiệu chỉnh theo từng (đồ thị, k) để tối đa hóa tỉ lệ cascade rơi vào 10–20%.
- `si_t`: SI rời rạc β = 0,3; chụp snapshot ngay khi số node nhiễm đạt mục tiêu ~ U(10%, 20%) · n.

## 4. Sửa lỗi 2 — số nguồn

**Phân tích chính: biết trước k.** Tách câu hỏi "phân hoạch có giúp định vị không" khỏi câu hỏi "ước lượng số nguồn" (câu hỏi của D1). Đây là thiết lập "top-k với k thật" mà Review 30/10 Mục 7.4 yêu cầu báo cáo.

Bộ định vị CommJordan (B2, Mục 7.1) khi biết k:
1. Với phân hoạch P, đếm số node nhiễm trong từng cộng đồng.
2. Phân bổ k tâm cho các cộng đồng theo D'Hondt trên số node nhiễm (không vượt số node nhiễm của cộng đồng).
3. Cộng đồng nhận m_c tâm: chạy greedy k-center (Gonzalez) m_c tâm trên đồ thị con nhiễm của cộng đồng, tâm đầu là Jordan center. Đồ thị con đứt mảnh được xử lý theo bản sửa ngày 07/11 (`H0c_fix/BUGFIX.md`): tâm đầu là Jordan center của mảnh lớn nhất, mảnh chưa có tâm nhận Jordan center của nó trước.

Đối chứng không dùng phân hoạch: Jordan (greedy k-center k tâm trên toàn tập nhiễm, cùng hàm đã sửa); LPSI (α = 0,5, top-k điểm). Tham chiếu: phân hoạch cộng đồng thật (không tính vào H-a).

ED với |Ŝ| = |S| = k nên không còn thưởng đoán thừa.

## 5. Kiểm tra hợp lệ (định trước, xét riêng từng mô hình quan sát)

- **V1 (cây):** cây tam phân cân bằng sâu 7, một nguồn ở gốc, tập nhiễm 100–200 node, 100 cascade: Jordan center có ED trung bình ≤ 1 hop.
- **V2 (sàn):** trên toàn bộ 16 đồ thị và mọi k, ED trung bình của 5 phân hoạch ngẫu nhiên **lớn hơn** ED trung bình của phân hoạch mặc định.

Mô hình quan sát nào trượt V1 hoặc V2 thì kết quả H-a, H-b của mô hình đó **không đọc được** và không dùng để kết luận.

## 6. Giả thuyết và quy tắc quyết định (Review 30/10 Mục 7.2)

**H-a**, xét cho từng (đồ thị, k) trên ma trận ED 50 phân hoạch Louvain × 200 cascade:
- η² = SS_phân hoạch / SS_tổng (phân rã hai nhân tố phân hoạch × cascade) ≥ 0,20, **và**
- Δ_cf ≥ 0,3 hop **hoặc** Δ_cf ≥ 10% ED mặc định (đọc đúng chữ "hoặc" của cô, tức ngưỡng = min(0,3; 10% ED mặc định)).
- Δ_cf (cross-fit): chọn phân hoạch có ED trung bình nhỏ nhất trên cascade chẵn, đo ED_mặc định − ED_chọn trên cascade lẻ; đổi vai; lấy trung bình. Tránh thổi phồng do lấy min trên 50 phân hoạch.
- Một đồ thị đạt khi ≥ 2/3 giá trị k đạt. H-a đạt khi ≥ 11/16 đồ thị đạt.
- Báo cáo phụ (không dùng kết luận): ngưỡng chặt max(0,3; 10%); Δ đơn giản (không cross-fit).

**H-b**, từng đồ thị: Spearman ρ giữa NMI(phân hoạch, cộng đồng thật) và ED trung bình của phân hoạch (gộp mọi k và cascade), trên 50 phân hoạch Louvain. Đạt khi |ρ| < 0,5 trên đa số (≥ 9/16) đồ thị.

**Kết luận cho P6:**
- Cả hai mô hình quan sát hợp lệ và H-a đạt ở cả hai → **GO**.
- Cả hai hợp lệ và H-a không đạt ở cả hai → **NO-GO**.
- Còn lại (một mô hình đạt, hoặc chỉ một mô hình hợp lệ) → **chưa kết luận, trình GVHD**.

Không đổi ngưỡng, tiêu chí hay quy tắc sau khi xem kết quả. Mọi kết quả đều được báo cáo.

## 7. Báo cáo kèm (mô tả, không dùng kết luận)

ED và F1@1 của: phân hoạch mặc định, Jordan, LPSI, phân hoạch thật, phân hoạch ngẫu nhiên; ED "oracle" (phân hoạch tốt nhất cho từng cascade, có độ chệch chọn lọc, chỉ để tham khảo); ED trung bình theo γ.

## 8. Giới hạn đã biết

- Biết trước k không phản ánh thực tế; trả lời "phân hoạch có giúp khi số nguồn đã biết". Nếu không giúp trong điều kiện thuận lợi này, P6 khó giúp khi phải ước lượng k.
- Chỉ Louvain (không Leiden, Infomap, DGC) và chỉ một họ bộ định vị (CommJordan). CommLPSI đã thử ở H0c.
- Lan truyền mô phỏng; nguồn chọn ngẫu nhiên đều.
