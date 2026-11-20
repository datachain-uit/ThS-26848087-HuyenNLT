# H0b — Kế hoạch thí nghiệm thăm dò (không phải H0 chính thức)

**Mục đích.** H0 (seed 2026, giao thức đã khóa) cho NO-GO nhưng bị chi phối bởi hai lỗi đo: (1) đoán thừa nguồn (|k̂ − k| = 31–89) khiến ED chạm sàn với mọi phân hoạch, phân hoạch ngẫu nhiên lại tốt nhất; (2) IC chạy đến hết làm nguồn khó định danh. H0b kiểm tra **công cụ đo**: có thiết lập hợp lệ nào cho phép đo ảnh hưởng của phân hoạch không. Kết quả H0 giữ nguyên; chạy lại H0 chính thức hay chuyển D1/D2 do GVHD quyết định.

**Nguyên tắc.** Seed mới 3030. Báo cáo mọi ô. Thiết lập chỉ được xem xét khi **hợp lệ** theo 3 tiêu chí định trước — không chọn theo η²:
- V1: kiểm tra cây — Jordan center ED trung bình ≤ 1 hop (cây tam phân cân bằng sâu 7, nguồn ở gốc, tập nhiễm 100–200 node).
- V2: phân hoạch ngẫu nhiên có ED trung bình **kém hơn** Louvain.
- V3: |k̂ − k| trung bình ≤ 1.

**Lưới 3 × 3 = 9 ô** (cùng 3 đồ thị LFR μ ∈ {0,1; 0,3; 0,5}, 50 phân hoạch Louvain + 5 ngẫu nhiên, k ∈ {1, 3, 5}, 30 val + 50 test):

| | rho_ed (như H0) | rho_f1 | known_k |
|---|---|---|---|
| ic_full (như H0) | ô 1 | ô 2 | ô 3 |
| ic_T (IC dừng sau 4 bước) | ô 4 | ô 5 | ô 6 |
| si_t (SI β = 0,3, chụp khi đạt 10–20%) | ô 7 | ô 8 | ô 9 |

**Đầu ra.** `results/raw/*.csv` (CSV thô), `results/summary/H0b_cells.csv`, `H0b_REPORT.md` (sinh tự động từ dữ liệu máy chạy).

**Bước sau.** Ô hợp lệ có η² đáng kể → viết H0' protocol gửi GVHD duyệt, rồi chạy 16 đồ thị với seed mới. Không ô hợp lệ nào cho khác biệt → bằng chứng mạnh hơn cho NO-GO, chuyển D1/D2. Kết quả phụ cho D1: so known_k với ρ ước lượng cho thấy mức sai của ước lượng số nguồn.
