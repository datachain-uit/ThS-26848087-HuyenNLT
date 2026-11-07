# GraphSL baselines (Review 30/10 Mục 7.4, hạn 10/11/2026)

Mục đích: cài GraphSL, chạy LPSI, NetSleuth, GCNSI, IVGD, SL-VAE trên Karate, Jazz, NetScience để kiểm môi trường; thay GCNSI tự cài trong pilot bằng bản GraphSL (O3).

- Repo chính thức: github.com/xianggebenben/GraphSL (link `mbeyss/GraphSL` trong review có thể sai). PyPI: `GraphSL` 0.15.
- Giao thức: giữ mặc định README của GraphSL — IC, infect_prob = 0,3, sim_num = 100, seed_ratio = 0,2, `split_dataset` mặc định. Metric do GraphSL trả: acc, pr, re, f1, auc.
- Kiểm tra hợp lý: so kết quả với bảng trong bài GraphSL (arXiv 2405.03724) — điền sau khi đọc bài.

## Các bước (VS Code: mở file, bấm ▶ Run)
1. `00_setup_env.py` → tạo `.venv`, cài GraphSL, ghi `requirements.lock.txt` (pin phiên bản).
2. `01_chay_5_baseline.py` → log `logs/run.log`, kết quả `results/baselines.csv`.
3. (Sau bước 2) GCNSI hai chế độ chọn tập nguồn: (a) ngưỡng chọn trên tập train/val — mặc định GraphSL; (b) top-k với k thật. Chế độ (b) cần đọc mã GCNSI đã cài để lấy điểm của từng node; viết sau khi môi trường chạy được.

## Còn phải làm (không tự động)
- Đọc toàn văn bài GraphSL và 5 bài N6; điền `ma_tran_tinh_moi.md`.
