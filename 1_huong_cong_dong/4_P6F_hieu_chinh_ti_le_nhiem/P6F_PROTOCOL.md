# Giao thức tiền đăng ký P6-F (bản nháp gửi GVHD duyệt)

Học viên: Nguyễn Lê Thanh Huyền · Căn cứ: Review 07/11/2026, Mục 7.1, 7.2, 7.5; QĐ13, QĐ15, QĐ17; O2, O4.
Trạng thái: **CHƯA KHÓA** — chỉ chạy chính thức sau khi GVHD trả lời xác nhận commit có tag `p6f-protocol`.

## 0. Những gì đã làm trước khi khóa

Theo Mục 7.5 bước 2, chỉ chạy bước **hiệu chỉnh tỉ lệ nhiễm f** (`hieu_chinh_f.py`, seed 7070). Bước này chỉ dùng các bộ định vị không dùng cộng đồng và hai mốc sàn, không sinh phân hoạch nào. Kết quả nằm ở `HIEU_CHINH_F.md`, `results/V3_table.csv` và `results/f_chon.json`. Bước chẩn đoán bổ sung (`chan_doan_truoc_khoa.py`, seed 7171, cũng chỉ dùng bộ định vị không cộng đồng) nằm ở `CHAN_DOAN.md` và `results/chan_doan/`. Những phát hiện ở bước này làm thay đổi thiết kế được ghi ở Mục 9.

## 1. Câu hỏi và giả thuyết

Chỉ xét những vùng có dư địa đo (đạt V3).

- **Q1.** Định vị dựa trên cộng đồng có tốt hơn bộ định vị không dùng cộng đồng mạnh nhất ở bài toán nhiều nguồn (k ∈ {3; 5}) không?
- **Q2.** Việc chọn phân hoạch (H-a), hoặc gộp nhiều phân hoạch (C3), có tạo thêm khác biệt so với phân hoạch mặc định không?
- **Đối chứng k = 1.** Kỳ vọng ở đây là phương pháp cộng đồng không tốt hơn Jordan toàn cục (đã chứng minh ở H0′). Đối chứng này không dùng để ra quyết định.

## 2. Đồ thị (cố định, SHA-256 trong `data/manifest.json`)

| Mã | Nguồn | Ghi chú |
|---|---|---|
| lfr10k_mu0.1_{0,1,2}, lfr10k_mu0.3_{0,1,2} | `nx.LFR_benchmark_graph`, n = 10.000, τ1 = 3, τ2 = 1,5, bậc TB 6, bậc max 100, cộng đồng 50–500, seed gốc 8080, LCC | Seed cụ thể ghi trong manifest |
| power_grid | Watts & Strogatz (1998); tệp `power_grid` của GraphSL, LCC | n = 4.941 |
| ca_grqc | Leskovec et al. (2007), SNAP, LCC | Tải và hiệu chỉnh trên máy học viên |

Tỉ lệ nhiễm f và tham số (T, p) của ic_T cho từng đồ thị lấy từ bước hiệu chỉnh (bảng ở Mục 8). Đồ thị nào **trượt V3** thì loại khỏi P6-F, và việc loại phải được báo trước khi chạy.

## 3. Lan truyền và cascade

- **si_t.** SI rời rạc, β = 0,3. Snapshot được chụp khi |I| ≥ mục tiêu, với mục tiêu ~ U(0,8f; 1,2f)·n.
- **ic_T.** IC dừng sau T bước. Dùng đúng (T, p) đã hiệu chỉnh cho từng bộ (đồ thị, f, k) ở bước 0.
- Cascade chỉ được nhận khi |I|/n ∈ [0,8f; 1,2f]. Nguồn chọn ngẫu nhiên đều trên toàn đồ thị.
- k ∈ {1; 3; 5}, biết trước k. Snapshot đầy đủ (quan sát toàn bộ tập nhiễm).
- Mỗi bộ (đồ thị, mô hình quan sát, k) có **50 cascade val** (chỉ dùng để chọn siêu tham số) và **200 cascade test**.
- Seed cascade: **9090**, khác seed 7070 của bước hiệu chỉnh và khác mọi thí nghiệm trước.

## 4. Phân hoạch

