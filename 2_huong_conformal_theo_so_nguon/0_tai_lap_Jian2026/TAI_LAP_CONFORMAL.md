# Tái lập Jian et al. (AAAI 2026) — conformal multi-source detection

highSchool, randomSIR 'Slow' (R0 1–15, γ 0,1–0,4, 1–15 nguồn), pow_expected 0,3, 50 lần lặp, α = 0,10. Dùng đầu ra GNN (SD-STGCN) tác giả đã tính sẵn; chỉ tái lập phần conformal. Commit repo: xem COMMITS.txt.

Mã thoát: 0. Log: `cnsd/logfiles_repro/runCPhighSchoolSlowpow3_repro.log`

| Phương pháp | Độ phủ (tác giả) | Độ phủ (tái lập) | Kích thước tập (tác giả) | Kích thước tập (tái lập) |
|---|---|---|---|---|
| set_recall | 0.898 ± 0.014 | 0.898 ± 0.014 | 6.570 ± 0.186 | 6.570 ± 0.186 |
| set_prec | 0.899 ± 0.014 | 0.899 ± 0.014 | 9.669 ± 0.283 | 9.669 ± 0.283 |
| set_min | 0.897 ± 0.015 | 0.897 ± 0.015 | 8.057 ± 0.254 | 8.057 ± 0.254 |
