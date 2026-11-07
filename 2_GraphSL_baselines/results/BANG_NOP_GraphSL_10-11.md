# GraphSL — 5 baseline × 3 đồ thị (nộp 10/11)

Chạy trên máy cá nhân (CPU), GraphSL 0.15, seed 0, chia train/test 60/40 theo `split_dataset` của GraphSL. Log: `logs/run.log` (bảng A), `logs/run_va.log` (bảng B, C), `logs/degree_baseline.log` (bảng D). Phiên bản thư viện: `requirements.lock.txt`.

**Thiết lập dữ liệu (mặc định GraphSL):** IC, 100 cascade, `seed_ratio = 0,2`, nguồn chọn trong nhóm (20% + 5%) node bậc cao nhất, 10 bước, vector nhiễm = trung bình 10 lần mô phỏng. Với IC, GraphSL dùng xác suất lây = `threshold` = 0,5 (tham số `infect_prob = 0,3` bị bỏ qua).

**Lỗi phát hiện trong GraphSL 0.15** (vẫn còn trên nhánh chính, commit `242751f`): `diffusion_generation` truyền tập nguồn cho ndlib dưới dạng vector 0/1 trong khi ndlib cần danh sách mã node → mọi cascade lan từ node 0 và 1, không liên quan nhãn nguồn. Bảng A dùng dữ liệu lỗi này; bảng B dùng bản vá sửa đúng một dòng (truyền danh sách mã node).

### A. Mặc định GraphSL (dữ liệu lỗi) — chỉ dùng làm bằng chứng lỗi

| Đồ thị | Phương pháp | acc | pr | re | f1 | auc | train (s) |
|---|---|---|---|---|---|---|---|
| karate | LPSI | 0.749 | 0.402 | 0.871 | 0.550 | 0.695 | 54 |
| karate | NetSleuth | 0.937 | 0.885 | 0.738 | 0.805 | 0.858 | 23 |
| karate | GCNSI | 0.937 | 0.885 | 0.738 | 0.805 | 0.986 | 1108 |
| karate | IVGD | 0.953 | 0.867 | 0.867 | 0.867 | 0.986 | 5803 |
| karate | SL-VAE | 0.971 | 0.857 | 1.000 | 0.923 | 0.983 | 139 |
| jazz | LPSI | 0.273 | 0.213 | 1.000 | 0.351 | 0.134 | 15 |
| jazz | NetSleuth | 0.794 | 0.330 | 0.042 | 0.075 | 0.511 | 74 |
| jazz | GCNSI | 0.940 | 0.815 | 0.899 | 0.855 | 0.972 | 79 |
| jazz | IVGD | 0.677 | 0.379 | 1.000 | 0.549 | 0.971 | 17954 |
| jazz | SL-VAE | 0.908 | 0.807 | 0.702 | 0.749 | 0.935 | 149 |
| netscience | LPSI | 0.798 | 0.000 | 0.000 | 0.000 | 0.498 | 7741 |
| netscience | NetSleuth | 0.799 | 0.000 | 0.000 | 0.000 | 0.499 | 8 |
| netscience | GCNSI | 0.936 | 0.800 | 0.906 | 0.850 | 0.964 | 7132 |
| netscience | IVGD | — | — | — | — | — | chưa chạy |
| netscience | SL-VAE | — | — | — | — | — | chưa chạy |

IVGD–NetScience và SL-VAE–NetScience không chạy ở bảng A (IVGD ước tính 4–5 ngày CPU, dữ liệu lỗi).

### B. Dữ liệu đã vá

| Đồ thị | Phương pháp | acc | pr | re | f1 | auc | train (s) |
|---|---|---|---|---|---|---|---|
| karate | LPSI | 0.806 | 0.477 | 1.000 | 0.646 | 0.780 | 3 |
| karate | NetSleuth | 0.938 | 0.890 | 0.742 | 0.809 | 0.861 | 2 |
| karate | GCNSI | 0.971 | 0.857 | 1.000 | 0.923 | 0.986 | 60 |
| karate | IVGD | 0.887 | 0.677 | 0.788 | 0.720 | 0.935 | 3336 |
| karate | SL-VAE | 0.968 | 0.858 | 0.983 | 0.916 | 0.983 | 159 |
| jazz | LPSI | 0.265 | 0.211 | 1.000 | 0.349 | 0.124 | 14 |
| jazz | NetSleuth | 0.794 | 0.325 | 0.042 | 0.074 | 0.510 | 82 |
| jazz | GCNSI | 0.940 | 0.815 | 0.899 | 0.855 | 0.972 | 208 |
| jazz | IVGD | 0.593 | 0.326 | 1.000 | 0.492 | 0.972 | 12695 |
| jazz | SL-VAE | 0.905 | 0.802 | 0.688 | 0.739 | 0.952 | 210 |
| netscience | LPSI | 0.933 | 0.750 | 1.000 | 0.857 | 0.944 | 6462 |
| netscience | NetSleuth | 0.804 | 0.790 | 0.025 | 0.048 | 0.512 | 225 |
| netscience | GCNSI | 0.935 | 0.800 | 0.896 | 0.846 | 0.961 | 7530 |
| netscience | IVGD | — | — | — | — | — | chưa chạy |
| netscience | SL-VAE | 0.856 | 0.802 | 0.371 | 0.507 | 0.552 | 1101 |