- **Louvain:** γ ∈ {0,1; 0,2; 0,3; 0,5; 0,7; 1,0; 1,5; 2,0; 3,0; 5,0} × seed {0; 1; 2}, tổng 30 phân hoạch.
- **Leiden:** RB-modularity, γ ∈ {0,5; 1,0; 1,5; 2,0; 3,0}, seed 0, tổng 5 phân hoạch.
- **Infomap:** cấu hình mặc định, seed 0, 1 phân hoạch.
- **Mặc định:** Louvain γ = 1,0, seed 0.
- **Sàn cho phân hoạch:** 5 phân hoạch ngẫu nhiên, tạo bằng cách hoán vị nhãn của phân hoạch mặc định (giữ nguyên phân phối kích thước).
- Với LFR: thêm cộng đồng thật, chỉ để tham khảo.

## 5. Bộ định vị

**Không dùng cộng đồng**

| Mã | Mô tả |
|---|---|
| rand (sàn) | k node nhiễm rút ngẫu nhiên; trung bình 20 lần rút mỗi cascade |
| deg (sàn) | k node nhiễm có bậc cao nhất |
| jordan | Greedy k-center (`kcenter_seq` đã sửa) trên đồ thị con nhiễm |
| lpsi | LPSI dạng lặp (α = 0,5; 60 vòng); top-k theo g |
| lpsi_r | LPSI + loại trùng: chọn lần lượt node có g cao nhất, bỏ mọi node trong bán kính r hop của node đã chọn; r ∈ {1; 2; 3} chọn trên val |

**Bộ không cộng đồng mạnh nhất** của mỗi bộ (đồ thị, quan sát, k) là bộ có ED val nhỏ nhất trong {jordan, lpsi, lpsi_r}. Bộ này được chọn trên val rồi khóa trước khi đọc test.

**Dùng cộng đồng**

| Mã | Mô tả |
|---|---|
| commjordan | Phân bổ D'Hondt theo số node nhiễm mỗi cộng đồng, rồi k-center trên đồ thị con nhiễm của từng cộng đồng (như H0′) |
| commlpsi | Như commjordan, nhưng trong mỗi cộng đồng lấy top-m_c theo LPSI lặp trên khối cộng đồng |
| soft (O4) | Prior mềm: s(v) = z(g_LPSI(v)) + λ·z(ρ_C(v)), trong đó ρ_C(v) = \|I ∩ C(v)\| / \|C(v)\| là mật độ nhiễm của cộng đồng chứa v. Chọn top-k có loại trùng bán kính r. λ ∈ {0; 0,25; 0,5; 1; 2} và r ∈ {1; 2; 3} chọn trên val. **λ = 0 trùng với lpsi_r**, nên khi cộng đồng không mang thông tin, phương pháp tự quay về bộ không cộng đồng |

## 6. Gộp phân hoạch (C3)

- **C3-rank (gộp mức kết quả).** Với mỗi phân hoạch Louvain/Leiden, tính điểm commlpsi của mọi node nhiễm rồi chuẩn hóa theo hạng về [0; 1]. Cộng điểm qua mọi phân hoạch, sau đó chọn top-k có loại trùng bán kính r (r ∈ {1; 2; 3} chọn trên val).
- **C3-cons (gộp mức phân hoạch).** Dựng ma trận đồng xuất hiện trên tập Louvain và Leiden (36 phân hoạch). Từ đó lập phân hoạch đồng thuận theo Lancichinetti & Fortunato (2012): ngưỡng τ = 0,5, Louvain lặp trên ma trận đồng thuận đến khi ổn định, tối đa 10 vòng. Sau đó chạy commjordan và commlpsi một lần trên phân hoạch đồng thuận.

## 7. Kiểm tra hợp lệ (định trước)

- **V1.** Cây ngẫu nhiên `nx.random_labeled_tree(2000)`, nguồn ngẫu nhiên, k = 1, nhiễm 5%, 100 cascade. Đạt khi ED_jordan ≤ 0,5·ED_rand cho cả si_t và ic_T. Xem lưu ý ở Mục 9.
- **V2.** ED trung bình của 5 phân hoạch ngẫu nhiên lớn hơn ED của phân hoạch mặc định, xét với commjordan và commlpsi.
- **V3.** Tính tại k = 3: ED_rand − min(ED_jordan, ED_lpsi) ≥ 1,0 hop, ở cả hai mô hình quan sát. Đồ thị nào trượt V3 thì không được đọc. V3 được tính lại trên dữ liệu test của P6-F và báo cáo cùng kết quả.

