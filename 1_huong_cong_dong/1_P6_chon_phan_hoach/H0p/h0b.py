"""H0b — thí nghiệm THĂM DÒ (không phải H0 chính thức): tìm thiết lập đo hợp lệ để kiểm tra
"phân hoạch có tạo khác biệt cho định vị nguồn không". Xem H0b_PLAN.md.

Lưới 3 x 3 = 9 ô:
  mô hình quan sát : ic_full (như H0) | ic_T (IC dừng sau T bước) | si_t (SI, chụp khi tập nhiễm đạt kích thước mục tiêu)
  xử lý số nguồn   : rho_ed (như H0)  | rho_f1 (chọn ρ theo F1@1 trên val) | known_k (biết trước tổng k)

  python h0b.py            # chạy toàn bộ + phân tích + viết H0b_REPORT.md
  python h0b.py --smoke    # chạy rất nhỏ để kiểm code
  python h0b.py --workers 8
"""
import _venv; _venv.ensure()
import argparse
import csv
import datetime as dt
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import networkx as nx
import pandas as pd

import config as C
import h0lib as L

SEED = 3030                       # seed mới, khác H0 (2026) và chạy thử (9999)
MUS = [0.1, 0.3, 0.5]
OBS = ["ic_full", "ic_T", "si_t"]
COUNT = ["rho_ed", "rho_f1", "known_k"]
KS = [1, 3, 5]
N_VAL, N_TEST = 30, 50
T_STEPS = 4                       # IC dừng sau 4 bước (định trước)
SI_BETA = 0.3                     # SI: xác suất lây mỗi cạnh mỗi bước
RHOS = [1, 2, 3, 4, 5, 6]
LO, HI = C.FRAC_RANGE
FIELDS = ["cell", "obs", "count", "graph", "mu", "k", "cascade", "method", "part_id", "gamma", "pseed",
          "rho", "ed", "khat", "kerr", "f1_0", "f1_1", "f1_2", "frac_inf"]


def log(msg, path="logs/h0b.log"):
    os.makedirs("logs", exist_ok=True)
    line = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ------------------------------------------------------------ mô hình quan sát
def ic_steps(A, src, p, rng, T):
    ip, ix = A.indptr, A.indices
    act = np.zeros(A.shape[0], bool); act[src] = True; fr = list(src)
    for _ in range(T):
        new = []
        for u in fr:
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[~act[nb]]
            if nb.size:
                h = nb[rng.random(nb.size) < p]
                if h.size:
                    act[h] = True; new += h.tolist()
        fr = new
        if not fr:
            break
    return np.flatnonzero(act)


def si_until(A, src, rng, target):
    """SI rời rạc; dừng (chụp snapshot) ngay khi số node nhiễm >= target."""
    ip, ix = A.indptr, A.indices
    act = np.zeros(A.shape[0], bool); act[src] = True
    while act.sum() < target:
        inf = np.flatnonzero(act)
        new = []
        for u in inf:
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[~act[nb]]
            if nb.size:
                new.extend(nb[rng.random(nb.size) < SI_BETA].tolist())
        if new:
            act[new] = True
    return np.flatnonzero(act)


def calib_p(A, k, seed, sim):
    n = A.shape[0]; rng = np.random.default_rng(seed); best, acc_b = None, -1
    for p in C.P_GRID:
        fr = np.array([sim(rng.choice(n, k, replace=False), p, rng).size / n for _ in range(60)])
        acc = float(((fr >= LO) & (fr <= HI)).mean())
        if acc > acc_b:
            best, acc_b = float(p), acc
        if np.median(fr) > 3 * HI:
            break
    return best, acc_b


def make_cascades(A, obs, k, n_casc, seed, p=None):
    n = A.shape[0]; rng = np.random.default_rng(seed); out = []; tries = 0
    while len(out) < n_casc:
        tries += 1
        if tries > 400 * n_casc:
            raise RuntimeError(f"{obs} k={k}: không đủ cascade 10-20%")
        src = rng.choice(n, k, replace=False)
        if obs == "ic_full":
            inf = L.simulate_ic(A, src, p, rng)
        elif obs == "ic_T":
            inf = ic_steps(A, src, p, rng, T_STEPS)
        else:
            inf = si_until(A, src, rng, int(rng.uniform(LO, HI) * n))
        if LO <= inf.size / n <= HI:
            out.append((src, inf))
    return out


