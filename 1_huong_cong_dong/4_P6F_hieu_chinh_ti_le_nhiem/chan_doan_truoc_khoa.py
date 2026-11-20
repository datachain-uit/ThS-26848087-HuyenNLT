"""P6-F — CHẨN ĐOÁN TRƯỚC KHI KHÓA (bổ sung cho hieu_chinh_f.py). Chỉ bộ định vị KHÔNG cộng đồng + hai mốc sàn,
seed riêng 7171. Không sinh phân hoạch, không chạy phương pháp cộng đồng (QĐ15).

Ba câu hỏi, để GVHD có số liệu khi quyết định (P6F_PROTOCOL.md Mục 9):
  D1  Đề xuất B có khả thi không? Đồ thị LFR thưa hơn (bậc TB 4) hoặc lớn hơn (n = 30.000) có cho dư địa ở tầng
      cascade CHỒNG LẤN (đồ thị con nhiễm 1 mảnh) không? So với LFR gốc của P6-F (n = 10.000, bậc TB 6).
  D2  Vì sao V1 trượt ở si_t? So 3 thiết lập (k = 1, tập nhiễm 80–120 node): cây Prüfer n = 2.000 nguồn ngẫu nhiên
      (đúng V1); cây bậc trong ≥ 3 n = 2.000 nguồn ngẫu nhiên; cây bậc trong ≥ 3 n = 20.000 với nguồn chỉ ở độ sâu ≤ 3
      (xa lá, gần cây vô hạn). Giả thuyết: trượt do hiệu ứng biên khi nguồn rơi vào lá, không do loại cây.
  D3  lpsi_r (LPSI top-k có loại trùng bán kính r) có mạnh hơn Jordan/LPSI không? Chạy trên 8 đồ thị P6-F, f = 1%.

  python chan_doan_truoc_khoa.py        # log: logs/chan_doan.log; kết quả: results/chan_doan/, CHAN_DOAN.md
"""
import csv
import datetime as dt
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import networkx as nx
import scipy.sparse as sp
from scipy.sparse.csgraph import shortest_path, connected_components, dijkstra

import hieu_chinh_f as H

SEED = 7171
N_CASC = 60
RS = [1, 2, 3]
OUT = os.path.join("results", "chan_doan")
LFR_B = {  # tên: (n, bậc TB, bậc max, cộng đồng min, max)
    "goc_n10k_d6": (10_000, 6, 100, 50, 500),
    "thua_n10k_d4": (10_000, 4, 100, 50, 500),
    "lon_n30k_d6": (30_000, 6, 150, 50, 500),
}