## 8. f đã chọn (từ bước hiệu chỉnh)

| Đồ thị | f* | V3 si_t (k=3) | V3 ic_T (k=3) | Đạt V3 |
|---|---|---|---|---|
| lfr10k_mu0.1_0 | 1% | 1.90 | 2.45 | ✓ |
| lfr10k_mu0.1_1 | 1% | 1.86 | 2.04 | ✓ |
| lfr10k_mu0.1_2 | 1% | 1.83 | 2.41 | ✓ |
| lfr10k_mu0.3_0 | 1% | 1.05 | 1.78 | ✓ |
| lfr10k_mu0.3_1 | 1% | 1.25 | 1.88 | ✓ |
| lfr10k_mu0.3_2 | 1% | 1.02 | 2.06 | ✓ |
| power_grid | 1% | 7.29 | 9.34 | ✓ |
| ca_grqc | 1% | 2.08 | 2.87 | ✓ |

Quy tắc chọn: f* = argmax_f min(V3_si_t, V3_ic_T) tại k = 3, hòa → f nhỏ hơn. (T, p) của ic_T cho từng (đồ thị, f, k) xem `results/V3_table.csv`.

## 9. Phát hiện ở bước hiệu chỉnh ảnh hưởng thiết kế

**P1 — Dư địa V3 trên LFR gần như toàn bộ đến từ cascade mà đồ thị con nhiễm đã tách sẵn thành ≥ k mảnh** (`results/V3_theo_tang.csv`). Ở f = 1%, k = 3, LFR μ = 0,1, ic_T: V3 = 2,83 hop ở tầng tách sẵn nhưng chỉ 0,16 hop ở tầng chồng lấn (1 mảnh); si_t: 2,67 so với 0,72. LFR μ = 0,3 tương tự (ic_T 2,92 so với 0,40; si_t 2,71 so với 0,96). Ở tầng tách sẵn, k-center đã tách nguồn theo mảnh liên thông nên cộng đồng gần như không có việc để làm; cộng đồng chỉ có thể giúp ở tầng chồng lấn — đúng nơi hiệu ứng sàn vẫn còn. Hệ quả: nếu đọc gộp, P6-F có thể ra K3 vì một lý do không liên quan tới giá trị của cộng đồng.

*Đề xuất A (xin GVHD quyết):* giữ f* như bảng trên, nhưng (i) mọi bảng kết quả phân tầng theo `n_comp` (tách sẵn / một phần / chồng lấn); (ii) điều kiện K2 ở Mục 11 được đánh giá trên tầng n_comp < k; (iii) V3 tính riêng cho tầng n_comp < k, tầng nào trượt thì báo là không đọc được.
*Đề xuất B (tốn thêm ~2 ngày):* tăng đường kính LFR (bậc TB 4 hoặc n = 50.000) và hiệu chỉnh lại, nhằm có dư địa ở tầng chồng lấn.

**P2 — LPSI top-k thường bằng hoặc kém sàn ngẫu nhiên** ở k = 3–5 (ví dụ LFR μ = 0,1, ic_T, f = 1%: 4,23 so với sàn 3,96). Nguyên nhân khả dĩ: k điểm g cao nhất nằm cạnh nhau quanh một đỉnh. Biến thể chỉ lấy đỉnh cục bộ tốt hơn rõ ở si_t (LFR μ = 0,3: 1,74 so với 2,18). Vì vậy giao thức thêm `lpsi_r` (top-k có loại trùng bán kính r) vào nhóm không cộng đồng, và prior mềm so với `lpsi_r` chứ không với LPSI top-k — để cải thiện không đến từ việc loại trùng.

