"""P6-F — BƯỚC HIỆU CHỈNH TỈ LỆ NHIỄM f (chạy TRƯỚC khi khóa giao thức). Review 07/11 Mục 7.1, 7.5 bước 2.

Nguyên tắc (QĐ15): bước này CHỈ dùng các bộ định vị KHÔNG dùng cộng đồng và hai mốc sàn, trên seed riêng
(CALIB_SEED). Không có phân hoạch, không CommJordan/CommLPSI → không nhìn trước hiệu ứng cần kiểm.

Việc script làm:
  1. Sinh/đọc 8 đồ thị P6-F, lưu vào data/ kèm SHA-256 (đồ thị này sẽ dùng lại nguyên vẹn cho P6-F):
       LFR n=10.000, bậc TB 6, bậc max 100, cộng đồng 50–500, μ ∈ {0,1; 0,3}, 3 đồ thị mỗi μ (LCC);
       Power Grid (Watts & Strogatz 1998; lấy từ data GraphSL); ca-GrQc (Leskovec 2007; tải SNAP, LCC).
  2. V1: cây ngẫu nhiên n=2.000, nguồn đặt ngẫu nhiên, k=1 → ED Jordan phải ≤ 50% sàn ngẫu nhiên.
  3. Với mỗi (đồ thị, mô hình quan sát ∈ {si_t, ic_T}, f ∈ {1%, 2%, 5%}, k ∈ {3, 5}):
       sinh N_CASC cascade, chấm ED của: rand (sàn), deg (sàn), jordan, lpsi (+ lpsi_peak chỉ để tham khảo).
  4. Tính V3 = ED_rand − min(ED_jordan, ED_lpsi) tại k=3; chọn f cho mỗi đồ thị theo QUY TẮC CHỌN f bên dưới.
  5. Ghi results/calib_raw.csv, results/V3_table.csv, results/f_chon.json, HIEU_CHINH_F.md.

QUY TẮC CHỌN f (đề xuất, ghi vào giao thức): với mỗi đồ thị, f* = argmax_f min(V3_si_t, V3_ic_T) tại k=3;
hòa → f nhỏ hơn. Đồ thị "đạt V3" khi min(V3_si_t, V3_ic_T) tại f* ≥ 1,0 hop; trượt thì loại khỏi P6-F.

  python hieu_chinh_f.py --smoke       # rất nhỏ, kiểm code
  python hieu_chinh_f.py --workers 4   # chạy thật
"""
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import pickle
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import networkx as nx
import scipy.sparse as sp
from scipy.optimize import linear_sum_assignment
from scipy.sparse.csgraph import shortest_path, connected_components

# ------------------------------------------------------------------ tham số
GRAPH_SEED = 8080          # seed sinh đồ thị — đồ thị này DÙNG LẠI cho P6-F
CALIB_SEED = 7070          # seed cascade của bước hiệu chỉnh — P6-F chính thức phải dùng seed KHÁC
LFR = dict(n=10_000, tau1=3, tau2=1.5, average_degree=6, max_degree=100, min_community=50, max_community=500)
LFR_MUS, LFR_PER_MU, LFR_TRIES = [0.1, 0.3], 3, 50
FS = [0.01, 0.02, 0.05]
WIN = (0.8, 1.2)           # tập nhiễm được nhận khi |I|/n ∈ [0,8f; 1,2f]
KS = [3, 5]
N_CASC = 60
SI_BETA = 0.3
T_GRID = [4, 6, 8, 12, 16, 24, 32]
P_GRID = np.unique(np.concatenate([np.geomspace(0.02, 0.6, 28), np.linspace(0.6, 1.0, 9)]))
N_PCAL, ACC_MIN = 40, 0.30  # ic_T: T = T nhỏ nhất có p đạt tỉ lệ nhận ≥ ACC_MIN; p = argmax tỉ lệ nhận
LPSI_ALPHA, LPSI_ITERS = 0.5, 60
N_RAND_DRAWS = 20          # sàn ngẫu nhiên: trung bình 20 lần rút cho mỗi cascade
V3_MIN = 1.0
SNAP_GRQC = "https://snap.stanford.edu/data/ca-GrQc.txt.gz"
GRQC_MIRROR = "https://raw.githubusercontent.com/suanrong/SDNE/master/GraphData/ca-Grqc.txt"
POWER_GRID_PKL = os.path.join("..", "..", "1_huong_cong_dong", "2_baseline_GraphSL", "data", "power_grid")