def log(msg):
    os.makedirs("logs", exist_ok=True)
    line = f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(os.path.join("logs", "chan_doan.log"), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def lpsi_r(lp, A, g, k, r, inf):
    """Chọn lần lượt node có g cao nhất trong tập nhiễm, bỏ mọi node trong bán kính r hop của node đã chọn."""
    order = inf[np.argsort(-g[inf])]
    picked = []
    blocked = np.zeros(A.shape[0], bool)
    for v in order:
        if blocked[v]:
            continue
        picked.append(int(v))
        if len(picked) == k:
            break
        d = dijkstra(A, unweighted=True, indices=[v], limit=r + 0.5)[0]
        blocked[np.isfinite(d)] = True
    if len(picked) < k:                      # thiếu thì bù theo g
        rest = [int(v) for v in order if v not in picked][:k - len(picked)]
        picked += rest
    return np.array(picked)


def eval_cascades(A, casc, k, rng, with_r=True):
    deg = np.asarray(A.sum(1)).ravel(); lp = H.LPSIIter(A); rows = []
    for ci, (src, inf) in enumerate(casc):
        Dsrc = shortest_path(A, method="D", unweighted=True, indices=src)
        AI = A[inf][:, inf]
        DII = shortest_path(AI, method="D", unweighted=True)
        r = dict(cascade=ci, n_inf=inf.size, n_comp=int(connected_components(AI, directed=False)[0]))
        r["ed_rand"] = float(np.mean([H.ed(Dsrc, rng.choice(inf, k, replace=False)) for _ in range(H.N_RAND_DRAWS)]))
        r["ed_deg"] = H.ed(Dsrc, inf[np.argsort(-deg[inf], kind="stable")[:k]])
        r["ed_jordan"] = H.ed(Dsrc, inf[H.kcenter_seq(DII, k)])
        g = lp.scores(inf)
        r["ed_lpsi"] = H.ed(Dsrc, np.argsort(-g)[:k])
        if with_r:
            for rr in RS:
                r[f"ed_lpsi_r{rr}"] = H.ed(Dsrc, lpsi_r(lp, A, g, k, rr, inf))
        rows.append(r)
    return rows


def write_rows(path, rows, base):
    rows = [{**base, **r} for r in rows]
    with open(path + ".tmp", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    os.replace(path + ".tmp", path)


# ------------------------------------------------------------------ D1
def d1_task(name, mu, obs, f, k):
    out = os.path.join(OUT, f"D1__{name}__mu{mu}__{obs}__f{f}__k{k}.csv")
    if os.path.exists(out):
        return out
    n, d, dmax, cmin, cmax = LFR_B[name]
    for att in range(H.LFR_TRIES):
        s = H.sub_seed(SEED, "lfrB", name, mu, att)
        try:
            G = nx.LFR_benchmark_graph(n, H.LFR["tau1"], H.LFR["tau2"], mu, average_degree=d, max_degree=dmax,
                                       min_community=cmin, max_community=cmax, seed=s)
            break
        except nx.ExceededMaxIterations:
            continue
    G, nodes = H.lcc_csr(G)
    idx = {v: j for j, v in enumerate(nodes)}
    e = np.array([(idx[a], idx[b]) for a, b in G.edges()])
    nn = len(nodes)
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(nn, nn))
    A = ((A + A.T) > 0).astype(np.float64).tocsr()
    T = p = acc = None
    if obs == "ic_T":
        T, p, acc = H.calib_ic(A, k, f, H.sub_seed(SEED, name, mu, "cal", f, k))
    casc, _ = H.make_cascades(A, obs, k, f, N_CASC, H.sub_seed(SEED, name, mu, obs, f, k, "casc"), T, p)
    rows = eval_cascades(A, casc, k, np.random.default_rng(H.sub_seed(SEED, name, mu, obs, f, k, "rand")), with_r=False)
    write_rows(out, rows, dict(family=name, mu=mu, obs=obs, f=f, k=k, n=nn, m=G.number_of_edges(), lfr_seed=s,
                               T="" if T is None else T, p="" if p is None else round(p, 5)))
    return out


# ------------------------------------------------------------------ D2
def tree_min3(n, seed):
    """Cây ngẫu nhiên n node: duyệt BFS, mỗi node trong nhận 2 hoặc 3 con (đều xác suất) → bậc node trong ≥ 3
    (trừ gốc có thể bậc 2)."""
    rng = np.random.default_rng(seed); G = nx.Graph(); G.add_node(0); q = [0]; nxt = 1
    while nxt < n:
        u = q.pop(0)
        for _ in range(int(rng.integers(2, 4))):
            if nxt >= n:
                break
            G.add_edge(u, nxt); q.append(nxt); nxt += 1
    return G


TREES = {  # tên: (loại cây, n, nguồn lấy từ đâu)
    "prufer": ("prufer", 2000, "moi_node"),        # đúng như V1 trong giao thức
    "min3": ("min3", 2000, "moi_node"),            # cây bậc trong ≥ 3, cùng cỡ
    "min3_trong": ("min3", 20000, "do_sau_le_3"),  # cây lớn, nguồn chỉ ở độ sâu ≤ 3 (xa lá) → gần cây vô hạn
}


def cascades_from_pool(A, obs, pool, lo, hi, n_c, seed, T, p):
    """Như H.make_cascades nhưng nguồn rút từ `pool` và cửa sổ kích thước nhiễm tuyệt đối [lo, hi]."""
    rng = np.random.default_rng(seed); out = []; tries = 0
    while len(out) < n_c:
        tries += 1
        if tries > 500 * n_c:
            raise RuntimeError(f"{obs}: không đủ cascade trong [{lo}, {hi}]")
        src = rng.choice(pool, 1, replace=False)
        inf = H.ic_steps(A, src, p, rng, T) if obs == "ic_T" else H.si_until(A, src, rng, int(rng.uniform(lo, hi)))
        if lo <= inf.size <= hi:
            out.append((src, inf))
    return out


def calib_pool(A, pool, lo, hi, seed):
    """Như H.calib_ic (T nhỏ nhất đạt tỉ lệ nhận ≥ ACC_MIN), nguồn rút từ `pool`, cửa sổ tuyệt đối."""
    rng = np.random.default_rng(seed); best = (None, None, -1.0)
    for T in H.T_GRID:
        bT = (None, -1.0)
        for p in H.P_GRID:
            sz = np.array([H.ic_steps(A, rng.choice(pool, 1), p, rng, T).size for _ in range(H.N_PCAL)])
            acc = float(((sz >= lo) & (sz <= hi)).mean())
            if acc > bT[1]:
                bT = (float(p), acc)
            if np.median(sz) > 2 * hi:
                break
        if bT[1] > best[2]:
            best = (T, bT[0], bT[1])
        if bT[1] >= H.ACC_MIN:
            return T, bT[0], bT[1]
    return best


def d2_task(tree, obs):
    out = os.path.join(OUT, f"D2__{tree}__{obs}.csv")
    if os.path.exists(out):
        return out
    kind, n, src_rule = TREES[tree]
    G = (nx.random_labeled_tree(n, seed=H.sub_seed(SEED, "tree", tree)) if kind == "prufer"
         else tree_min3(n, H.sub_seed(SEED, "tree", tree)))
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), dtype=float))
    depth = nx.single_source_shortest_path_length(G, 0)
    pool = np.arange(n) if src_rule == "moi_node" else np.array([v for v in range(n) if depth[v] <= 3])
    lo, hi = 80, 120                                 # = 5% của 2.000 node, cửa sổ 0,8–1,2 như hieu_chinh_f
    T = p = None
    if obs == "ic_T":
        T, p, _ = calib_pool(A, pool, lo, hi, H.sub_seed(SEED, tree, "cal"))
    casc = cascades_from_pool(A, obs, pool, lo, hi, 100, H.sub_seed(SEED, tree, obs), T, p)
    rows = eval_cascades(A, casc, 1, np.random.default_rng(H.sub_seed(SEED, tree, obs, "rand")), with_r=False)
    deg = np.array([d for _, d in G.degree()])
    leaf_src = float(np.mean([deg[s[0]] == 1 for s, _ in casc]))
    write_rows(out, rows, dict(tree=tree, n_tree=n, src_rule=src_rule, obs=obs,
                               frac_leaf=round(float((deg == 1).mean()), 3), frac_src_leaf=round(leaf_src, 3),
                               T="" if T is None else T, p="" if p is None else round(p, 5)))
    return out


