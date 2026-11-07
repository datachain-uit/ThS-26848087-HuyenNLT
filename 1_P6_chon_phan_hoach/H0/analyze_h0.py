"""Phân tích H0 và tự sinh BAO_CAO_H0.md (H0_PROTOCOL.md Mục 1, 9).

  python analyze_h0.py            # phân tích lượt chính (results/raw)
  python analyze_h0.py --smoke    # phân tích dữ liệu chạy thử (chỉ để kiểm code)
"""
import _venv; _venv.ensure()
import argparse
import glob
import json
import math
import os
import datetime as dt

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import config as C
import h0lib as L


def two_way(E):
    """Phân rã hai nhân tố không lặp: E[phân hoạch, cascade]."""
    g = E.mean()
    ss_t = ((E - g) ** 2).sum()
    ss_p = E.shape[1] * ((E.mean(1) - g) ** 2).sum()
    ss_c = E.shape[0] * ((E.mean(0) - g) ** 2).sum()
    return ss_p, ss_c, ss_t


def delta_naive(E, d):
    m = E.mean(1)
    return float(m[d] - m.min()), int(np.argmin(m))


def delta_crossfit(E, d):
    """Chọn phân hoạch tốt nhất trên nửa cascade này, đo Δ trên nửa kia; lấy trung bình hai chiều."""
    a, b = np.arange(0, E.shape[1], 2), np.arange(1, E.shape[1], 2)
    out = []
    for fit, ev in ((a, b), (b, a)):
        best = int(np.argmin(E[:, fit].mean(1)))
        out.append(E[d, ev].mean() - E[best, ev].mean())
    return float(np.mean(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    root = "smoke" if a.smoke else "."
    data, raw = os.path.join(root, "data"), os.path.join(root, "results", "raw")
    summ = os.path.join(root, "results", "summary")
    os.makedirs(summ, exist_ok=True)
    manifest = json.load(open(os.path.join(data, "manifest.json"), encoding="utf-8"))
    files = sorted(glob.glob(os.path.join(raw, "*.csv")))
    files = [f for f in files if not f.endswith("_run1.csv")]
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    graphs = sorted(df.graph.unique(), key=lambda g: (manifest[g]["mu"], g))

    # ------------------------------------------------ H-a theo (đồ thị, k)
    rows_a, rows_b = [], []
    for gid in graphs:
        P = np.load(os.path.join(data, f"{gid}_parts.npz"))
        gam, pse, labels = P["gamma"], P["pseed"], P["labels"]
        n_louv = int((gam >= 0).sum())
        dmask = (gam == C.DEFAULT_PART[0]) & (pse == C.DEFAULT_PART[1])
        d = int(np.flatnonzero(dmask)[0]) if dmask.any() else 0
        cj = df[(df.graph == gid) & (df.method == "commjordan")]
        for k, g in cj.groupby("k"):
            E = g.pivot(index="part_id", columns="cascade", values="ed").sort_index().values
            E = E[:n_louv]
            ss_p, ss_c, ss_t = two_way(E)
            eta2 = ss_p / ss_t if ss_t > 0 else 0.0
            ratio_c = ss_p / ss_c if ss_c > 0 else np.inf
            dn, best = delta_naive(E, d)
            dc = delta_crossfit(E, d)
            ed_def = float(E[d].mean())
            v1 = (dc >= C.HA_DELTA_ABS) or (dc >= C.HA_DELTA_REL * ed_def)
            v2 = eta2 >= C.HA_ETA2
            rows_a.append(dict(graph=gid, mu=manifest[gid]["mu"], k=k, ed_default=ed_def,
                               ed_best=float(E[best].mean()), best_gamma=gam[best], best_seed=int(pse[best]),
                               delta_crossfit=dc, delta_naive=dn, eta2=eta2, ss_p_over_ss_c=ratio_c,
                               kerr_default=float(g[g.part_id == d].kerr.mean()),
                               v1=v1, v2=v2, pass_main=v1 and v2,
                               pass_naive=((dn >= C.HA_DELTA_ABS) or (dn >= C.HA_DELTA_REL * ed_def)) and v2,
                               pass_and=(dc >= C.HA_DELTA_ABS) and (dc >= C.HA_DELTA_REL * ed_def) and v2,
                               pass_ratio04=v1 and (ratio_c >= C.HA_ETA2)))
        # ------------------------------------------- H-b
        truth = np.load(os.path.join(data, f"{gid}_truth.npy"))
        nm = np.array([L.nmi(labels[i], truth) for i in range(n_louv)])
        edp = cj.groupby("part_id").ed.mean().reindex(range(n_louv)).values
        rho = spearmanr(nm, edp).correlation
        rows_b.append(dict(graph=gid, mu=manifest[gid]["mu"], spearman=rho,
                           nmi_min=nm.min(), nmi_max=nm.max(), pass_hb=abs(rho) < C.HB_RHO))
    A = pd.DataFrame(rows_a)
    B = pd.DataFrame(rows_b)
    G = A.groupby("graph").agg(mu=("mu", "first"), k_pass=("pass_main", "sum"), n_k=("k", "count")).reset_index()
    G["graph_pass"] = G.k_pass >= np.ceil(C.HA_K_PASS / 3 * G.n_k)
    n_need = math.ceil(C.HA_GRAPH_FRAC * len(G))
    go = int(G.graph_pass.sum()) >= n_need
    hb_ok = int(B.pass_hb.sum()) > len(B) / 2
    A.to_csv(os.path.join(summ, "Ha_by_graph_k.csv"), index=False)
    G.to_csv(os.path.join(summ, "Ha_by_graph.csv"), index=False)
    B.to_csv(os.path.join(summ, "Hb_by_graph.csv"), index=False)

    # ------------------------------------------------ báo cáo phụ
    M = (df.groupby(["mu", "k", "method"])
           .agg(ed=("ed", "mean"), kerr=("kerr", "mean"), f1_1=("f1_1", "mean"), frac=("frac_inf", "mean"))
           .reset_index())
    M.to_csv(os.path.join(summ, "methods_by_mu_k.csv"), index=False)
    gam_tab = (df[df.method == "commjordan"].groupby(["mu", "gamma"]).ed.mean().unstack(0))
    gam_tab.to_csv(os.path.join(summ, "ed_by_gamma.csv"))
    variants = {k: int(A.groupby("graph")[k].sum().ge(2).sum()) for k in
                ["pass_main", "pass_naive", "pass_and", "pass_ratio04"]}

    # ------------------------------------------------ hình
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4))
        for mu in gam_tab.columns:
            ax.plot(gam_tab.index, gam_tab[mu], marker="o", label=f"μ = {mu}")
        ax.set_xscale("log"); ax.set_xlabel("γ (resolution Louvain)"); ax.set_ylabel("ED trung bình (hop)")
        ax.axvline(1.0, ls="--", c="grey", lw=0.8); ax.legend(); fig.tight_layout()
        fig.savefig(os.path.join(summ, "fig_ed_by_gamma.png"), dpi=150)
        fig, ax = plt.subplots(figsize=(7, 4))
        A2 = A.sort_values(["mu", "graph", "k"])
        ax.bar(range(len(A2)), A2.eta2, color=["tab:green" if p else "tab:red" for p in A2.pass_main])
        ax.axhline(C.HA_ETA2, ls="--", c="k", lw=0.8)
        ax.set_xticks(range(len(A2))); ax.set_xticklabels([f"{g}|k{k}" for g, k in zip(A2.graph, A2.k)], rotation=90, fontsize=6)
        ax.set_ylabel("η² do phân hoạch"); fig.tight_layout()
        fig.savefig(os.path.join(summ, "fig_eta2.png"), dpi=150)
    except Exception as e:
        print("Bỏ qua vẽ hình:", e)

    sanity = {}
    sp_ = os.path.join("results", "summary", "sanity_tree.json")
    if os.path.exists(sp_):
        sanity = json.load(open(sp_, encoding="utf-8"))
    write_report(root, A, G, B, M, variants, go, hb_ok, n_need, sanity, manifest, a.smoke)
    print(f"H-a: {int(G.graph_pass.sum())}/{len(G)} đồ thị đạt (cần {n_need}) -> {'GO' if go else 'NO-GO'}")
    print(f"H-b: {int(B.pass_hb.sum())}/{len(B)} đồ thị có |ρ| < {C.HB_RHO}")