HERE = os.path.dirname(os.path.abspath(__file__))


def log(msg, root):
    os.makedirs(os.path.join(root, "logs"), exist_ok=True)
    line = f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(os.path.join(root, "logs", "hieu_chinh_f.log"), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def sub_seed(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ------------------------------------------------------------------ đồ thị
def lcc_csr(G):
    G = G.copy(); G.remove_edges_from(nx.selfloop_edges(G))
    G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
    nodes = sorted(G.nodes())
    return G, nodes


def build_graphs(data_dir, root):
    """Sinh hoặc đọc lại đồ thị. Lưu edges (txt) + truth (npy, chỉ LFR). Trả về manifest."""
    os.makedirs(data_dir, exist_ok=True)
    man_path = os.path.join(data_dir, "manifest.json")
    man = json.load(open(man_path, encoding="utf-8")) if os.path.exists(man_path) else {}
    for mu in LFR_MUS:
        for i in range(LFR_PER_MU):
            gid = f"lfr10k_mu{mu}_{i}"
            if gid in man:
                continue
            for att in range(LFR_TRIES):
                s = sub_seed(GRAPH_SEED, "lfr", mu, i, att)
                try:
                    G = nx.LFR_benchmark_graph(LFR["n"], LFR["tau1"], LFR["tau2"], mu, seed=s,
                                               **{k: v for k, v in LFR.items() if k not in ("n", "tau1", "tau2")})
                    break
                except nx.ExceededMaxIterations:
                    log(f"  {gid}: seed {s} không hội tụ, thử seed kế (ghi DEVIATIONS.md nếu xảy ra ở P6-F)", root)
            else:
                raise RuntimeError(f"{gid} không hội tụ")
            comm = {v: min(G.nodes[v]["community"]) for v in G}
            G, nodes = lcc_csr(G)
            idx = {v: j for j, v in enumerate(nodes)}
            keys = {}
            truth = np.array([keys.setdefault(comm[v], len(keys)) for v in nodes])
            save_graph(data_dir, gid, G, idx, truth)
            man[gid] = dict(kind="lfr", mu=mu, seed=s, attempt=att)
            log(f"  {gid}: n={len(nodes)} m={G.number_of_edges()} cộng đồng thật={len(keys)}", root)
    if "power_grid" not in man and os.path.exists(POWER_GRID_PKL):
        A = pickle.load(open(POWER_GRID_PKL, "rb"))["adj_mat"]
        G, nodes = lcc_csr(nx.from_scipy_sparse_array(A))
        save_graph(data_dir, "power_grid", G, {v: j for j, v in enumerate(nodes)}, None)
        man["power_grid"] = dict(kind="real", source="GraphSL data/power_grid (Watts & Strogatz 1998)")
        log(f"  power_grid: n={len(nodes)} m={G.number_of_edges()}", root)
    if "ca_grqc" not in man:
        # Thứ tự nguồn: (1) tệp cục bộ data/ca-GrQc.txt (tải tay từ SNAP), (2) SNAP, (3) bản sao GitHub.
        # Bản sao (3) đã đánh lại số node 0..5241; kiểm bằng thống kê SNAP công bố: 5.242 node, 14.496 cạnh, LCC 4.158 node.
        txt = src = None
        local = os.path.join(data_dir, "ca-GrQc.txt")
        if os.path.exists(local):
            txt, src = open(local, encoding="utf-8").read(), "tệp cục bộ data/ca-GrQc.txt"
        else:
            for url, gz in ((SNAP_GRQC, True), (GRQC_MIRROR, False)):
                try:
                    with urllib.request.urlopen(url, timeout=60) as r:
                        raw = r.read()
                    txt, src = (gzip.decompress(raw) if gz else raw).decode(), url
                    break
                except Exception as e:
                    log(f"  ca_grqc: không tải được {url} ({e.__class__.__name__})", root)
        if txt is None:
            log("  ca_grqc: KHÔNG có nguồn nào; đặt tệp SNAP vào data/ca-GrQc.txt rồi chạy lại", root)
        else:
            G = nx.Graph(); first = True
            for line in io.StringIO(txt):
                q = line.split()
                if line.startswith("#") or len(q) != 2:
                    continue
                if first and src == GRQC_MIRROR:      # dòng đầu của bản sao là "số_node số_cạnh"
                    first = False
                    continue
                first = False
                G.add_edge(int(q[0]), int(q[1]))
            n_all, m_all = G.number_of_nodes(), G.number_of_edges()
            G, nodes = lcc_csr(G)
            ok = (n_all == 5242 and len(nodes) == 4158)
            save_graph(data_dir, "ca_grqc", G, {v: j for j, v in enumerate(nodes)}, None)
            man["ca_grqc"] = dict(kind="real", source=src + " (LCC)", n_all=n_all, m_all_incl_selfloops=m_all,
                                  khop_thong_ke_SNAP=ok)
            log(f"  ca_grqc: nguồn {src}; toàn bộ n={n_all} m={m_all}; LCC n={len(nodes)} m={G.number_of_edges()}; "
                f"khớp thống kê SNAP: {ok}", root)
    for gid in man:
        man[gid]["sha256_edges"] = sha256(os.path.join(data_dir, f"{gid}_edges.txt"))
    json.dump(man, open(man_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return man


def save_graph(data_dir, gid, G, idx, truth):
    with open(os.path.join(data_dir, f"{gid}_edges.txt"), "w") as fh:
        for a, b in G.edges():
            fh.write(f"{idx[a]} {idx[b]}\n")
    if truth is not None:
        np.save(os.path.join(data_dir, f"{gid}_truth.npy"), truth)


def load_csr(data_dir, gid):
    e = np.loadtxt(os.path.join(data_dir, f"{gid}_edges.txt"), dtype=np.int64, ndmin=2)
    n = int(e.max()) + 1
    A = sp.coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n))
    A = ((A + A.T) > 0).astype(np.float64).tocsr()
    return A


# ------------------------------------------------------------------ mô hình quan sát
def ic_steps(A, src, p, rng, T):
    """IC rời rạc: mỗi node vừa nhiễm thử lây MỘT lần cho từng hàng xóm chưa nhiễm (xs p); dừng sau T bước."""
    ip, ix = A.indptr, A.indices
    act = np.zeros(A.shape[0], bool); act[src] = True; fr = np.asarray(src)
    for _ in range(T):
        nb = np.concatenate([ix[ip[u]:ip[u + 1]] for u in fr]) if len(fr) else np.empty(0, int)
        nb = nb[~act[nb]]
        hit = np.unique(nb[rng.random(nb.size) < p])   # node có ≥1 lần thử thành công
        act[hit] = True; fr = hit
        if not fr.size:
            break
    return np.flatnonzero(act)


def si_until(A, src, rng, target):
    """SI rời rạc: MỌI node đã nhiễm thử lây mỗi bước (xs β); chụp snapshot khi |I| ≥ target."""
    ip, ix = A.indptr, A.indices
    act = np.zeros(A.shape[0], bool); act[src] = True
    while act.sum() < target:
        inf = np.flatnonzero(act)
        nb = np.concatenate([ix[ip[u]:ip[u + 1]] for u in inf])
        nb = nb[~act[nb]]
        act[nb[rng.random(nb.size) < SI_BETA]] = True
    return np.flatnonzero(act)


def calib_ic(A, k, f, seed):
    """Chọn (T, p) cho ic_T: T nhỏ nhất trong T_GRID có p đạt tỉ lệ nhận ≥ ACC_MIN; p = argmax tỉ lệ nhận.
    T nhỏ + p lớn = gần BFS (dễ định vị); T lớn + p nhỏ = ngẫu nhiên hơn. Quy tắc này thiên về T nhỏ."""
    n = A.shape[0]; lo, hi = WIN[0] * f * n, WIN[1] * f * n
    rng = np.random.default_rng(seed); best = (None, None, -1.0)
    for T in T_GRID:
        bT = (None, -1.0)
        for p in P_GRID:
            sz = np.array([ic_steps(A, rng.choice(n, k, replace=False), p, rng, T).size for _ in range(N_PCAL)])
            acc = float(((sz >= lo) & (sz <= hi)).mean())
            if acc > bT[1]:
                bT = (float(p), acc)
            if np.median(sz) > 2 * hi:
                break
        if bT[1] > best[2]:
            best = (T, bT[0], bT[1])
        if bT[1] >= ACC_MIN:
            return T, bT[0], bT[1]
    return best


def make_cascades(A, obs, k, f, n_casc, seed, T=None, p=None):
    n = A.shape[0]; lo, hi = WIN[0] * f * n, WIN[1] * f * n
    rng = np.random.default_rng(seed); out = []; tries = 0
    while len(out) < n_casc:
        tries += 1
        if tries > 500 * n_casc:
            raise RuntimeError(f"{obs} k={k} f={f}: không đủ cascade trong cửa sổ")
        src = rng.choice(n, k, replace=False)
        inf = ic_steps(A, src, p, rng, T) if obs == "ic_T" else si_until(A, src, rng, int(rng.uniform(lo, hi)))
        if lo <= inf.size <= hi:
            out.append((src, inf))
    return out, tries


# ------------------------------------------------------------------ bộ định vị (biết trước k), không dùng cộng đồng
def kcenter_seq(M, m):
    """Gonzalez tham lam trên ma trận khoảng cách M (∞ = khác mảnh). Bản đã sửa (H0c_fix/BUGFIX.md):
    tâm đầu = Jordan center của mảnh lớn nhất; còn mảnh chưa có tâm → Jordan center của mảnh lớn nhất chưa có tâm;
    mọi mảnh đã có tâm → điểm xa tập tâm nhất."""
    _, comp = connected_components(sp.csr_matrix(np.isfinite(M)), directed=False)
    order = np.argsort(-np.bincount(comp), kind="stable")

    def jordan(c):
        idx = np.flatnonzero(comp == c)
        return int(idx[np.argmin(M[np.ix_(idx, idx)].max(axis=1))])

    centers = [jordan(order[0])]; covered = {int(order[0])}; dmin = M[centers[0]].copy()
    while len(centers) < min(m, M.shape[0]):
        if not np.isfinite(dmin).all():
            c = next(int(c) for c in order if int(c) not in covered); covered.add(c); nxt = jordan(c)
        else:
            nxt = int(np.argmax(dmin))
        centers.append(nxt); dmin = np.minimum(dmin, M[nxt])
    return centers


class LPSIIter:
    """LPSI (Wang et al. 2017) dạng lặp: g ← αSg + Y, S = D^-1/2 A D^-1/2. Không nghịch đảo ma trận (n = 10.000)."""

    def __init__(self, A):
        d = np.asarray(A.sum(1)).ravel()
        Dm = sp.diags(1 / np.sqrt(d))
        self.S = (Dm @ A @ Dm).tocsr(); self.A = A

    def scores(self, inf):
        Y = -np.ones(self.A.shape[0]); Y[inf] = 1.0; g = Y.copy()
        for _ in range(LPSI_ITERS):
            g = LPSI_ALPHA * (self.S @ g) + Y
        return g

    def peaks_topk(self, g, k):
        """Tham khảo: chỉ lấy đỉnh cục bộ (g > mọi hàng xóm), xếp theo g; thiếu thì bù top-k thường."""
        ip, ix = self.A.indptr, self.A.indices
        nbmax = np.maximum.reduceat(g[ix], ip[:-1])
        pk = np.flatnonzero(g > nbmax); pk = pk[np.argsort(-g[pk])][:k]
        if pk.size < k:
            rest = [v for v in np.argsort(-g) if v not in set(pk)][:k - pk.size]
            pk = np.concatenate([pk, rest])
        return pk.astype(int)


def ed(dist_src, pred):
    """ED: ghép một-một (Hungarian) nguồn thật ↔ dự đoán, trung bình khoảng cách hop trên G."""
    M = dist_src[:, pred]
    r, c = linear_sum_assignment(M)
    return float(M[r, c].mean())


# ------------------------------------------------------------------ một việc = (đồ thị, quan sát, f, k)
def run_task(gid, obs, f, k, data_dir, raw_dir, n_casc, seed):
    out = os.path.join(raw_dir, f"{gid}__{obs}__f{f}__k{k}.csv")
    if os.path.exists(out):
        return out
    A = load_csr(data_dir, gid); n = A.shape[0]
    deg = np.asarray(A.sum(1)).ravel(); lp = LPSIIter(A)
    T = p = acc = None
    if obs == "ic_T":
        T, p, acc = calib_ic(A, k, f, sub_seed(seed, gid, "cal", f, k))
    casc, tries = make_cascades(A, obs, k, f, n_casc, sub_seed(seed, gid, obs, f, k, "casc"), T, p)
    rng = np.random.default_rng(sub_seed(seed, gid, obs, f, k, "rand"))
    rows = []
    for ci, (src, inf) in enumerate(casc):
        Dsrc = shortest_path(A, method="D", unweighted=True, indices=src)       # k × n, chỉ để chấm
        AI = A[inf][:, inf]
        DII = shortest_path(AI, method="D", unweighted=True)                    # |I|×|I|, trên đồ thị con nhiễm
        r = dict(graph=gid, obs=obs, f=f, k=k, cascade=ci, n=n, n_inf=inf.size,
                 n_comp=int(connected_components(AI, directed=False)[0]),
                 T="" if T is None else T, p="" if p is None else round(p, 5),
                 acc="" if acc is None else round(acc, 3), tries=tries)
        r["ed_rand"] = float(np.mean([ed(Dsrc, rng.choice(inf, k, replace=False)) for _ in range(N_RAND_DRAWS)]))
        r["ed_deg"] = ed(Dsrc, inf[np.argsort(-deg[inf], kind="stable")[:k]])
        r["ed_jordan"] = ed(Dsrc, inf[kcenter_seq(DII, k)])
        g = lp.scores(inf)
        r["ed_lpsi"] = ed(Dsrc, np.argsort(-g)[:k])
        r["ed_lpsi_peak"] = ed(Dsrc, lp.peaks_topk(g, k))
        rows.append(r)
    with open(out + ".tmp", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    os.replace(out + ".tmp", out)
    return out


# ------------------------------------------------------------------ V1
def v1_tree(seed, n_casc):
    """Cây ngẫu nhiên n = 2.000, nguồn ngẫu nhiên, k = 1, tập nhiễm 5% (80–120 node).
    Đạt khi ED_jordan ≤ 0,5 · ED_rand cho cả hai mô hình quan sát."""
    G = nx.random_labeled_tree(2000, seed=sub_seed(seed, "tree"))
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(2000), dtype=float))
    res = {}
    for obs in ("si_t", "ic_T"):
        T = p = None
        if obs == "ic_T":
            T, p, _ = calib_ic(A, 1, 0.05, sub_seed(seed, "tree_cal"))
        casc, _ = make_cascades(A, obs, 1, 0.05, n_casc, sub_seed(seed, "tree", obs), T, p)
        rng = np.random.default_rng(sub_seed(seed, "tree_rand", obs)); ej, er = [], []
        for src, inf in casc:
            Dsrc = shortest_path(A, method="D", unweighted=True, indices=src)
            DII = shortest_path(A[inf][:, inf], method="D", unweighted=True)
            ej.append(ed(Dsrc, inf[kcenter_seq(DII, 1)]))
            er.append(np.mean([ed(Dsrc, rng.choice(inf, 1)) for _ in range(N_RAND_DRAWS)]))
        res[obs] = dict(T=T, p=p, ed_jordan=float(np.mean(ej)), ed_rand=float(np.mean(er)),
                        pct_hit=float(np.mean(np.array(ej) == 0) * 100),
                        pass_=bool(np.mean(ej) <= 0.5 * np.mean(er)))
    return res


# ------------------------------------------------------------------ tổng hợp
def analyze(root, raw_dir, v1, man):
    import glob
    import pandas as pd
    df = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(os.path.join(raw_dir, "*.csv")))], ignore_index=True)
    meth = ["ed_rand", "ed_deg", "ed_jordan", "ed_lpsi", "ed_lpsi_peak"]
    g = df.groupby(["graph", "obs", "f", "k"])
    S = g[meth].mean()
    S["se_rand"] = g["ed_rand"].sem()
    S["n_inf"] = g["n_inf"].mean(); S["n_comp"] = g["n_comp"].mean()
    S["n"] = g["n"].first(); S["T"] = g["T"].first(); S["p"] = g["p"].first(); S["acc"] = g["acc"].first()
    S["V3"] = S["ed_rand"] - S[["ed_jordan", "ed_lpsi"]].min(axis=1)
    S = S.reset_index()
    os.makedirs(os.path.join(root, "results"), exist_ok=True)
    S.to_csv(os.path.join(root, "results", "V3_table.csv"), index=False)
    # Phân tầng theo mức tách của đồ thị con nhiễm: dư địa đến từ cascade đã tách sẵn thành ≥ k mảnh
    # (k-center tách được mà không cần cộng đồng) hay từ cascade chồng lấn (1 mảnh) — nơi cộng đồng mới có việc để làm.
    df["tang"] = np.where(df.n_comp >= df.k, "tach_san", np.where(df.n_comp == 1, "chong_lan", "mot_phan"))
    gt = df.groupby(["graph", "obs", "f", "k", "tang"])
    O = gt[meth].mean(); O["n_casc"] = gt.size()
    O["V3"] = O["ed_rand"] - O[["ed_jordan", "ed_lpsi"]].min(axis=1)
    O.reset_index().to_csv(os.path.join(root, "results", "V3_theo_tang.csv"), index=False)
    choice = {}
    for gid, gg in S[S.k == 3].groupby("graph"):
        piv = gg.pivot(index="f", columns="obs", values="V3")
        if piv.shape[1] < 2:
            continue
        mn = piv.min(axis=1)
        fstar = float(mn[mn == mn.max()].index.min())
        choice[gid] = dict(f=fstar, V3_si_t=float(piv.loc[fstar, "si_t"]), V3_ic_T=float(piv.loc[fstar, "ic_T"]),
                           pass_V3=bool(mn.loc[fstar] >= V3_MIN))
    json.dump(dict(time=dt.datetime.now().isoformat(timespec="seconds"), calib_seed=CALIB_SEED, v1=v1, choice=choice),
              open(os.path.join(root, "results", "f_chon.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    write_report(root, S, choice, v1, man)
    return S, choice


def write_report(root, S, choice, v1, man):
    f2 = lambda x: f"{x:.2f}"
    ok = lambda b: "✓" if b else "✗"
    o = ["# P6-F — Hiệu chỉnh tỉ lệ nhiễm f (trước khi khóa giao thức)\n",
         f"Sinh tự động {dt.datetime.now():%d/%m/%Y %H:%M} từ `results/raw/`. Seed cascade hiệu chỉnh {CALIB_SEED} "
         f"(P6-F chính thức phải dùng seed khác). Seed đồ thị {GRAPH_SEED}. {N_CASC} cascade mỗi ô. "
         "Chỉ dùng bộ định vị không cộng đồng và hai mốc sàn (Review 07/11 Mục 7.1, 7.5).\n",
         "## V1 — cây ngẫu nhiên n = 2.000, nguồn ngẫu nhiên, k = 1, nhiễm 5%\n",
         "| Quan sát | (T, p) | ED Jordan | ED sàn ngẫu nhiên | Trúng nguồn % | Đạt (Jordan ≤ 50% sàn) |", "|---|---|---|---|---|---|"]
    for obs, r in v1.items():
        tp = "—" if r["T"] is None else f"({r['T']}, {r['p']:.3f})"
        o.append(f"| {obs} | {tp} | {f2(r['ed_jordan'])} | {f2(r['ed_rand'])} | {r['pct_hit']:.0f} | {ok(r['pass_'])} |")
    o += ["\n## f được chọn (k = 3)\n",
          f"Quy tắc: f* = argmax_f min(V3_si_t, V3_ic_T); hòa → f nhỏ hơn. Đạt khi min ≥ {V3_MIN} hop.\n",
          "| Đồ thị | n | f* | V3 si_t | V3 ic_T | Đạt V3 |", "|---|---|---|---|---|---|"]
    for gid, c in sorted(choice.items()):
        n = int(S[S.graph == gid].iloc[0]["n"])
        o.append(f"| {gid} | {n} | {c['f']:.0%} | {f2(c['V3_si_t'])} | {f2(c['V3_ic_T'])} | {ok(c['pass_V3'])} |")
    missing = [g for g in man if g not in choice]
    if missing:
        o.append(f"\n> Chưa có kết quả: {', '.join(missing)}.")
    if "ca_grqc" not in man:
        o.append("\n> ca-GrQc chưa có (không tải được). Đặt tệp SNAP vào data/ca-GrQc.txt rồi chạy lại; các ô đã có được giữ nguyên.")
    o += ["\n## Bảng đầy đủ (ED trung bình, hop)\n",
          "| Đồ thị | Quan sát | f | k | (T, p) | \\|I\\| TB | Số mảnh TB | Sàn ngẫu nhiên (SE) | Sàn bậc | Jordan | LPSI | LPSI-đỉnh* | V3 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in S.sort_values(["graph", "obs", "k", "f"]).iterrows():
        tp = "—" if r.obs == "si_t" else f"({int(r['T'])}, {float(r['p']):.3f}; nhận {float(r['acc']):.2f})"
        o.append(f"| {r.graph} | {r.obs} | {r.f:.0%} | {r.k} | {tp} | {r.n_inf:.0f} | {r.n_comp:.1f} | "
                 f"{f2(r.ed_rand)} ({r.se_rand:.2f}) | {f2(r.ed_deg)} | {f2(r.ed_jordan)} | {f2(r.ed_lpsi)} | "
                 f"{f2(r.ed_lpsi_peak)} | **{f2(r.V3)}** |")
    o += ["\n\\* LPSI-đỉnh (chỉ lấy đỉnh cục bộ của g) chỉ để tham khảo, KHÔNG dùng trong V3. "
          "Nếu nó tốt hơn rõ LPSI top-k, cần quyết định trong giao thức dùng biến thể nào làm đối chứng mạnh nhất.",
          "\n## Ghi chú thiết kế",
          f"- Cửa sổ nhận cascade: |I|/n ∈ [{WIN[0]}f; {WIN[1]}f]. si_t: β = {SI_BETA}, chụp khi |I| ≥ mục tiêu ~ U(cửa sổ).",
          f"- ic_T: T = giá trị nhỏ nhất trong {T_GRID} có p đạt tỉ lệ nhận ≥ {ACC_MIN}; p = argmax tỉ lệ nhận ({N_PCAL} lần thử/p).",
          f"- LPSI dạng lặp, α = {LPSI_ALPHA}, {LPSI_ITERS} vòng; biết trước k → top-k của g.",
          f"- Sàn ngẫu nhiên: k node nhiễm rút ngẫu nhiên, trung bình {N_RAND_DRAWS} lần mỗi cascade. Sàn bậc: k node nhiễm bậc cao nhất.",
          "- ED: ghép Hungarian nguồn thật ↔ dự đoán, khoảng cách hop trên toàn đồ thị G."]
    open(os.path.join(root, "HIEU_CHINH_F.md"), "w", encoding="utf-8").write("\n".join(o) + "\n")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    os.chdir(HERE)
    root = "smoke" if a.smoke else "."
    data_dir = "data"; raw_dir = os.path.join(root, "results", "raw"); os.makedirs(raw_dir, exist_ok=True)
    seed = CALIB_SEED + (1 if a.smoke else 0)
    n_casc = 4 if a.smoke else N_CASC
    log(f"Hiệu chỉnh f bắt đầu | smoke={a.smoke} | workers={a.workers} | seed={seed} | networkx {nx.__version__}", root)
    log(f"  SHA-256 hieu_chinh_f.py: {sha256(os.path.abspath(__file__))}", root)
    import scipy, sys
    log(f"  Python {sys.version.split()[0]} | numpy {np.__version__} | scipy {scipy.__version__} | networkx {nx.__version__}", root)
    man = build_graphs(data_dir, root)
    graphs = sorted(man) if not a.smoke else sorted(man)[:2]
    log("V1: cây ngẫu nhiên...", root)
    v1 = v1_tree(seed, 20 if a.smoke else 100)
    for obs, r in v1.items():
        log(f"  V1 {obs}: ED Jordan {r['ed_jordan']:.2f} / sàn {r['ed_rand']:.2f} → {'ĐẠT' if r['pass_'] else 'KHÔNG ĐẠT'}", root)
    tasks = [(g, o, f, k) for g in graphs for o in ("si_t", "ic_T") for f in FS for k in KS]
    # việc nặng trước: f lớn, ic_T (có hiệu chỉnh p)
    tasks.sort(key=lambda t: (-t[2], t[1] != "ic_T"))
    log(f"=== {len(tasks)} việc, {n_casc} cascade mỗi việc ===", root)
    t0 = time.time(); done = 0
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(run_task, *t, data_dir, raw_dir, n_casc, seed): t for t in tasks}
        for fu in as_completed(futs):
            try:
                fu.result()
            except Exception as e:
                log(f"  LỖI {futs[fu]}: {e}", root)
            done += 1
            el = (time.time() - t0) / 60
            log(f"--- {done}/{len(tasks)} {futs[fu]} ({el:.1f} phút; còn ~{el / done * (len(tasks) - done):.0f} phút)", root)
    S, choice = analyze(root, raw_dir, v1, man)
    for gid, c in sorted(choice.items()):
        log(f"  {gid}: f*={c['f']:.0%} V3 si_t={c['V3_si_t']:.2f} ic_T={c['V3_ic_T']:.2f} → {'ĐẠT' if c['pass_V3'] else 'TRƯỢT'}", root)
    log("=== XONG ===", root)


if __name__ == "__main__":
    main()