# ------------------------------------------------------------ bộ định vị khi biết trước k
def kcenter_seq(M, m):
    """Greedy Gonzalez trả về tối đa m tâm theo thứ tự và bán kính sau mỗi tâm.

    SỬA LỖI 07/11/2026 (xem BUGFIX.md). Bản cũ thay khoảng cách vô cùng bằng 1e6 rồi lấy
    argmin(max hàng): khi đồ thị con nhiễm đứt thành nhiều mảnh, mọi hàng có max = 1e6 nên tâm
    đầu luôn là phần tử đầu tiên (node có chỉ số nhỏ nhất), không phải Jordan center; tâm kế tiếp
    ở mảnh khác cũng là phần tử đầu tiên của mảnh đó.
    Bản sửa: tâm đầu = Jordan center của mảnh lớn nhất; khi còn mảnh chưa có tâm, tâm kế tiếp =
    Jordan center của mảnh chưa có tâm lớn nhất; khi mọi mảnh đã có tâm, Gonzalez như cũ.
    Với đồ thị con liên thông, kết quả trùng hệt bản cũ."""
    from scipy.sparse.csgraph import connected_components
    import scipy.sparse as _sp
    fin = np.isfinite(M)
    _, comp = connected_components(_sp.csr_matrix(fin), directed=False)
    sizes = np.bincount(comp)
    order = np.argsort(-sizes, kind="stable")

    def jordan(c):
        idx = np.flatnonzero(comp == c)
        return int(idx[np.argmin(M[np.ix_(idx, idx)].max(axis=1))])

    centers = [jordan(order[0])]
    covered = {int(order[0])}
    dmin = M[centers[0]].copy()
    radii = [float(np.where(np.isfinite(dmin), dmin, 1e6).max())]
    while len(centers) < min(m, M.shape[0]):
        if not np.isfinite(dmin).all():
            c = next(int(c) for c in order if int(c) not in covered)
            covered.add(c)
            nxt = jordan(c)
        else:
            nxt = int(np.argmax(dmin))
        centers.append(nxt)
        dmin = np.minimum(dmin, M[nxt])
        radii.append(float(np.where(np.isfinite(dmin), dmin, 1e6).max()))
    return centers, radii


def comm_jordan_known_k(ctx, labels, k):
    """B2 khi biết tổng k: mỗi cộng đồng nhiễm lớn nhất nhận 1 tâm (Jordan center của đồ thị con nhiễm
    của cộng đồng); nếu k > số cộng đồng nhiễm, các tâm còn lại cấp dần cho cộng đồng có bán kính lớn nhất."""
    from scipy.sparse.csgraph import shortest_path
    lab_I = labels[ctx.I]
    comms, sizes = np.unique(lab_I, return_counts=True)
    order = comms[np.argsort(-sizes, kind="stable")]
    seqs = {}
    for c in order[:k]:
        X = np.flatnonzero(lab_I == c)
        Ms = shortest_path(ctx.A_I[X][:, X], method="D", unweighted=True)
        cs, rs = kcenter_seq(Ms, k)
        seqs[c] = (X, cs, rs)
    m = {c: 1 for c in seqs}
    for _ in range(k - len(seqs)):
        cand = [c for c in seqs if m[c] < len(seqs[c][1])]
        if not cand:
            break
        c = max(cand, key=lambda c: seqs[c][2][m[c] - 1])
        m[c] += 1
    return np.array([seqs[c][0][j] for c in seqs for j in seqs[c][1][:m[c]]])


def jordan_known_k(ctx, k):
    cs, _ = kcenter_seq(ctx.DIIsub, k)
    return np.array(cs)