IVGD–NetScience: chạy trên Colab GPU (`colab/GraphSL_va_loi_colab.ipynb`), chưa có kết quả.

### C. GCNSI — các chế độ chọn tập nguồn (dữ liệu đã vá)

| Đồ thị | Chế độ | acc | pr | re | f1 | auc |
|---|---|---|---|---|---|---|
| karate | GraphSL gốc (ngưỡng train; có lỗi chỉ số trong test) | 0.971 | 0.857 | 1.000 | 0.923 | 0.986 |
| karate | Sửa lỗi chỉ số, ngưỡng chọn trên train | 0.971 | 0.857 | 1.000 | 0.923 | 0.986 |
| karate | Top-k với k thật | 0.953 | 0.867 | 0.867 | 0.867 | 0.986 |
| karate | Ngưỡng chọn trên val (75/25 tách từ train) | 0.971 | 0.857 | 1.000 | 0.923 | 0.986 |
| jazz | GraphSL gốc (ngưỡng train; có lỗi chỉ số trong test) | 0.940 | 0.815 | 0.899 | 0.855 | 0.972 |
| jazz | Sửa lỗi chỉ số, ngưỡng chọn trên train | 0.940 | 0.815 | 0.899 | 0.855 | 0.972 |
| jazz | Top-k với k thật | 0.927 | 0.815 | 0.815 | 0.815 | 0.972 |
| jazz | Ngưỡng chọn trên val (75/25 tách từ train) | 0.955 | 0.812 | 1.000 | 0.897 | 0.972 |
| netscience | GraphSL gốc (ngưỡng train; có lỗi chỉ số trong test) | 0.935 | 0.800 | 0.896 | 0.846 | 0.961 |
| netscience | Sửa lỗi chỉ số, ngưỡng chọn trên train | 0.938 | 0.807 | 0.906 | 0.854 | 0.966 |
| netscience | Top-k với k thật | 0.923 | 0.807 | 0.807 | 0.807 | 0.966 |
| netscience | Ngưỡng chọn trên val (75/25 tách từ train) | 0.938 | 0.809 | 0.904 | 0.854 | 0.967 |

Lỗi chỉ số trong `GCNSI.test`: vòng đánh giá dùng `lpsi_input[i]` với `i` còn sót từ vòng trước → mọi cascade test dùng chung một đầu vào.

### D. Mốc đoán theo bậc (không dùng lan truyền)

| Đồ thị | Chọn tập nguồn | acc | pr | re | f1 | auc |
|---|---|---|---|---|---|---|
| karate | Top-k với k thật | 0.953 | 0.867 | 0.867 | 0.867 | 0.986 |
| karate | Ngưỡng chọn trên train | 0.971 | 0.857 | 1.000 | 0.923 | 0.986 |
| jazz | Top-k với k thật | 0.927 | 0.815 | 0.815 | 0.815 | 0.972 |
| jazz | Ngưỡng chọn trên train | 0.904 | 0.672 | 1.000 | 0.804 | 0.972 |
| netscience | Top-k với k thật | 0.920 | 0.801 | 0.801 | 0.801 | 0.964 |
| netscience | Ngưỡng chọn trên train | 0.860 | 0.588 | 1.000 | 0.741 | 0.964 |

Kết quả mốc theo bậc trên dữ liệu gốc và bản vá trùng nhau (mốc không nhìn vector nhiễm).

## Kiểm tra hợp lý so với tài liệu gốc

Bài GraphSL (arXiv 2405.03724) không có bảng kết quả, nên đối chiếu với bảng 3 bài IVGD (Wang, Jiang & Zhao, WWW 2022; IC, 10% nguồn ngẫu nhiên, train/test 8:2). Kết quả **không cùng cỡ** và thứ hạng đảo: trong bài IVGD, GCNSI có F1 0,02–0,16 và IVGD 0,92–0,99; ở bảng B, GCNSI 0,85–0,92 và IVGD 0,49–0,72. Chỉ LPSI–NetScience gần cùng cỡ (0,857 so với 0,920).

## Nhận xét

1. Bảng A không dùng làm baseline được: lan truyền không liên quan đến nguồn; điểm cao của GCNSI/IVGD/SL-VAE đến từ việc học "nguồn = node bậc cao".
2. Với thiết lập mặc định, Karate và Jazz gần bão hòa (84% và 98% node nhiễm) nên ngay cả bản vá, vector nhiễm mang rất ít thông tin về nguồn; NetScience nhiễm ~43%.
3. Mốc đoán theo bậc đạt auc 0,96–0,99 và trùng GCNSI trên Karate, Jazz (top-k). Không phương pháp nào vượt rõ mốc này → benchmark mặc định chủ yếu đo việc học phân phối nguồn, không đo khả năng truy vết ngược lan truyền.
4. Đề xuất (chờ cô duyệt): chạy thêm thiết lập nguồn ngẫu nhiên 10% (gần bài IVGD) và/hoặc không bão hòa, giữ bản vá, báo cáo kèm mốc theo bậc.