**P3 — V1 trượt ở si_t do hiệu ứng biên của cây hữu hạn, không do code** (`CHAN_DOAN.md`, D2). ED Jordan 5,94 so với sàn 10,15 (59%, ngưỡng 50%); ic_T đạt (42%). Giả thuyết ban đầu ("cây Prüfer có nhiều đoạn bậc 2") bị bác: cây bậc trong ≥ 3 cùng cỡ còn trượt nặng hơn (62–75%), vì 60% node là lá và nguồn rút ngẫu nhiên phần lớn rơi vào lá, khi đó lan truyền chỉ đi về một phía và Jordan nằm giữa vùng nhiễm. Trên cây bậc ≥ 3 lớn (n = 20.000) với nguồn đặt xa lá (độ sâu ≤ 3), Jordan gần như trúng nguồn: ic_T 0%, si_t 10% sàn. *Đề xuất (xin GVHD quyết):* V1 dùng cây bậc trong ≥ 3, n = 20.000, nguồn ở độ sâu ≤ 3 — đúng tinh thần kiểm tra "Jordan đúng trên cây gần như vô hạn" mà vẫn có nguồn ngẫu nhiên; giữ phiên bản Prüfer làm thông tin phụ.

**P4 — Power Grid gần như không có cascade chồng lấn** (0–4/60 ở k = 3) do đường kính lớn: đồ thị này chỉ kiểm được tầng tách sẵn, nên đóng góp hạn chế cho Q1 nếu áp dụng Đề xuất A.

**P5 — ca-GrQc** lấy từ bản sao GitHub (SNAP bị chặn trên máy chạy), đã đối chiếu thống kê SNAP công bố: 5.242 node, 14.496 dòng cạnh, LCC 4.158 node (`data/manifest.json`). Đạt V3 tại f = 1%; cũng như LFR, dư địa nằm chủ yếu ở cascade tách sẵn (ic_T: 3,04 hop) và gần như không còn ở cascade chồng lấn (0,2–0,7 hop ở f = 2–5%). Nếu GVHD yêu cầu, học viên tải tệp gốc từ SNAP, đặt vào `data/ca-GrQc.txt` và chạy lại.

**P6 — Đề xuất B (đổi đồ thị) không giải quyết được tầng chồng lấn** (`CHAN_DOAN.md`, D1; 1 đồ thị mỗi họ, 60 cascade). Ở tầng chồng lấn, V3 (theo Jordan/LPSI) vẫn 0,15–1,3 hop với cả LFR thưa (bậc TB 4) lẫn LFR lớn (n = 30.000), gần như LFR gốc. Đồ thị thưa làm tăng dư địa chung chủ yếu vì có nhiều cascade tách sẵn hơn.

**P7 — lpsi_r là đối chứng không cộng đồng mạnh nhất ở si_t, và làm thay đổi kết luận về tầng chồng lấn** (`CHAN_DOAN.md`, D3; 8 đồ thị P6-F, f = 1%). Ở si_t, lpsi_r3 tốt nhất trên 7/8 đồ thị (trừ Power Grid); ở ic_T, Jordan tốt nhất trên cả 8. Gộp 8 đồ thị, tầng chồng lấn, k = 3: si_t — sàn 2,90, Jordan 2,45, LPSI 2,12, **lpsi_r3 0,94** (dư địa 1,96 hop); ic_T — sàn 3,40, Jordan 3,11, lpsi_r3 2,63 (dư địa 0,77). Hệ quả: (i) V3 nên tính với bộ không cộng đồng mạnh nhất gồm cả lpsi_r, khi đó tầng chồng lấn **có** dư địa ở si_t; (ii) ngưỡng để phương pháp cộng đồng "đạt" K2 cao hơn hẳn (phải thắng lpsi_r, ED ~0,9 ở tầng chồng lấn si_t); (iii) r = 3 là biên của lưới, nên mở rộng lưới r ∈ {1; …; 5}.

*Đề xuất tổng hợp (xin GVHD quyết):* dùng Đề xuất A (phân tầng theo số mảnh, K2 đánh giá trên tầng n_comp < k), giữ đồ thị như Mục 2, định nghĩa lại V3 = ED_sàn − min(ED_jordan, ED_lpsi, ED_lpsi_r), và mở rộng lưới r của lpsi_r, soft, C3-rank thành {1; …; 5}.

## 10. Metric và thống kê

