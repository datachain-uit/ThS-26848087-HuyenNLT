# J-K — báo cáo (sinh tự động)

18/11/2026 10:53. Windows, Python 3.11.9. SHA {'JK_PLAN.md': '893a6642076ac3e9', 'jk.py': '005ba64d7e7aef4d'}. Giao thức: `JK_PLAN.md`.

## Kết luận: **NO-GO (M1 hoặc M3 trượt)**

- S: độ phủ G = 0.898 (cần [0,87; 0,93]) → đạt
- M2: độ phủ nhóm thấp nhất của G = 0.664 (cần < 0,85) → đạt
- M1: độ phủ nhóm thấp nhất của KS = 0.869 (cần ≥ 0,85) → đạt
- M3: kích thước KS / G = 7.89 (cần ≤ 1,2) → trượt

Tập dự đoán k (α_k = 0,05) trên 6000 mẫu: độ phủ 0.943, kích thước trung bình 3.97 giá trị (trên 15).

## Độ phủ (recall ≥ 0,3) và kích thước tập nguồn, α = 0,10, 50 lần lặp

| Phương pháp | Độ phủ | Kích thước | phủ k 1–3 | phủ k 4–7 | phủ k 8–11 | phủ k 12–15 |
|---|---|---|---|---|---|---|
| G | 0.898 ± 0.015 | 6.535 ± 0.194 | 0.664 | 0.873 | 0.989 | 0.991 |
| O | 0.905 ± 0.016 | 45.248 ± 8.289 | 0.925 | 0.899 | 0.899 | 0.905 |
| KS | 0.907 ± 0.016 | 51.572 ± 8.514 | 0.945 | 0.869 | 0.916 | 0.910 |
| KP | 0.893 ± 0.016 | 46.416 ± 8.396 | 0.928 | 0.855 | 0.895 | 0.906 |

## Kịch bản lệch prior số nguồn (kiểm trên k 5–10)

| Hiệu chỉnh | Độ phủ | Kích thước |
|---|---|---|
| G, chỉ k 10–15 (đoán thừa) | 0.795 ± 0.033 | 4.028 ± 0.142 |
| G, chỉ k 1–5 (đoán thiếu) | 1.000 ± 0.001 | 11.231 ± 0.429 |
| G, đủ k 1–15 | 0.958 ± 0.017 | 6.141 ± 0.216 |
| KS, đủ k 1–15 | 0.907 ± 0.025 | 4.878 ± 0.157 |

## Giới hạn

- Một đồ thị, một cấu hình SIR, mô hình GNN của tác giả. KS làm yếu giả định trao đổi được; chưa có bảo đảm lý thuyết.
