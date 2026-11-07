"""Kiểm tra định danh nguồn, bản so sánh công bằng (thay cho H0/identifiability_check.py).

Bản cũ so IC chạy đến hết (p = 0,9) với IC dừng sau 6 bước (p = 1,0): khác cả p lẫn thời điểm dừng,
nên con số "3% so với 74%" phóng đại khác biệt. Bản này giữ CÙNG p, chỉ đổi thời điểm dừng
(T = 2, 4, 6 bước, hoặc chạy đến hết), một nguồn ngẫu nhiên, 200 cascade, không lọc theo kích thước
(báo cáo kích thước để đọc kèm). Bộ định vị: Jordan center của tập nhiễm.

  python identifiability_v2.py     -> results/identifiability_v2.csv, in bảng ra màn hình
"""
import _venv; _venv.ensure()
import os
import numpy as np
import networkx as nx
import pandas as pd
import h0lib as L
import h0b as B

N_CASC = 200
STOPS = [2, 4, 6, None]          # None = chạy đến hết


def run(name, G, ps, seed):
    A = L.graph_arrays(G); n = A.shape[0]; rows = []
    for p in ps:
        for T in STOPS:
            rng = np.random.default_rng(L.sub_seed(seed, name, p, T))
            eds, sizes = [], []
            while len(eds) < N_CASC:
                s = rng.choice(n, 1, replace=False)
                I = L.simulate_ic(A, s, p, rng) if T is None else B.ic_steps(A, s, p, rng, T)
                if I.size < 3:          # cascade gần như không lan: bỏ (như nhau cho mọi T)
                    continue
                c = L.CascadeCtx(A, s, I)
                eds.append(L.score_pos(c, np.array(B.kcenter_seq(c.DIIsub, 1)[0]))["ed"]); sizes.append(I.size)
            eds = np.array(eds)
            rows.append(dict(graph=name, p=p, stop="đến hết" if T is None else f"T={T}",
                             frac_inf=float(np.mean(sizes) / n), ed_mean=float(eds.mean()),
                             pct_ed0=float((eds == 0).mean() * 100), pct_ed_le1=float((eds <= 1).mean() * 100)))
            print(f"{name:12s} p={p:<5} {rows[-1]['stop']:8s} nhiễm TB {rows[-1]['frac_inf']:.3f} | "
                  f"ED TB {rows[-1]['ed_mean']:.2f} | đoán trúng {rows[-1]['pct_ed0']:.0f}% | ED<=1 {rows[-1]['pct_ed_le1']:.0f}%", flush=True)
    return rows


def run_same_size(name, G, seed, T):
    """Phần B: CÙNG kích thước nhiễm 10–20% (như H0 và H0'), mỗi kiểu lan truyền tự hiệu chỉnh p
    (IC đến hết, IC dừng sau T bước: 4 trên LFR như H0', 12 trên cây như H0b) hoặc chụp đúng kích thước (SI). Đây là phép so sánh sát với
    khác biệt thật giữa H0 và H0'."""
    A = L.graph_arrays(G); n = A.shape[0]; rows = []
    sims = {"IC đến hết": lambda s, p, r: L.simulate_ic(A, s, p, r),
            f"IC T={T}": lambda s, p, r: B.ic_steps(A, s, p, r, T)}
    for mode in ["IC đến hết", f"IC T={T}", "SI chụp 10-20%"]:
        rng = np.random.default_rng(L.sub_seed(seed, name, mode))
        p = None
        if mode in sims:
            p, acc = B.calib_p(A, 1, L.sub_seed(seed, name, mode, "cal"), sims[mode])
        eds = []; tries = 0
        while len(eds) < N_CASC and tries < 400 * N_CASC:
            tries += 1
            s = rng.choice(n, 1, replace=False)
            I = sims[mode](s, p, rng) if mode in sims else B.si_until(A, s, rng, int(rng.uniform(B.LO, B.HI) * n))
            if not (B.LO <= I.size / n <= B.HI):
                continue
            c = L.CascadeCtx(A, s, I)
            eds.append(L.score_pos(c, np.array(B.kcenter_seq(c.DIIsub, 1)[0]))["ed"])
        eds = np.array(eds)
        if eds.size == 0:
            print(f"{name:12s} {mode:15s} không sinh được cascade 10–20%", flush=True)
            continue
        rows.append(dict(graph=name, p="" if p is None else round(p, 4), stop=mode, frac_inf="0,10–0,20",
                         n=len(eds), ed_mean=float(eds.mean()), pct_ed0=float((eds == 0).mean() * 100),
                         pct_ed_le1=float((eds <= 1).mean() * 100)))
        print(f"{name:12s} {mode:15s} p={rows[-1]['p']!s:7s} | {len(eds)} cascade | ED TB {eds.mean():.2f} | "
              f"đoán trúng {rows[-1]['pct_ed0']:.0f}% | ED<=1 {rows[-1]['pct_ed_le1']:.0f}%", flush=True)
    return rows


if __name__ == "__main__":
    tree = nx.random_labeled_tree(500, seed=9999)          # cùng cây với H0/sanity_checks.py
    lfr = nx.convert_node_labels_to_integers(
        nx.read_edgelist(os.path.join("data", "lfr_mu0.3_0_edges.txt"), nodetype=int), ordering="sorted")
    print("=== Phần A: cùng p, chỉ đổi thời điểm dừng (kích thước nhiễm thay đổi theo) ===")
    rows_a = run("cay_n500", tree, [0.7, 0.9], 7001) + run("lfr_mu0.3_0", lfr, [0.09, 0.15, 0.3], 7002)
    print("=== Phần B: cùng kích thước nhiễm 10–20%, mỗi kiểu lan truyền tự hiệu chỉnh p ===")
    rows_b = run_same_size("cay_n500", tree, 7003, 12) + run_same_size("lfr_mu0.3_0", lfr, 7004, 4)   # cây: 12 bước như H0b
    os.makedirs("results", exist_ok=True)
    pd.DataFrame(rows_a).to_csv(os.path.join("results", "identifiability_v2_same_p.csv"), index=False)
    pd.DataFrame(rows_b).to_csv(os.path.join("results", "identifiability_v2_same_size.csv"), index=False)
    print("Đã lưu results/identifiability_v2_same_p.csv và results/identifiability_v2_same_size.csv")
