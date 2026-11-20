# H0c — Kiểm tra ba điều kiện tiền đề của P6 (thăm dò có đăng ký trước)

Viết và khóa (SHA-256 ghi trong log lúc bắt đầu chạy) **trước khi** có bất kỳ kết quả nào. Seed mới 4040.
H0 và H0b giữ nguyên; H0c không thay thế H0 chính thức — kết quả trình GVHD để quyết định.

## Câu hỏi
- **Đ1 (H-a):** đổi phân hoạch Louvain (toàn lưới γ) có làm ED thay đổi đáng kể không?
- **Đ2:** khác biệt có còn khi chỉ xét các phân hoạch *hợp lý* γ ∈ {0,5; 0,7; 1; 1,5; 2; 3; 5} (bỏ γ ≤ 0,3 — gần như không chia)?
- **Đ3 (H-b):** một tiêu chí không cần nhãn có chọn được phân hoạch tốt hơn mặc định không?

## Thiết lập (chỉ dùng chế độ đo đã hợp lệ ở H0b)
- Đồ thị: 3 LFR n = 1000, μ ∈ {0,1; 0,3; 0,5} (sinh mới với seed 4040; lưu cả cộng đồng thật).
- Phân hoạch: 50 Louvain (10 γ × 5 seed) + 5 ngẫu nhiên (sàn) + cộng đồng thật LFR (tham chiếu, không tính vào η²). Mặc định: γ = 1, seed 0.
- Quan sát: `ic_T` (IC dừng sau 4 bước) và `si_t` (SI β = 0,3, chụp khi nhiễm 10–20%). Bỏ `ic_full` (không định danh được).
- Số nguồn: biết trước k ∈ {3, 5} (khâu ước lượng k hỏng ở H0/H0b; đó là câu hỏi của D1).
- **Đặt nguồn (B):** `random` (như H0/H0b) và `spread` (mỗi nguồn ở một cộng đồng thật khác nhau — kịch bản thuận lợi nhất cho phân hoạch).
- 100 cascade test cho mỗi (đồ thị, k, quan sát, đặt nguồn).

## Bộ định vị (A)
- **CommJordan** (B2 của cô, có biết k): phân bổ k tâm cho các cộng đồng theo số node nhiễm (D'Hondt), mỗi cộng đồng chạy greedy k-center trên đồ thị con nhiễm của nó.
- **CommLPSI** (họ thứ hai — chia để trị kiểu lan truyền nhãn): bỏ cạnh giữa các cộng đồng, chạy LPSI (α = 0,5) trên từng khối, mỗi cộng đồng chọn m_c node điểm cao nhất (cùng phân bổ D'Hondt). Với phân hoạch 1 cộng đồng, CommLPSI ≡ LPSI.
  *Giới hạn:* đây là đại diện cho họ phương pháp chia để trị theo cộng đồng, **không** phải bản tái hiện trung thực MSDCM/CNSL/CLP (cần đọc toàn văn N6 trước).
- Đối chứng không phân hoạch: Jordan (k-center đúng k tâm), LPSI top-k.

## Tiêu chí không cần nhãn (Đ3) — tính từ tập nhiễm và phân hoạch, không dùng nguồn thật
- **`q_inf` (tiêu chí CHÍNH, định trước):** modularity của phân hoạch thu hẹp trên đồ thị con nhiễm.
- Phụ (thăm dò): `q_full` (modularity trên G), `conc` (tỉ lệ node nhiễm nằm trong k cộng đồng nhiễm lớn nhất), `fitk` (−|số cộng đồng chứa ≥ 10% node nhiễm − k|), `cons` (NMI trung bình với các phân hoạch Louvain khác).
- Chọn: mỗi cascade lấy phân hoạch Louvain có tiêu chí cao nhất (hòa → γ gần 1, seed nhỏ).

## Độ đo và quy tắc quyết định (định trước)
Cho mỗi tổ hợp (quan sát × đặt nguồn × bộ định vị), xét 6 cặp (đồ thị × k):
- **Cặp đạt Đ1:** η² (toàn Louvain) ≥ 0,20 **và** Δcf ≥ max(0,3 hop; 10% ED mặc định). Δcf: chọn phân hoạch tốt nhất trên nửa A cascade, đo ED trên nửa B, so với mặc định trên nửa B (và đổi vai, lấy trung bình).
- **Cặp đạt Đ2:** như trên nhưng chỉ trên tập phân hoạch hợp lý.
- **Cặp đạt Đ3:** ED_mặc định − ED_chọn-bằng-`q_inf` ≥ max(0,3 hop; 10%).
- **Tổ hợp đạt** một điều kiện nếu ≥ 4/6 cặp đạt.
- **Hợp lệ:** V2 (phân hoạch ngẫu nhiên kém hơn Louvain mặc định) phải đúng; nếu sai, tổ hợp không được đọc.

**Kết luận P6:**
- GO có điều kiện: có tổ hợp hợp lệ đạt cả Đ1, Đ2, Đ3 → P6 có phạm vi rõ (nêu đúng tổ hợp đó).
- Cần thêm phương pháp: đạt Đ1, Đ2 nhưng không đạt Đ3 → bài toán có, nhưng chưa có tiêu chí chọn (P6 phải đề xuất tiêu chí — rủi ro cao).
- NO-GO mạnh: không tổ hợp hợp lệ nào đạt Đ2, kể cả `spread` → chọn phân hoạch không đáng tối ưu.

Báo cáo mọi tổ hợp; không đổi ngưỡng hay tiêu chí chính sau khi xem kết quả. Ngoài ra báo cáo ED của phân hoạch thật và của oracle (tốt nhất từng cascade) làm trần tham chiếu.