# ------------------------------------------------------------ chạy một (ô, đồ thị)
def run_task(obs, count, gid, mu, data_dir, raw_dir, smoke):
    out = os.path.join(raw_dir, f"{obs}__{count}__{gid}.csv")
    if os.path.exists(out):
        return out, 0.0
    t0 = time.time()
    G = nx.read_edgelist(os.path.join(data_dir, f"{gid}_edges.txt"), nodetype=int)
    G = nx.convert_node_labels_to_integers(G, ordering="sorted")
    A = L.graph_arrays(G)
    P = np.load(os.path.join(data_dir, f"{gid}_parts.npz"))
    labels, gam, pse = P["labels"], P["gamma"], P["pseed"]
    n_louv = int((gam >= 0).sum())
    d = int(np.flatnonzero((gam == 1.0) & (pse == 0))[0])
    lpsi = L.LPSI(A, C.LPSI_ALPHA)
    n_val, n_test = (6, 8) if smoke else (N_VAL, N_TEST)
    rows = []
    for k in KS:
        p = None
        if obs == "ic_full":
            p, _ = calib_p(A, k, L.sub_seed(SEED, gid, k, "cal_full"), lambda s, p, r: L.simulate_ic(A, s, p, r))
        elif obs == "ic_T":
            p, _ = calib_p(A, k, L.sub_seed(SEED, gid, k, "cal_T"), lambda s, p, r: ic_steps(A, s, p, r, T_STEPS))
        # cùng seed cascade cho mọi cách xử lý số nguồn trong cùng mô hình quan sát
        test = make_cascades(A, obs, k, n_test, L.sub_seed(SEED, gid, obs, k, "test"), p)
        rho_cj = rho_j = None
        if count != "known_k":
            val = make_cascades(A, obs, k, n_val, L.sub_seed(SEED, gid, obs, k, "val"), p)
            vctx = [L.CascadeCtx(A, s, i) for s, i in val]
            crit = "ed" if count == "rho_ed" else "f1_1"
            sgn = 1 if crit == "ed" else -1
            def best(fn):
                sc = {r: np.nanmean([fn(c, r)[crit] for c in vctx]) for r in RHOS}
                return min(RHOS, key=lambda r: (sgn * sc[r], r))
            rho_cj = best(lambda c, r: L.score_pos(c, L.comm_jordan(c, labels[d], r)))
            rho_j = best(lambda c, r: L.score_pos(c, L.jordan_global(c, r)))
        for ci, (src, inf) in enumerate(test):
            ctx = L.CascadeCtx(A, src, inf)
            base = dict(cell=f"{obs}|{count}", obs=obs, count=count, graph=gid, mu=mu, k=k, cascade=ci,
                        frac_inf=round(len(inf) / A.shape[0], 4))
            for pi in range(labels.shape[0]):
                pred = (comm_jordan_known_k(ctx, labels[pi], k) if count == "known_k"
                        else L.comm_jordan(ctx, labels[pi], rho_cj))
                rows.append({**base, "method": "commjordan" if pi < n_louv else "random_part", "part_id": pi,
                             "gamma": gam[pi], "pseed": pse[pi], "rho": rho_cj, **L.score_pos(ctx, pred)})
            pj = jordan_known_k(ctx, k) if count == "known_k" else L.jordan_global(ctx, rho_j)
            rows.append({**base, "method": "jordan", "part_id": -1, "rho": rho_j, **L.score_pos(ctx, pj)})
            if count == "known_k":
                Y = -np.ones(A.shape[0]); Y[inf] = 1.0; g = lpsi.Minv @ Y
                pl = np.argsort(-g)[:k]
            else:
                pl = lpsi.predict(inf)
            rows.append({**base, "method": "lpsi", "part_id": -1, **L.score_nodes(ctx, pl)})
    tmp = out + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader()
        for r in rows:
            w.writerow({k_: (f"{v:.6g}" if isinstance(v, float) else v) for k_, v in r.items()})
    os.replace(tmp, out)
    el = time.time() - t0
    log(f"[{obs}|{count}] {gid}: XONG {len(rows)} dòng, {el:.0f}s")
    return out, el


# ------------------------------------------------------------ kiểm tra cây theo từng mô hình quan sát
def tree_check(obs):
    """Kiểm tra hợp lý (30/10 Mục 7.3): cây, 1 nguồn, quan sát đầy đủ -> Jordan center cho ED nhỏ.
    Dùng cây tam phân cân bằng sâu 7 (3280 node), nguồn ở gốc — xấp xỉ cây đều vô hạn, thiết lập mà lý thuyết
    Jordan center / rumor center (Shah & Zaman; Zhu & Ying) được chứng minh; tập nhiễm 100–200 node để tránh biên lá."""
    G = nx.balanced_tree(3, 7)
    A = L.graph_arrays(G)
    src = np.array([0]); lo, hi = 100, 200
    rng = np.random.default_rng(2)

    def sim(p):
        if obs == "ic_full":
            return L.simulate_ic(A, src, p, rng)
        if obs == "ic_T":
            return ic_steps(A, src, p, rng, T_STEPS)
        return si_until(A, src, rng, int(rng.uniform(lo, hi)))
    p_best = None
    if obs != "si_t":
        best = -1
        for p in np.linspace(0.3, 1.0, 29):
            acc = np.mean([lo <= sim(p).size <= hi for _ in range(40)])
            if acc > best:
                best, p_best = acc, p
    casc = []; tries = 0
    while len(casc) < 100 and tries < 20000:
        tries += 1
        I = sim(p_best)
        if lo <= I.size <= hi:
            casc.append(I)
    if not casc:
        return float("nan"), 0.0
    eds = np.array([L.score_pos(c, np.array([L.kcenter(c.DIIsub, np.inf)[0]]))["ed"]
                    for c in (L.CascadeCtx(A, src, I) for I in casc)])
    return float(eds.mean()), float((eds == 0).mean() * 100)