# ------------------------------------------------------------------ D3
def d3_task(gid, obs, k):
    out = os.path.join(OUT, f"D3__{gid}__{obs}__k{k}.csv")
    if os.path.exists(out):
        return out
    f = 0.01
    A = H.load_csr("data", gid)
    T = p = None
    if obs == "ic_T":
        T, p, _ = H.calib_ic(A, k, f, H.sub_seed(SEED, gid, "cal", f, k))
    casc, _ = H.make_cascades(A, obs, k, f, N_CASC, H.sub_seed(SEED, gid, obs, f, k, "casc"), T, p)
    rows = eval_cascades(A, casc, k, np.random.default_rng(H.sub_seed(SEED, gid, obs, k, "rand")), with_r=True)
    write_rows(out, rows, dict(graph=gid, obs=obs, f=f, k=k, T="" if T is None else T, p="" if p is None else round(p, 5)))
    return out


# ------------------------------------------------------------------ tổng hợp
def tang(df):
    return np.where(df.n_comp >= df.k, "tach_san", np.where(df.n_comp == 1, "chong_lan", "mot_phan"))


def report():
    import glob
    import pandas as pd
    f2 = lambda x: "—" if pd.isna(x) else f"{x:.2f}"
    o = ["# P6-F — Chẩn đoán trước khi khóa (bổ sung cho HIEU_CHINH_F.md)\n",
         f"Sinh tự động {dt.datetime.now():%d/%m/%Y %H:%M} từ `{OUT}/`. Seed {SEED}. Chỉ bộ định vị không cộng đồng "
         "và hai mốc sàn. V3 = ED_sàn ngẫu nhiên − min(ED_Jordan, ED_LPSI).\n"]
    # D1
    d1 = pd.concat([pd.read_csv(x) for x in glob.glob(os.path.join(OUT, "D1__*.csv"))], ignore_index=True)
    d1["tang"] = tang(d1)
    o += ["## D1 — Đề xuất B: đồ thị thưa hơn / lớn hơn có cho dư địa ở tầng chồng lấn không? (k = 3)\n",
          "Mỗi họ 1 đồ thị mỗi μ (seed riêng, không phải đồ thị P6-F). Ô: V3 (số cascade).\n",
          "| Họ đồ thị | n | μ | Quan sát | f | V3 chung | V3 tách sẵn | V3 một phần | V3 chồng lấn |", "|---|---|---|---|---|---|---|---|---|"]
    for (fam, mu, obs, f), g in d1[d1.k == 3].groupby(["family", "mu", "obs", "f"]):
        def v3(x):
            if x.empty:
                return "—"
            m = x[["ed_rand", "ed_jordan", "ed_lpsi"]].mean()
            return f"{m.ed_rand - min(m.ed_jordan, m.ed_lpsi):.2f} ({len(x)})"
        o.append(f"| {fam} | {int(g.n.iloc[0])} | {mu} | {obs} | {f:.0%} | {v3(g)} | {v3(g[g.tang == 'tach_san'])} | "
                 f"{v3(g[g.tang == 'mot_phan'])} | {v3(g[g.tang == 'chong_lan'])} |")
    # D2
    d2 = pd.concat([pd.read_csv(x) for x in glob.glob(os.path.join(OUT, "D2__*.csv"))], ignore_index=True)
    o += ["\n## D2 — V1: vì sao si_t trượt? (k = 1, tập nhiễm 80–120 node, 100 cascade)\n",
          "| Cây | n | Nguồn đặt ở | Tỉ lệ lá | Tỉ lệ nguồn là lá | Quan sát | ED Jordan | ED sàn ngẫu nhiên | Jordan / sàn | Đạt (≤ 50%) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for (tr, obs), g in d2.groupby(["tree", "obs"]):
        j, r = g.ed_jordan.mean(), g.ed_rand.mean()
        o.append(f"| {tr} | {g.n_tree.iloc[0]} | {g.src_rule.iloc[0]} | {g.frac_leaf.iloc[0]:.2f} | {g.frac_src_leaf.iloc[0]:.2f} | "
                 f"{obs} | {f2(j)} | {f2(r)} | {j / r:.0%} | {'✓' if j <= 0.5 * r else '✗'} |")
    # D3
    d3 = pd.concat([pd.read_csv(x) for x in glob.glob(os.path.join(OUT, "D3__*.csv"))], ignore_index=True)
    d3["tang"] = tang(d3)
    cols = ["ed_rand", "ed_deg", "ed_jordan", "ed_lpsi"] + [f"ed_lpsi_r{r}" for r in RS]
    o += ["\n## D3 — lpsi_r có phải đối chứng không cộng đồng mạnh nhất không? (8 đồ thị P6-F, f = 1%)\n",
          "ED trung bình (hop), thấp hơn là tốt hơn. Cột cuối: bộ tốt nhất trong {Jordan, LPSI, lpsi_r1..3}.\n",
          "| Đồ thị | Quan sát | k | Sàn ngẫu nhiên | Sàn bậc | Jordan | LPSI | lpsi_r1 | lpsi_r2 | lpsi_r3 | Tốt nhất |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for (gid, obs, k), g in d3.groupby(["graph", "obs", "k"]):
        m = g[cols].mean()
        best = m[["ed_jordan", "ed_lpsi"] + [f"ed_lpsi_r{r}" for r in RS]].idxmin().replace("ed_", "")
        o.append(f"| {gid} | {obs} | {k} | " + " | ".join(f2(m[c]) for c in cols) + f" | {best} |")
    o += ["\nTheo tầng (gộp 8 đồ thị, k = 3): ED trung bình.\n",
          "| Quan sát | Tầng | Số cascade | Sàn ngẫu nhiên | Jordan | LPSI | lpsi_r1 | lpsi_r2 | lpsi_r3 |", "|---|---|---|---|---|---|---|---|---|"]
    for (obs, t), g in d3[d3.k == 3].groupby(["obs", "tang"]):
        m = g[cols].mean()
        o.append(f"| {obs} | {t} | {len(g)} | {f2(m.ed_rand)} | {f2(m.ed_jordan)} | {f2(m.ed_lpsi)} | "
                 + " | ".join(f2(m[f'ed_lpsi_r{r}']) for r in RS) + " |")
    open("CHAN_DOAN.md", "w", encoding="utf-8").write("\n".join(o) + "\n")
    log("Đã viết CHAN_DOAN.md")


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(OUT, exist_ok=True)
    import scipy, sys
    log(f"Chẩn đoán bắt đầu | seed {SEED} | Python {sys.version.split()[0]} | numpy {np.__version__} | "
        f"scipy {scipy.__version__} | networkx {nx.__version__}")
    log(f"  SHA-256 chan_doan_truoc_khoa.py: {H.sha256(os.path.abspath(__file__))}")
    man = json.load(open(os.path.join("data", "manifest.json"), encoding="utf-8"))
    tasks = [("D2", t, o) for t in TREES for o in ("si_t", "ic_T")]
    tasks += [("D3", g, o, k) for g in sorted(man) for o in ("si_t", "ic_T") for k in (3, 5)]
    tasks += [("D1", fam, mu, o, f, 3) for fam in LFR_B for mu in (0.1, 0.3) for o in ("si_t", "ic_T") for f in (0.01, 0.02)]
    fn = dict(D1=d1_task, D2=d2_task, D3=d3_task)
    log(f"=== {len(tasks)} việc ===")
    t0 = time.time(); done = 0
    with ProcessPoolExecutor(max_workers=max(1, (os.cpu_count() or 2) - 1)) as ex:
        futs = {ex.submit(fn[t[0]], *t[1:]): t for t in tasks}
        for fu in as_completed(futs):
            try:
                fu.result()
            except Exception as e:
                log(f"  LỖI {futs[fu]}: {e.__class__.__name__}: {e}")
            done += 1
            el = (time.time() - t0) / 60
            log(f"--- {done}/{len(tasks)} {futs[fu]} ({el:.1f} phút)")
    report()
    log("=== XONG ===")


if __name__ == "__main__":
    main()