- **ED (metric chính).** Ghép Hungarian một-một giữa nguồn thật và nguồn dự đoán, rồi lấy trung bình khoảng cách hop trên G.
- **Metric phụ:** F1@1, và tỉ lệ trúng top-k (tỉ lệ nguồn thật nằm đúng trong tập dự đoán).
- **Mọi bảng kèm hai mốc sàn** rand và deg (O2).
- **Δ (QĐ17).** Một so sánh "đạt" khi Δ ≥ max(0,3 hop; 10% ED của phương pháp đối chứng) **và** CI95 không chứa 0. CI95 lấy từ cluster bootstrap 10.000 lần theo cascade, ghép cặp trên cùng cascade.
- **H-a.** η² (hai nhân tố không lặp, phân hoạch × cascade, như H0′) ≥ 0,20 và Δ_cf (cross-fit chẵn/lẻ) đạt. Báo cáo thêm partial η² = SS_p / (SS_p + SS_res), chỉ để tham khảo, không dùng để ra quyết định.
- **Chọn bằng val.** Mọi siêu tham số (r, λ, bộ không cộng đồng mạnh nhất, phương pháp cộng đồng tốt nhất) đều chọn trên val. Test chỉ dùng để đánh giá.

## 11. Cây quyết định (Review 07/11 Mục 7.2)

- **Phạm vi:** chỉ xét k ∈ {3; 5}, trên các đồ thị đạt V3.
- **Cặp đạt:** một cặp (đồ thị, k) đạt một tiêu chí khi thỏa quy tắc Δ ở Mục 10.
- **Kết luận được chấp nhận:** khi ≥ 2/3 số cặp hợp lệ đạt.

| Kết cục | Điều kiện | Hướng đi |
|---|---|---|
| K1: P6 sống | H-a đạt (trên commlpsi hoặc commjordan, chọn trên val), **hoặc** C3 tốt nhất (chọn trên val) tốt hơn phân hoạch mặc định | Tiếp tục P6 (C1–C3); khóa R4 trước 15/01/2027 |
| K2: Cộng đồng có ích, chọn phân hoạch thì không | Không đạt K1, nhưng phương pháp cộng đồng tốt nhất trong {commjordan, commlpsi, soft, C3-rank, C3-cons} (chọn trên val) tốt hơn bộ không cộng đồng mạnh nhất | Chuyển sang Phương án B2; P6 thành chương phân tích |
| K3: Cộng đồng không có ích | Không đạt K1, không đạt K2 | Đóng P6; chuyển sang Phương án B1, bắt buộc có ablation |

## 12. Quy trình (QĐ15)

1. Commit giao thức này cùng `hieu_chinh_f.py` và kết quả hiệu chỉnh, gắn tag `p6f-protocol`, push lên GitHub, rồi email GVHD kèm link commit.
2. Chỉ chạy `run_p6f.py` sau khi GVHD xác nhận. Mọi log phải ghi commit hash của giao thức.
3. Kết quả được push trong một commit riêng sau khi chạy. Không viết lại lịch sử Git.
4. Mọi sai lệch so với giao thức (ví dụ LFR không hội tụ, thiếu ca-GrQc) ghi vào `DEVIATIONS.md` và báo GVHD **trước khi** đọc kết quả.

## 13. Chi phí

- **Bước hiệu chỉnh:** 37 giây trên máy học viên (Windows, Python 3.11.9, 21 tiến trình; 60 cascade/ô, 96 ô).
- **P6-F chính thức:** ước tính 20–40 CPU-giờ. Phần tốn nhất là 41 phân hoạch × 250 cascade × 3 k × 2 mô hình quan sát × 8 đồ thị. Khoảng cách chỉ tính trên đồ thị con nhiễm và từ các nguồn thật. LPSI dùng bản lặp, không nghịch đảo ma trận.

## Tài liệu

- Lancichinetti, A., & Fortunato, S. (2012). Consensus clustering in complex networks. *Scientific Reports*, 2, 336.
- Wang, Z., Wang, C., Pei, J., & Ye, X. (2017). Multiple source detection without knowing the underlying propagation model. *AAAI*.
- Watts, D. J., & Strogatz, S. H. (1998). Collective dynamics of 'small-world' networks. *Nature*, 393, 440–442.
- Leskovec, J., Kleinberg, J., & Faloutsos, C. (2007). Graph evolution: Densification and shrinking diameters. *ACM TKDD*, 1(1).
- Rosvall, M., & Bergstrom, C. T. (2008). Maps of random walks on complex networks reveal community structure. *PNAS*, 105(4), 1118–1123.
- Traag, V. A., Waltman, L., & van Eck, N. J. (2019). From Louvain to Leiden: guaranteeing well-connected communities. *Scientific Reports*, 9, 5233.