# ------------------------------------------------------------ phân tích + báo cáo
def analyze(raw_dir, tree):
    import glob
    df = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(raw_dir, "*.csv"))], ignore_index=True)
    rows = []
    for (cell, gid, k), g in df[df.method == "commjordan"].groupby(["cell", "graph", "k"]):
        E = g.pivot(index="part_id", columns="cascade", values="ed").sort_index().values
        gm = E.mean(); sst = ((E - gm) ** 2).sum(); ssp = E.shape[1] * ((E.mean(1) - gm) ** 2).sum()
        dmask = g.drop_duplicates("part_id").set_index("part_id")
        d = int(dmask[(dmask.gamma == 1.0) & (dmask.pseed == 0)].index[0])
        a, b = np.arange(0, E.shape[1], 2), np.arange(1, E.shape[1], 2)
        dc = np.mean([E[d, ev].mean() - E[int(np.argmin(E[:, fi].mean(1))), ev].mean() for fi, ev in ((a, b), (b, a))])
        rows.append(dict(cell=cell, graph=gid, k=k, ed_default=E[d].mean(), delta_cf=dc,
                         eta2=ssp / sst if sst > 0 else 0.0))
    R = pd.DataFrame(rows)
    S = []
    for cell, g in df.groupby("cell"):
        obs = cell.split("|")[0]
        cj = g[g.method == "commjordan"]; rp = g[g.method == "random_part"]
        r = R[R.cell == cell]
        v1 = tree[obs][0] <= 1.0
        v2 = rp.ed.mean() > cj.ed.mean()
        v3 = cj.kerr.mean() <= 1.0
        S.append(dict(cell=cell, tree_ed=tree[obs][0], tree_pct0=tree[obs][1], V1_tree=v1,
                      ed_louvain=cj.ed.mean(), ed_random=rp.ed.mean(), V2_random_worse=v2,
                      kerr=cj.kerr.mean(), V3_kerr_le1=v3, valid=v1 and v2 and v3,
                      f1_1=cj.f1_1.mean(), ed_jordan=g[g.method == "jordan"].ed.mean(),
                      ed_lpsi=g[g.method == "lpsi"].ed.mean(),
                      eta2_median=r.eta2.median(), eta2_max=r.eta2.max(), delta_cf_median=r.delta_cf.median(),
                      n_pairs_eta2_ge_020=int((r.eta2 >= 0.20).sum()), n_pairs=len(r)))
    S = pd.DataFrame(S)
    os.makedirs("results/summary", exist_ok=True)
    R.to_csv("results/summary/H0b_by_cell_graph_k.csv", index=False)
    S.to_csv("results/summary/H0b_cells.csv", index=False)
    f = lambda x: f"{x:.2f}"
    L_ = ["# H0b — Báo cáo thăm dò (không phải H0 chính thức)\n",
          f"Sinh tự động {dt.datetime.now():%d/%m/%Y %H:%M} từ CSV thô trong `results/raw/` (máy chạy). Seed {SEED}. "
          f"3 đồ thị LFR (μ ∈ {{0,1; 0,3; 0,5}}), 50 phân hoạch Louvain + 5 ngẫu nhiên, k ∈ {{1, 3, 5}}, {N_TEST} cascade test.\n",
          "**Quy tắc đọc:** chỉ ô **hợp lệ** (V1 cây ED ≤ 1, V2 phân hoạch ngẫu nhiên kém hơn Louvain, V3 |k̂−k| ≤ 1) "
          "mới được xem η². Thiết lập không được chọn theo η².\n",
          "| Ô (quan sát \\| số nguồn) | Cây ED (đoán trúng %) | ED Louvain | ED ngẫu nhiên | \\|k̂−k\\| | Hợp lệ | F1@1 | η² trung vị | η² max | Δ cf trung vị | cặp η² ≥ 0,20 |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, s in S.sort_values("cell").iterrows():
        L_.append(f"| {s.cell} | {f(s.tree_ed)} ({s.tree_pct0:.0f}%) | {f(s.ed_louvain)} | {f(s.ed_random)} | {s.kerr:.1f} | "
                  f"{'✓' if s.valid else '✗'} | {f(s.f1_1)} | {f(s.eta2_median)} | {f(s.eta2_max)} | {f(s.delta_cf_median)} | "
                  f"{s.n_pairs_eta2_ge_020}/{s.n_pairs} |")
    L_ += ["\n## Ghi chú thiết kế",
           f"- ic_T: IC dừng sau T = {T_STEPS} bước (cây: 12 bước), p hiệu chỉnh để tập nhiễm 10–20%.",
           f"- si_t: SI rời rạc, β = {SI_BETA}, chụp snapshot ngay khi tập nhiễm đạt kích thước mục tiêu ~ U(10%, 20%).",
           "- known_k: tổng k biết trước; CommJordan phân bổ k tâm cho các cộng đồng nhiễm lớn nhất, tâm dư cấp cho cộng đồng có bán kính lớn nhất; Jordan: greedy k-center đúng k tâm; LPSI: top-k điểm.",
           "- rho_f1: ngưỡng ρ chọn trên val theo F1@1 (phạt đoán thừa).",
           "- Kiểm tra cây (V1): cây tam phân cân bằng sâu 7, nguồn ở gốc, tập nhiễm 100–200 node (xấp xỉ cây đều vô hạn). "
           "Lưu ý: với nguồn ở gốc, cây đối xứng nên V1 kém nhạy với vấn đề định danh của ic_full; vấn đề này xem ở identifiability_check của H0.",
           "- Mọi ô dùng cùng đồ thị và phân hoạch; trong cùng mô hình quan sát, các ô dùng cùng cascade."]
    open("H0b_REPORT.md", "w", encoding="utf-8").write("\n".join(L_) + "\n")
    log("Đã viết H0b_REPORT.md")
    print(S[["cell", "valid", "eta2_median", "eta2_max", "n_pairs_eta2_ge_020"]].to_string(index=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    root = "smoke" if a.smoke else "."
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root, "data"); raw_dir = os.path.join(root, "results", "raw")
    os.makedirs(data_dir, exist_ok=True); os.makedirs(raw_dir, exist_ok=True)
    log(f"H0b bắt đầu | smoke={a.smoke} | workers={a.workers} | seed={SEED}")
    graphs = []
    for mu in MUS:
        gid = f"lfr_mu{mu}"
        if not os.path.exists(os.path.join(data_dir, f"{gid}_parts.npz")):
            G, truth, meta = L.make_lfr(mu, 0, SEED, log)
            nx.write_edgelist(G, os.path.join(data_dir, f"{gid}_edges.txt"), data=False)
            parts = L.make_partitions(G, C.GAMMAS, C.PART_SEEDS if not a.smoke else [0])
            dl = [q for q in parts if (q["gamma"], q["seed"]) == (1.0, 0)][0]["labels"]
            allp = parts + L.random_partitions(dl, C.N_RANDOM_PARTS, L.sub_seed(SEED, gid, "rand"))
            np.savez(os.path.join(data_dir, f"{gid}_parts.npz"), labels=np.stack([q["labels"] for q in allp]),
                     gamma=np.array([q["gamma"] for q in allp]), pseed=np.array([q["seed"] for q in allp]))
            log(f"  {gid}: n={G.number_of_nodes()} m={G.number_of_edges()}")
        graphs.append((gid, mu))
    log("Kiểm tra cây theo từng mô hình quan sát...")
    tree = {o: tree_check(o) for o in OBS}
    for o, (e, p0) in tree.items():
        log(f"  cây | {o}: ED TB={e:.2f}, đoán trúng {p0:.0f}%")
    json.dump(tree, open(os.path.join(root, "results", "tree_check.json"), "w"), indent=1)
    tasks = [(o, c, g, m) for o in OBS for c in COUNT for g, m in graphs]
    log(f"=== {len(tasks)} việc (9 ô x {len(graphs)} đồ thị) ===")
    t0 = time.time(); done = 0
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(run_task, o, c, g, m, data_dir, raw_dir, a.smoke) for o, c, g, m in tasks]
        for fu in as_completed(futs):
            fu.result(); done += 1
            log(f"--- Tiến độ: {done}/{len(tasks)} ({(time.time()-t0)/60:.1f} phút) ---")
    if a.smoke:
        os.chdir(root)
    analyze(os.path.join("results", "raw"), tree)
    log("=== H0b XONG ===")


if __name__ == "__main__":
    main()
