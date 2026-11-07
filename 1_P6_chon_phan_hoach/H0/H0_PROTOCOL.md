# H0 — Giao thức và kế hoạch thực hiện (BẢN NHÁP, chờ chốt)

| Mục | Nội dung |
|---|---|
| Đề tài | P6 — Chọn và gộp phân hoạch cộng đồng không dùng nhãn cho bài toán định vị nguồn lan truyền |
| Thí nghiệm | H0 — thí nghiệm tiền đề, kiểm tra giả thuyết H-a (và H-b sơ bộ) |
| Căn cứ | Review 30/10: Mục 7.1 (B2), 7.2 (H-a, H-b), 7.3 (thiết lập H0); QĐ11 (hạn 20/11), QĐ12 (mọi số liệu có tệp gốc), R4 (không nới ngưỡng) |
| Trạng thái | **NHÁP.** Các mục ghi **[CHỜ CHỐT]** cần học viên xác nhận. Sau khi chốt, file được khóa bằng SHA-256 **trước** khi sinh dữ liệu |
| Nơi chạy | Máy của học viên, VS Code, terminal Python, thư mục `C:\Users\ad\Documents\H0\` |

Quy ước: **[Cô]** = lấy nguyên từ review; **[Đề xuất]** = lựa chọn của Claude khi review không nêu; **[CHỜ CHỐT]** = cần học viên quyết định.

---

## 1. Câu hỏi và quy tắc quyết định

**Câu hỏi.** Thay đổi phân hoạch cộng đồng có làm sai số định vị nguồn (ED) của bộ định vị dựa trên cộng đồng thay đổi đáng kể, so với dao động do cascade ngẫu nhiên, hay không?

**H-a [Cô].** Chênh ED giữa phân hoạch tốt nhất và mặc định (Louvain γ = 1) ≥ 0,3 hop (hoặc ≥ 10% ED mặc định) **và** phần phương sai ED do phân hoạch ≥ 20% (phân rã hai nhân tố phân hoạch × cascade), trên ≥ 2/3 đồ thị pilot.

**Cách đọc chính dùng để kết luận [CHỜ CHỐT — đề xuất]:**

| Thành phần | Cách đọc chính | Báo cáo phụ (không dùng kết luận) |
|---|---|---|
| Vế 1 | Δ ≥ 0,3 hop **hoặc** Δ ≥ 0,10 × ED_mặc định (đúng câu chữ 30/10) | Chỉ "≥ 0,3 hop"; "và" thay cho "hoặc" |
| Δ | **Cross-fit**: chọn phân hoạch tốt nhất trên một nửa cascade, đo Δ trên nửa còn lại, lấy trung bình hai chiều (tránh thiên lệch chọn người thắng) | Δ đơn giản (chọn và đo trên cùng cascade) |
| Vế 2 | η²_phân hoạch = SS_phân hoạch / SS_tổng ≥ 0,20 (đúng câu chữ 30/10) | SS_phân hoạch / SS_cascade ≥ 0,20 (cách viết ở 04/10) |
| Đơn vị "đồ thị" | Một đồ thị **đạt** khi đạt ở ≥ 2/3 giá trị k ∈ {1, 3, 5} | Kết quả từng cặp (đồ thị, k) |
| Kết luận chung | **GO** nếu ≥ 2/3 số đồ thị đạt (≥ 11/16) | Theo từng μ |

**H-b [Cô], kiểm sơ bộ.** Spearman |ρ|(NMI, ED) < 0,5 trong từng đồ thị, trên đa số đồ thị có cộng đồng thật. [Đề xuất] ED dùng để tính ρ là ED trung bình của mỗi phân hoạch, gộp qua 3 giá trị k; báo cáo kèm khoảng NMI của 50 phân hoạch (cảnh báo thu hẹp khoảng biến thiên).

Quy tắc khóa: sau khi hash file này, **không đổi ngưỡng, cách đọc chính, tham số hay tập dữ liệu**. Mọi sai lệch bắt buộc (ví dụ LFR không hội tụ) ghi vào `DEVIATIONS.md` kèm lý do.

---

## 2. Môi trường

- Windows, VS Code, Python ≥ 3.10, môi trường ảo `.venv` trong thư mục `H0`.
- Thư viện: `networkx`, `numpy`, `scipy`, `pandas`, `matplotlib`. Sau khi cài, xuất `pip freeze > requirements.lock.txt` để pin phiên bản (yêu cầu 04/10).
- Seed gốc: **2026**. Mọi seed con suy ra từ seed gốc theo (đồ thị, k, cascade) để chạy lại cho kết quả giống hệt.
- Chạy song song theo số nhân CPU của máy; có `if __name__ == "__main__"` cho Windows.

## 3. Cấu trúc thư mục

```
H0/
├─ H0_PROTOCOL.md          # file này
├─ H0_PROTOCOL.sha256      # hash, tạo sau khi chốt
├─ DEVIATIONS.md           # sai lệch so với giao thức (nếu có)
├─ requirements.txt / requirements.lock.txt
├─ config.py               # toàn bộ tham số, khớp Mục 4–8
├─ h0lib.py                # đồ thị, phân hoạch, IC, CommJordan (B2), Jordan, LPSI, chấm điểm
├─ lock_protocol.py        # tạo H0_PROTOCOL.sha256
├─ run_h0.py               # chạy toàn bộ, có --smoke, chạy tiếp được khi bị ngắt
├─ analyze_h0.py           # phân rã phương sai, H-a, H-b, bảng và hình
├─ sanity_checks.py        # kiểm tra hợp lý
├─ data/                   # đồ thị, phân hoạch (kèm hash)
├─ results/raw/            # CSV thô theo từng đồ thị
├─ results/summary/        # bảng tổng hợp, hình
├─ logs/h0.log             # tiến độ
└─ BAO_CAO_H0.md           # báo cáo 2 trang, đề xuất go/no-go
```

## 4. Đồ thị

| Đồ thị | Thiết lập |
|---|---|
| LFR [Cô] | n = 1.000; μ ∈ {0,1; 0,3; 0,5}; 5 đồ thị mỗi μ → 15 đồ thị |
| LFR, tham số còn lại [Đề xuất] | τ₁ = 3, τ₂ = 1,5, bậc trung bình 10, bậc tối đa 50, kích thước cộng đồng 20–100. Không hội tụ → thử seed kế tiếp, ghi vào log |
| email-Eu-core [Cô] | SNAP `email-Eu-core.txt.gz` + `email-Eu-core-department-labels.txt.gz`; bỏ hướng, bỏ self-loop, lấy thành phần liên thông lớn nhất; phòng ban = cộng đồng thật. Không tải được → học viên tải thủ công |

Tổng: **16 đồ thị**, đều có cộng đồng thật (LFR: cộng đồng cài sẵn; email-Eu-core: phòng ban).

## 5. Phân hoạch (sinh một lần, trước khi sinh cascade)

- Louvain (`networkx.community.louvain_communities`), **10 giá trị γ**: 0,1; 0,2; 0,3; 0,5; 0,7; **1,0**; 1,5; 2; 3; 5 × **5 seed** (0–4) → **50 phân hoạch** mỗi đồ thị [Cô: 10 γ × 5 seed; Đề xuất: lưới γ].
- **Mặc định** = γ = 1, seed 0 [Cô].
- **Mức sàn**: 5 phân hoạch ngẫu nhiên giữ nguyên phân bố kích thước cộng đồng của phân hoạch mặc định [Cô]. Không tính vào 50 phân hoạch, không dùng cho H-a.
- Lưu ra `data/partitions_<đồ thị>.json` và ghi hash.

## 6. Cascade

- Mô hình **IC**, quan sát **snapshot đầy đủ** ở trạng thái cuối [Cô].
- Số nguồn **k ∈ {1, 3, 5}**, chọn ngẫu nhiên đều, không trùng [Cô].
- **Hiệu chỉnh p và lọc kích thước** [Đề xuất, bắt buộc về kỹ thuật]: IC có chuyển pha (cascade hoặc tắt sớm, hoặc lan > 40%), nên không p nào cho trung vị tỉ lệ nhiễm trong 10–20%. Vì vậy: với mỗi (đồ thị, k), chọn p trên lưới sao cho tỉ lệ cascade rơi vào 10–20% là cao nhất (100 cascade thử mỗi p); khi sinh val/test, **chỉ giữ cascade có tỉ lệ nhiễm trong 10–20%** (lấy mẫu loại bỏ) [Cô: 10–20%]. Cascade thử không dùng lại.
- Mỗi (đồ thị, k): **50 cascade val** (chỉ để chọn ρ) + **200 cascade test** [Cô: 200 cascade].
- Tổng test: 16 × 3 × 200 = 9.600 cascade; mỗi cascade chạy với 50 phân hoạch → **480.000 lần định vị CommJordan**.

## 7. Bộ định vị

**Khoảng cách.** [Cô, Mục 7.1] k-center dùng khoảng cách **trên đồ thị con nhiễm** (đồ thị cảm sinh trên tập nhiễm; với B2 là đồ thị con nhiễm của từng cộng đồng I_c). Nếu đồ thị con bị đứt thành nhiều mảnh, chạy k-center riêng trên từng mảnh (mỗi mảnh ≥ 1 tâm). ED được chấm bằng khoảng cách trên **toàn đồ thị G**. Khoảng cách tính một lần cho mỗi cascade, dùng chung cho mọi phân hoạch.

**k-center tham lam (Gonzalez, xấp xỉ 2).** Trên tập điểm X: điểm đầu là Jordan center (node có độ lệch tâm nhỏ nhất tới X); sau đó lần lượt thêm điểm xa nhất. Bán kính r(k) = max khoảng cách từ một điểm tới tâm gần nhất. Lý do dùng heuristic: k-center là NP-hard.

| Bộ định vị | Cách làm |
|---|---|
| **B2 — CommJordan** [Cô, Mục 7.1] | Với mỗi cộng đồng c có tập nhiễm I_c ≠ ∅: k_c = k nhỏ nhất sao cho r(k) trên I_c ≤ ρ; tâm = k_c điểm của k-center. Ŝ_P = hợp các tâm. **Không** giả định k_c ≤ 1 |
| **Jordan center** (đối chứng, không cộng đồng) [Cô] | Cùng k-center với ngưỡng ρ, chạy trên toàn bộ tập nhiễm |
| **LPSI** (đối chứng, không cộng đồng) [Cô] | Wang et al. (AAAI 2017): S = D^{-1/2} A D^{-1/2}; Y = +1 node nhiễm, −1 còn lại; G* = (I − αS)^{-1} Y, α = 0,5; nguồn = node có G* > 0 và lớn hơn mọi hàng xóm |

**Chọn ρ [Đề xuất].** ρ ∈ {1, 2, 3, 4, 5, 6} hop, chọn trên **50 cascade val** (mỗi (đồ thị, k)) theo **ED trung bình nhỏ nhất** (metric chính của cô): CommJordan dùng phân hoạch mặc định; Jordan center chọn ρ riêng. Sau đó cố định cho toàn bộ test. Nguồn thật của val được dùng — hợp lệ vì val tách biệt test. B2 chạy **đúng mô tả của cô**, không thêm bước loại trùng.

## 8. Chấm điểm

- **ED**: ma trận khoảng cách giữa Ŝ và S; ghép Hungarian (`scipy.optimize.linear_sum_assignment`) trên min(|Ŝ|, |S|) cặp; ED = trung bình khoảng cách các cặp ghép [Cô, Mục 7.1 B5].
- **|k̂ − k|** báo cáo riêng [Cô].
- **F1@h**, h ∈ {0, 1, 2} [Cô]: precision = tỉ lệ nguồn đoán cách một nguồn thật ≤ h; recall = tỉ lệ nguồn thật cách một nguồn đoán ≤ h.
- Mỗi dòng CSV thô: đồ thị, μ, seed đồ thị, k, p, cascade_id, phân hoạch (γ, seed), ED, k̂, |k̂−k|, F1@0/1/2, tỉ lệ nhiễm.

## 9. Phân tích

Với mỗi (đồ thị, k), ma trận E (50 phân hoạch × 200 cascade):

1. **Phân rã hai nhân tố** (không lặp): SS_tổng = SS_phân hoạch + SS_cascade + SS_dư; η²_phân hoạch = SS_phân hoạch / SS_tổng.
2. **Δ = ED_mặc định − ED_tốt nhất**: cross-fit (chính) và đơn giản (phụ).
3. Quyết định H-a theo Mục 1.
4. **H-b**: Spearman giữa NMI(P, cộng đồng thật) và ED trung bình của P, trên 50 phân hoạch; kèm min–max NMI.
5. Báo cáo phụ: theo μ (xem trước H-e); ED của Jordan center, LPSI, phân hoạch ngẫu nhiên; |k̂ − k|; F1@h.
6. Hình: ED theo γ cho từng μ; phân bố η²; Δ theo đồ thị; NMI–ED.

## 10. Kiểm tra hợp lý

| Kiểm tra | Tiêu chí | Nếu không đạt |
|---|---|---|
| Cây ngẫu nhiên n = 500, k = 1, snapshot đầy đủ, 100 cascade [Cô] | Jordan center cho ED trung bình nhỏ (báo cáo giá trị thật; > 1 hop thì đánh dấu) | Dừng, kiểm code trước khi chạy đầy đủ |
| Phân hoạch ngẫu nhiên [Cô] | ED trung vị kém hơn phân hoạch mặc định | Dừng, kiểm code |
| Tỉ lệ nhiễm | Trung vị trong 10–20% với mọi (đồ thị, k) | Hiệu chỉnh lại p, ghi DEVIATIONS |
| Tính tất định | Chạy lại một cấu hình cho CSV giống hệt (so hash) | Sửa seed trước khi chạy đầy đủ |

### 10.1. Ghi nhận khi thiết kế (không dùng cho H-a) — giữ nguyên thiết kế của cô, báo cáo để GVHD đánh giá

1. **Tính định danh khi IC chạy đến hết.** Tập nhiễm cuối của IC là một cụm của đồ thị cạnh "sống" (percolation); với 1 nguồn, mọi node trong cụm có xác suất là nguồn như nhau. Mức độ được đo lại trên máy chạy bằng `identifiability_check.py` (seed riêng) và trích tự động vào báo cáo. Kiểm tra hợp lý trên cây có thể không đạt dưới thiết lập hiện tại.
2. **ED ghép min(|Ŝ|, |S|) cặp có lợi cho dự đoán thừa nguồn.** Khi ρ chọn theo ED, ρ nhỏ có xu hướng được chọn, |k̂ − k| lớn, và phân hoạch nhiều mảnh (kể cả ngẫu nhiên) có thể cho ED thấp hơn Louvain; số liệu thật lấy từ lượt chạy trên máy. Vì vậy báo cáo H0 trình bày ED **song song** với |k̂ − k| và F1@h.
3. Hai điểm trên không làm thay đổi giao thức; chúng được nêu trong báo cáo H0 để GVHD quyết định có điều chỉnh thiết lập (ví dụ IC dừng sau T bước) cho các bước sau hay không.

## 11. Thời gian ước tính

| Bước | Ước tính |
|---|---|
| Viết code (Claude) | 1–2 giờ |
| Cài môi trường, chạy thử `--smoke` (1 đồ thị LFR, 10 phân hoạch, 20 cascade) | ~10 phút |
| Chạy đầy đủ | ước 2–4 giờ trên 2 nhân (dưới mức < 10 CPU-giờ của cô); số thật đo ở bước smoke |
| Phân tích + báo cáo | ~30 phút |

## 12. Các bước Claude sẽ làm trên máy học viên

| # | Việc | Học viên thấy gì |
|---|---|---|
| S1 | Ghi toàn bộ file code vào `Documents\H0\` qua thư mục chia sẻ | File xuất hiện trong thư mục |
| S2 | Điều khiển màn hình: mở VS Code tại `Documents\H0` | VS Code mở thư mục H0 |
| S3 | Terminal: `python --version`; `python -m venv .venv`; kích hoạt; `pip install -r requirements.txt`; `pip freeze > requirements.lock.txt` | Lệnh chạy trong terminal VS Code |
| S4 | `python data_graphs.py` — sinh LFR, tải email-Eu-core | Log tiến độ |
| S5 | Tạo `H0_PROTOCOL.sha256` (khóa giao thức) | File hash xuất hiện |
| S6 | Bấm Run `01_kiem_tra_hop_ly.py`, rồi `02_chay_thu_smoke.py` | Kết quả kiểm tra hợp lý, thời gian đo được |
| S7 | `python run_h0.py` — chạy đầy đủ; Claude theo dõi qua `logs/h0.log` (đọc file, không chụp màn hình liên tục) | Terminal chạy; máy phải bật |
| S8 | `python analyze_h0.py` | Bảng và hình trong `results/summary/` |
| S9 | Viết nháp `BAO_CAO_H0.md` (2 trang, go/no-go) từ số liệu thật | File báo cáo |
| S10 | Học viên tải thư mục `H0` lên Drive (NCKH) | — |

**Claude sẽ không:** đổi ngưỡng hay cách đọc chính sau khi thấy kết quả; xóa file; đụng vào thư mục ngoài `Documents\H0`; chạy gì liên quan dòng tiền/provenance.

**Học viên cần:** cài sẵn VS Code + Python ≥ 3.10; giữ máy bật khi chạy; không dùng chuột/bàn phím lúc Claude thao tác; bấm đồng ý khi app hỏi quyền điều khiển máy.

## 13. Rủi ro và cách xử lý

| Rủi ro | Xử lý |
|---|---|
| LFR không hội tụ với một seed | Thử seed kế tiếp, ghi log; vẫn đủ 5 đồ thị mỗi μ |
| Máy ngủ / bị ngắt giữa chừng | `run_h0.py` lưu CSV theo từng đồ thị và bỏ qua phần đã xong khi chạy lại |
| Không tải được email-Eu-core | Học viên tải thủ công; nếu bỏ, ghi DEVIATIONS (lệch thiết kế của cô) |
| Chạy chậm hơn ước tính | Đo ở bước smoke; báo học viên trước khi chạy đầy đủ |
| Kết quả không đạt H-a | Không chỉnh gì; báo cáo NO-GO, đề xuất D1/D2 theo 30/10 Mục 7.6 |

## 14. Các điểm chờ chốt

- [ ] Cách đọc chính của H-a (Mục 1): "hoặc", Δ cross-fit, η² trên tổng phương sai
- [ ] Đơn vị đạt: đồ thị đạt khi ≥ 2/3 giá trị k đạt; GO khi ≥ 11/16 đồ thị
- [ ] Tham số LFR còn lại (Mục 4) và lưới γ (Mục 5)
- [ ] Cách chọn ρ trên val (Mục 7)
- [ ] email-Eu-core: tải tự động, nếu lỗi thì học viên tải

Nên gửi cô câu hỏi về cách đọc H-a (vế "hoặc", mẫu số của vế 2) trước khi khóa. Nếu cô trả lời sau khi đã chạy, các biến thể đã có sẵn ở phần báo cáo phụ, không cần chạy lại.
