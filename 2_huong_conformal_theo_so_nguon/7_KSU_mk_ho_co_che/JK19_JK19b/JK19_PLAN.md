# J-K19 — Hiệu chỉnh trên hỗn hợp cơ chế lan truyền, hợp lệ theo (cơ chế, k) — KHÓA TRƯỚC KHI CHẠY

Khóa: 20/11/2026 ~16:20 (giờ VN), trước khi có kết quả. SHA file này và script ghi vào báo cáo.

## Động cơ (từ J-K17)
Khi mô phỏng sai LOẠI mô hình lan truyền, mọi phương pháp conformal (kể cả oracle biết k) mất bảo đảm.
Câu hỏi: nếu hiệu chỉnh trên một HỌ cơ chế khả dĩ (SI, IC, SIR) và coi cơ chế là biến ẩn thứ hai bên cạnh k,
có lấy lại được bảo đảm theo từng (cơ chế, k) với tập nhỏ hơn cách an toàn hiển nhiên (MDCP trên mọi nhóm) không?

## Kiểm tính mới (tóm tắt, chi tiết: docs/KHAO_SAT_TINH_MOI.md)
Gần nhất: MDCP (Yang & Jin 2026) — đồng đều trên nhiều phân phối, không dùng x để thu hẹp; MS-RLCP (2026) — chọn nguồn theo x, bảo đảm tiệm cận.
Chưa thấy áp dụng cho định vị nguồn với hai biến ẩn (cơ chế, k). Vì vậy MDCP là baseline BẮT BUỘC.

## Thiết kế
- Đồ thị: lfr10k_mu0.1_0, cora_ml; vùng nhiễm 50 và 200 → 4 tổ hợp. 3 seed (s = 0, 1, 2) → 12 lượt.
- Họ cơ chế F = {SI, IC, SIR} (tham số như J-K17). Mỗi cơ chế 8 000 mẫu hiệu chỉnh → ktr 1 400, kcal 600, kho 6 000 (rút 5 600/lần).
- Nhóm g = (cơ chế, k): 45 nhóm. Bộ phân loại RF dự đoán g (trên 3×1 400 ktr). Điểm nút: HGB cấu trúc huấn luyện trên ktr trộn.
- Dữ liệu triển khai: 4 000 mẫu cho mỗi cơ chế trong họ (SI, IC, SIR) và ngoài họ (SIR-nhanh, SIR-dai); rút 400/lần; 50 lần.
- Phương pháp (ngưỡng trên điểm độ sâu, luật phủ/kích thước như J-K11/J-K17):
  - G: split CP trên hiệu chỉnh trộn.
  - O: oracle biết (cơ chế, k) (ngoài họ: dùng ngưỡng SIR với k thật).
  - WCP-mk: WCP với trọng số P̂(g | x) trên 45 nhóm (chỉ bảo đảm biên).
  - MD-m: max theo cơ chế của ngưỡng biên theo cơ chế (đồng đều theo cơ chế, KHÔNG theo k).
  - MD-mk: max trên 45 nhóm (đồng đều theo (cơ chế, k)) — baseline có CÙNG bảo đảm với phương pháp đề xuất.
  - KSU*-SIR: KSU* hiệu chỉnh chỉ trên SIR (cách làm khi tin một cơ chế — đối chứng J-K17).
  - KSU*-k: KSU* theo k trên dữ liệu trộn (bỏ qua cơ chế).
  - **KSU*-mk (đề xuất):** tập Mondrian K̂(x) trên 45 nhóm (α_g 0,02) + ngưỡng theo nhóm (α_s 0,08); C(x) = top-max_{g∈K̂} t_g.
    Bảo đảm: P(phủ | cơ chế, k) ≥ 0,90 cho mọi cơ chế trong họ và mọi k (cùng chứng minh Mệnh đề KSU*).

## Tiêu chí (12 lượt × 3 cơ chế trong họ = 36 bộ "trong họ")
- V1 (hợp lệ): KSU*-mk phủ k xấu nhất ≥ 0,88 ở ≥ 34/36 bộ trong họ VÀ không bộ nào < 0,86.
- V2 (hiệu quả, chính): kích thước KSU*-mk < MD-mk ở ≥ 75% (≥ 27/36) bộ trong họ.
- Kết luận: V1 ∧ V2 → "J-K19 ĐẠT — đóng góp phương pháp cho bản journal"; chỉ V1 → "HỢP LỆ NHƯNG KHÔNG HIỆU QUẢ HƠN MDCP"; ¬V1 → "CẦN XEM LẠI".
- Mô tả kèm (không quyết định): so với MD-m, KSU*-k, KSU*-SIR (phủ theo k ở từng cơ chế); giá so với O; phủ ngoài họ.

## Ghi chú minh bạch
- 16:25: chạy thử trên shell phụ (Linux, NO_VENV); `_tmp_smoke_test.py` là bản sao jk19.py chỉ đổi đường dẫn lưu kết quả thử, không xóa được, không dùng cho chạy chính. Chạy thử: luật phủ khớp; kích thước = cả đồ thị vì mỗi nhóm chỉ vài mẫu (dự kiến, không đọc số).

## Không thay đổi sau khi xem kết quả
Mọi tham số cố định ở đây. Chạy thử chỉ để kiểm cài đặt.