def fmt(x, d=2):
    return "—" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def write_report(root, A, G, B, M, variants, go, hb_ok, n_need, sanity, manifest, smoke):
    p = os.path.join(root, "BAO_CAO_H0.md")
    L_ = []
    w = L_.append
    w("# Báo cáo thí nghiệm tiền đề H0\n")
    w(f"Ngày tạo: {dt.datetime.now():%d/%m/%Y %H:%M} · Sinh tự động bởi `analyze_h0.py` từ CSV thô trong `results/raw/`.")
    if smoke:
        w("\n> **DỮ LIỆU CHẠY THỬ (seed 9999). Chỉ để kiểm code, không dùng làm kết luận H-a.**")
    w("\nCăn cứ: Review 30/10 Mục 7.1, 7.2, 7.3; QĐ11; QĐ12. Giao thức: `H0_PROTOCOL.md` (hash trong `H0_PROTOCOL.sha256`).\n")

    # ---- Phần 1: tóm tắt 2 trang
    w("## Phần 1. Tóm tắt (bản nộp GVHD)\n")
    w(f"**Kết luận đề xuất: {'GO' if go else 'NO-GO'}.** H-a đạt trên **{int(G.graph_pass.sum())}/{len(G)}** đồ thị "
      f"(ngưỡng ≥ {n_need}). H-b: **{int(B.pass_hb.sum())}/{len(B)}** đồ thị có |ρ(NMI, ED)| < {C.HB_RHO} "
      f"→ {'đạt' if hb_ok else 'không đạt'} (cần đa số).\n")
    if not go:
        w("Theo 30/10 Mục 7.6, nếu GVHD xác nhận NO-GO: giữ truy vết, chuyển sang D1 (ước lượng số nguồn bằng cộng đồng) hoặc D2 (đặt monitor theo cộng đồng).\n")
    w("### 1.1. Thiết lập\n")
    n_lfr = sum(1 for g in manifest if g.startswith("lfr"))
    w("| Thành phần | Thiết lập |\n|---|---|")
    w(f"| Đồ thị | {n_lfr} LFR (n = 1.000; μ ∈ {{0,1; 0,3; 0,5}}) {'+ email-Eu-core' if 'email_eu' in manifest else '(không có email-Eu-core)'} |")
    w(f"| Phân hoạch | Louvain {len(C.GAMMAS)} γ × {len(C.PART_SEEDS)} seed = {len(C.GAMMAS)*len(C.PART_SEEDS)}/đồ thị; mặc định γ = 1, seed 0 |")
    w(f"| Lan truyền | IC chạy đến hết, snapshot đầy đủ; giữ cascade có 10–20% node nhiễm; k ∈ {{1, 3, 5}}; {C.N_TEST} cascade test + {C.N_VAL} val mỗi cấu hình |")
    w("| Bộ định vị | B2 CommJordan (k-center trên đồ thị con nhiễm của từng cộng đồng, ngưỡng ρ chọn trên val theo ED); đối chứng Jordan center, LPSI |")
    w("| Metric | ED (Hungarian, min(|Ŝ|,|S|) cặp); |k̂ − k| và F1@h báo cáo riêng |\n")
    w("### 1.2. H-a theo từng đồ thị\n")
    w("Một đồ thị đạt khi đạt ở ≥ 2/3 giá trị k. Một cặp (đồ thị, k) đạt khi Δ_crossfit ≥ 0,3 hop **hoặc** ≥ 10% ED mặc định, **và** η² ≥ 0,20.\n")
    w("| Đồ thị | μ | k | ED mặc định | ED tốt nhất (γ) | Δ cross-fit | η² | |k̂−k| mặc định | Đạt |\n|---|---|---|---|---|---|---|---|---|")
    for _, r in A.sort_values(["mu", "graph", "k"]).iterrows():
        w(f"| {r.graph} | {r.mu} | {r.k} | {fmt(r.ed_default)} | {fmt(r.ed_best)} ({r.best_gamma:g}) | {fmt(r.delta_crossfit)} | "
          f"{fmt(r.eta2)} | {fmt(r.kerr_default,1)} | {'✓' if r.pass_main else '✗'} |")
    w("\n![η² theo đồ thị](results/summary/fig_eta2.png)\n")
    w("### 1.3. H-b: NMI và ED\n")
    w("| Đồ thị | μ | Spearman ρ(NMI, ED) | Khoảng NMI | |ρ| < 0,5 |\n|---|---|---|---|---|")
    for _, r in B.sort_values(["mu", "graph"]).iterrows():
        w(f"| {r.graph} | {r.mu} | {fmt(r.spearman)} | {fmt(r.nmi_min)}–{fmt(r.nmi_max)} | {'✓' if r.pass_hb else '✗'} |")
    w("\n![ED theo γ](results/summary/fig_ed_by_gamma.png)\n")
    w("### 1.4. Các cách đọc khác của H-a (báo cáo phụ, không dùng kết luận)\n")
    w("| Cách đọc | Số đồ thị đạt |\n|---|---|")
    w(f"| Chính: Δ cross-fit, \"hoặc\", η² trên tổng phương sai | {variants['pass_main']} |")
    w(f"| Δ đơn giản (chọn và đo trên cùng cascade) | {variants['pass_naive']} |")
    w(f"| \"và\" thay cho \"hoặc\" | {variants['pass_and']} |")
    w(f"| Vế 2 theo 04/10: SS_phân hoạch / SS_cascade ≥ 0,20 | {variants['pass_ratio04']} |\n")
    w("### 1.5. Kiểm tra hợp lý\n")
    if sanity:
        w(f"- Cây ngẫu nhiên n = 500, k = 1: Jordan center ED trung bình **{fmt(sanity['ed_mean'])}** hop, "
          f"ED = 0 ở {fmt(sanity['pct_ed0'],0)}% cascade → {'đạt' if sanity['pass'] else '**không đạt**'} (tiêu chí ED TB ≤ 1).")
    rp = M[M.method == "random_part"].ed.mean(); cjm = M[M.method == "commjordan"].ed.mean()
    w(f"- Phân hoạch ngẫu nhiên ED TB **{fmt(rp)}** so với Louvain **{fmt(cjm)}** → "
      f"{'đạt (ngẫu nhiên kém hơn)' if rp > cjm else '**không đạt** (ngẫu nhiên lại tốt hơn — xem Phần 4)'}.\n")
    w("### 1.6. So sánh bộ định vị (trung bình theo μ, k)\n")
    w("| μ | k | Phương pháp | ED | |k̂−k| | F1@1 | Tỉ lệ nhiễm |\n|---|---|---|---|---|---|---|")
    for _, r in M.iterrows():
        w(f"| {r.mu} | {r.k} | {r.method} | {fmt(r.ed)} | {fmt(r.kerr,1)} | {fmt(r.f1_1)} | {fmt(r.frac,3)} |")

    # ---- Phần 2: vì sao chọn tham số
    w("\n## Phần 2. Vì sao chọn các tham số này\n")
    w("Nhãn: **[Cô]** lấy nguyên từ Review 30/10; **[Bắt buộc]** cô không nêu nhưng code cần; **[Chọn]** lựa chọn có thể đổi.\n")
    w("| Tham số | Giá trị | Nguồn | Lý do |\n|---|---|---|---|")
    T = [
        ("LFR n, μ, số đồ thị", "1.000; {0,1; 0,3; 0,5}; 5/μ", "[Cô]", "30/10 Mục 7.3"),
        ("LFR τ₁, τ₂, bậc TB, bậc max, cỡ cộng đồng", "3; 1,5; 10; 50; 20–100", "[Bắt buộc]", "Hàm LFR cần đủ tham số; dùng mức phổ biến trong tài liệu (Lancichinetti et al. 2008)"),
        ("Thành phần liên thông lớn nhất", "Có", "[Bắt buộc]", "Node rời không có đường đi → không tính được ED"),
        ("email-Eu-core", "Bỏ hướng, bỏ self-loop, LCC; phòng ban = cộng đồng thật", "[Cô] + [Bắt buộc]", "Cô yêu cầu đồ thị có cộng đồng thật cho H-b"),
        ("Lưới γ", ", ".join(f"{g:g}" for g in C.GAMMAS), "[Chọn]", "Cô yêu cầu 10 giá trị, gợi ý thang log 0,1–5; lưới phải chứa đúng γ = 1 để có phân hoạch mặc định"),
        ("Seed phân hoạch", "0–4", "[Cô]", "10 γ × 5 seed"),
        ("Sinh phân hoạch trước cascade", "Có, lưu hash", "[Cô]", "Chống rò rỉ: phân hoạch không phụ thuộc cascade"),
        ("Phân hoạch ngẫu nhiên", f"{C.N_RANDOM_PARTS}, giữ phân bố kích thước của mặc định", "[Cô] + [Chọn số lượng]", "Mức sàn"),
        ("Mô hình lan truyền", "IC chạy đến hết, snapshot đầy đủ", "[Cô]", "30/10 Mục 7.3"),
        ("Đạt 10–20% nhiễm", "Chọn p tối đa hóa tỉ lệ cascade trong 10–20%, chỉ giữ cascade trong khoảng", "[Bắt buộc]", "IC có chuyển pha: không p nào cho trung vị trong 10–20% (chạy thử)"),
        ("k", "1, 3, 5", "[Cô]", "30/10 Mục 7.3"),
        ("Số cascade", f"{C.N_TEST} test + {C.N_VAL} val", "[Cô] + [Chọn val]", "Cô: 200 cascade; val cần để chốt ρ (30/10 Mục 7.1: tham số chốt trên val)"),
        ("Ngưỡng ρ của B2", "{1..6} hop, chọn theo ED trên val", "[Chọn]", "Cô yêu cầu ngưỡng nhưng không nêu lưới; ED là metric chính của cô"),
        ("k-center", "Greedy Gonzalez (xấp xỉ 2)", "[Bắt buộc]", "k-center là NP-hard"),
        ("Khoảng cách cho k-center", "Trên đồ thị con nhiễm; mảnh rời xử lý riêng", "[Cô]", "30/10 Mục 7.1: bán kính trên đồ thị con nhiễm"),
        ("Khoảng cách cho ED", "Trên toàn đồ thị G", "[Cô]", "ED = số hop giữa nguồn đoán và nguồn thật"),
        ("Jordan center (k > 1)", "Cùng k-center, ρ riêng chọn trên val", "[Chọn]", "Jordan cổ điển chỉ cho 1 nguồn"),
        ("LPSI", "α = 0,5; nguồn = cực đại địa phương dương", "[Chọn theo bài gốc]", "Wang et al., AAAI 2017"),
        ("Δ cross-fit", "Chọn trên nửa cascade, đo trên nửa kia", "[Chọn]", "Tránh thổi phồng khi lấy max trên 50 phân hoạch; Δ đơn giản báo cáo phụ"),
        ("Đơn vị đạt", "Đồ thị đạt khi ≥ 2/3 k đạt; GO khi ≥ 2/3 đồ thị", "[Cô] + [Chọn]", "Cô nói ≥ 2/3 đồ thị; mỗi đồ thị có 3 giá trị k nên cần quy tắc gộp"),
        ("Seed", f"{C.MASTER_SEED} (chính), {C.SMOKE_SEED} (chạy thử)", "[Chọn]", "Tái lập; chạy thử không nhìn trước dữ liệu chính"),
    ]
    for t in T:
        w("| " + " | ".join(t) + " |")

    # ---- Phần 3: code làm gì
    w("\n## Phần 3. Code làm gì\n")
    w("| File | Vai trò |\n|---|---|")
    w("| `config.py` | Toàn bộ tham số ở Phần 2; khóa hash cùng giao thức |")
    w("| `h0lib.py` | Sinh LFR, tải email-Eu-core; Louvain; mô phỏng IC; `CommJordan` (B2), `jordan_global`, `LPSI`; chấm ED/F1 |")
    w("| `run_h0.py` | Bước PREPARE (đồ thị + phân hoạch) rồi RUN (cascade, định vị, chấm điểm), ghi CSV thô từng đồ thị; chạy tiếp được khi bị ngắt |")
    w("| `sanity_checks.py` | Kiểm tra cây |")
    w("| `analyze_h0.py` | Phân rã phương sai, H-a, H-b, hình, sinh báo cáo này |")
    w("\nĐiểm then chốt của B2 (`h0lib.comm_jordan`): với mỗi cộng đồng có node nhiễm, lấy đồ thị con nhiễm của cộng đồng đó, "
      "chạy k-center tham lam: tâm đầu là Jordan center (độ lệch tâm nhỏ nhất), thêm điểm xa nhất cho tới khi mọi node nhiễm cách tâm gần nhất ≤ ρ hop. "
      "Số tâm chính là k_c; không giả định k_c ≤ 1. Khoảng cách giữa các node nhiễm được tính một lần cho mỗi cascade và dùng chung cho 50 phân hoạch.\n")
    w("Phân rã phương sai (`two_way`): ma trận ED kích thước 50 phân hoạch × 200 cascade; SS_tổng = SS_phân hoạch + SS_cascade + SS_dư; η² = SS_phân hoạch / SS_tổng.\n")

    # ---- Phần 4: ghi nhận
    w("## Phần 4. Ghi nhận và hạn chế (giữ nguyên thiết kế của cô, nêu để GVHD đánh giá)\n")
    w("1. **Tính định danh khi IC chạy đến hết.** Tập nhiễm cuối của IC là một cụm của đồ thị cạnh \"sống\"; với 1 nguồn, mọi node trong cụm có xác suất là nguồn như nhau.")
    ip_ = os.path.join("results", "summary", "identifiability.json")
    if os.path.exists(ip_):
        I_ = json.load(open(ip_, encoding="utf-8"))
        w("   Đo trên máy chạy (`identifiability_check.py`, seed riêng): Jordan center đoán trúng (ED = 0) "
          f"trên cây {fmt(I_['tree_ic_full']['pct_ed0'],0)}% khi IC chạy đến hết so với {fmt(I_['tree_ic_T6']['pct_ed0'],0)}% khi IC dừng sau 6 bước; "
          f"trên LFR μ = 0,3: {fmt(I_['lfr_mu0.3_ic_full']['pct_ed0'],0)}% so với {fmt(I_['lfr_mu0.3_ic_p0.3_T3']['pct_ed0'],0)}% (p = 0,3, T = 3).")
    else:
        w("   (Chưa chạy `identifiability_check.py`.)")
    w("2. **ED ghép min(|Ŝ|, |S|) cặp có lợi cho dự đoán thừa nguồn.** Khi ρ chọn theo ED, ρ nhỏ được chọn và |k̂ − k| rất lớn (xem bảng 1.6); "
      "phân hoạch nhiều mảnh (kể cả ngẫu nhiên) có thể cho ED thấp hơn. Vì vậy ED được đọc cùng |k̂ − k| và F1@h.")
    w("3. Hai điểm trên có thể làm H-a đạt hoặc không đạt vì lý do khác với giả thuyết. Đề xuất hỏi GVHD có điều chỉnh thiết lập (ví dụ IC dừng sau T bước; chọn ρ theo tiêu chí phạt đoán thừa) cho các bước sau.\n")
    w("## Phần 5. Tái lập\n")
    w("```\n.venv\\Scripts\\python.exe sanity_checks.py\n.venv\\Scripts\\python.exe run_h0.py\n.venv\\Scripts\\python.exe analyze_h0.py\n```")
    w("Phiên bản thư viện: `requirements.lock.txt`. Hash đồ thị và phân hoạch: `data/manifest.json`.")
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(L_) + "\n")
    print("Đã viết", p)


if __name__ == "__main__":
    main()
