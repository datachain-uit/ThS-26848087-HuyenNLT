# H0c_fix — sửa lỗi `kcenter_seq` và chạy lại H0c

Ngày: 07/11/2026. Phát hiện khi rà soát code H0b/H0c.

## Lỗi
`h0b.kcenter_seq` (dùng chung cho H0b ô `known_k` và toàn bộ H0c) thay khoảng cách vô cùng bằng 1e6 rồi chọn tâm đầu bằng `argmin(max hàng)`.
Khi đồ thị con nhiễm của một cộng đồng đứt thành nhiều mảnh, mọi hàng có max = 1e6, nên tâm đầu luôn là phần tử đầu tiên (node có chỉ số nhỏ nhất) chứ không phải Jordan center. Tâm ở mảnh khác cũng là phần tử đầu tiên của mảnh đó.

## Mức ảnh hưởng (đo lại trên đồ thị H0c, 30 cascade mỗi cấu hình)
Tỉ lệ cộng đồng nhận tâm mà phần nhiễm bị đứt mảnh:

| Đồ thị | Phân hoạch mặc định | Louvain (toàn lưới) | Ngẫu nhiên |
|---|---|---|---|
| μ = 0,1 | 2–4% | 13–14% | 100% |
| μ = 0,3 | 37–50% | 34–47% | 100% |
| μ = 0,5 | 95–99% | 56–67% | 100% |

Đối chứng Jordan (toàn tập nhiễm, k tâm) bị ảnh hưởng ở `ic_T`: 10–37% cascade có tập nhiễm đứt mảnh.
CommLPSI và LPSI **không** bị ảnh hưởng.

## Sửa
Tâm đầu = Jordan center của mảnh lớn nhất; khi còn mảnh chưa có tâm, tâm kế tiếp = Jordan center của mảnh chưa có tâm lớn nhất; khi mọi mảnh đã có tâm, Gonzalez như cũ. Với đồ thị con liên thông, kết quả trùng hệt bản cũ (`test_kcenter.py`).

## Giữ nguyên
Toàn bộ kế hoạch `H0c_PLAN.md` (ngưỡng, tiêu chí chính `q_inf`, quy tắc kết luận), seed 4040, đồ thị và phân hoạch. Chỉ thay đổi đúng hàm `kcenter_seq`. Kết quả H0c cũ giữ nguyên trong thư mục `H0c/` để đối chiếu.
