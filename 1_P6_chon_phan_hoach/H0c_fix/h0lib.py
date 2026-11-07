"""Thư viện H0: đồ thị, phân hoạch, cascade IC, bộ định vị, chấm điểm.
Tham chiếu: H0_PROTOCOL.md; Review 30/10 Mục 7.1 (B2) và 7.3.
"""
import gzip
import io
import json
import hashlib
import urllib.request

import numpy as np
import networkx as nx
import scipy.sparse as sp
from scipy.sparse.csgraph import shortest_path
from scipy.optimize import linear_sum_assignment

import config as C


# ---------------------------------------------------------------- tiện ích
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sub_seed(*parts):
    """Seed con tất định từ các thành phần (đồ thị, k, cascade...)."""
    s = "|".join(str(p) for p in parts).encode()
    return int(hashlib.sha256(s).hexdigest()[:8], 16)


def to_labels(communities, n):
    lab = np.full(n, -1, dtype=np.int64)
    for c, nodes in enumerate(communities):
        for v in nodes:
            lab[v] = c
    assert (lab >= 0).all()
    return lab


# ---------------------------------------------------------------- đồ thị (Mục 4)
def _lcc_relabel(G, truth_attr):
    G = G.copy()
    G.remove_edges_from(nx.selfloop_edges(G))
    lcc = max(nx.connected_components(G), key=len)
    G = G.subgraph(lcc).copy()
    mapping = {v: i for i, v in enumerate(sorted(G.nodes()))}
    truth = {mapping[v]: truth_attr[v] for v in G.nodes()}
    G = nx.relabel_nodes(G, mapping)
    n = G.number_of_nodes()
    # nhãn cộng đồng thật -> số nguyên liên tiếp
    keys = {}
    t = np.array([keys.setdefault(truth[i], len(keys)) for i in range(n)], dtype=np.int64)
    return G, t


def make_lfr(mu, idx, master_seed, log=print):
    for attempt in range(C.LFR_MAX_TRIES):
        seed = sub_seed(master_seed, "lfr", mu, idx, attempt)
        try:
            G = nx.LFR_benchmark_graph(C.LFR_N, mu=mu, seed=seed, **C.LFR_PARAMS)
        except nx.ExceededMaxIterations:
            log(f"  LFR mu={mu} idx={idx}: seed {seed} không hội tụ, thử lại")
            continue
        comm = {v: min(G.nodes[v]["community"]) for v in G.nodes()}
        G, truth = _lcc_relabel(G, comm)
        return G, truth, {"seed": seed, "attempt": attempt}
    raise RuntimeError(f"LFR mu={mu} idx={idx} không hội tụ sau {C.LFR_MAX_TRIES} lần")


def load_email_eu(cache_dir):
    def fetch(url):
        with urllib.request.urlopen(url, timeout=60) as r:
            return gzip.decompress(r.read()).decode()
    edges_txt = fetch(C.EMAIL_EDGES_URL)
    labels_txt = fetch(C.EMAIL_LABELS_URL)
    with open(f"{cache_dir}/email-Eu-core.txt", "w") as f:
        f.write(edges_txt)
    with open(f"{cache_dir}/email-Eu-core-department-labels.txt", "w") as f:
        f.write(labels_txt)
    G = nx.Graph()
    for line in io.StringIO(edges_txt):
        a, b = line.split()
        G.add_edge(int(a), int(b))
    dept = {}
    for line in io.StringIO(labels_txt):
        a, b = line.split()
        dept[int(a)] = int(b)
    G.remove_nodes_from([v for v in list(G.nodes()) if v not in dept])
    return _lcc_relabel(G, dept)


def graph_arrays(G):
    n = G.number_of_nodes()
    A = nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=np.float64)
    A = sp.csr_matrix(A)
    return A


# ---------------------------------------------------------------- phân hoạch (Mục 5)
def make_partitions(G, gammas, part_seeds):
    n = G.number_of_nodes()
    parts = []
    for g in gammas:
        for s in part_seeds:
            comms = nx.community.louvain_communities(G, resolution=g, seed=s)
            parts.append({"gamma": g, "seed": s, "labels": to_labels(comms, n)})
    return parts


def random_partitions(default_labels, n_random, seed):
    rng = np.random.default_rng(seed)
    out = []
    for r in range(n_random):
        perm = rng.permutation(len(default_labels))
        out.append({"gamma": -1.0, "seed": r, "labels": default_labels[perm].copy()})
    return out


def nmi(a, b):
    """NMI chuẩn hóa trung bình cộng (giống mặc định sklearn)."""
    _, ai = np.unique(a, return_inverse=True)
    _, bi = np.unique(b, return_inverse=True)
    n = len(a)
    cont = sp.coo_matrix((np.ones(n), (ai, bi))).toarray()
    pij = cont / n
    pi, pj = pij.sum(1), pij.sum(0)
    nz = pij > 0
    mi = (pij[nz] * np.log(pij[nz] / (pi[:, None] * pj[None, :])[nz])).sum()
    hi = -(pi[pi > 0] * np.log(pi[pi > 0])).sum()
    hj = -(pj[pj > 0] * np.log(pj[pj > 0])).sum()
    den = (hi + hj) / 2
    return 0.0 if den == 0 else float(mi / den)


# ---------------------------------------------------------------- cascade IC (Mục 6)
def simulate_ic(A, sources, p, rng):
    indptr, indices = A.indptr, A.indices
    active = np.zeros(A.shape[0], dtype=bool)
    active[sources] = True
    frontier = list(sources)
    while frontier:
        new = []
        for u in frontier:
            nb = indices[indptr[u]:indptr[u + 1]]
            nb = nb[~active[nb]]
            if nb.size:
                hit = nb[rng.random(nb.size) < p]
                if hit.size:
                    active[hit] = True
                    new.extend(hit.tolist())
        frontier = new
    return np.flatnonzero(active)


def calibrate_p(A, k, n_calib, seed, log=print):
    """Chọn p có tỉ lệ cascade rơi vào FRAC_RANGE cao nhất (IC có chuyển pha nên
    không thể nhắm trung vị; cascade ngoài khoảng sẽ bị loại khi sinh)."""
    n = A.shape[0]
    rng = np.random.default_rng(seed)
    lo, hi = C.FRAC_RANGE
    best, best_acc = None, -1.0
    for p in C.P_GRID:
        fr = np.array([simulate_ic(A, rng.choice(n, k, replace=False), p, rng).size / n
                       for _ in range(n_calib)])
        acc = float(((fr >= lo) & (fr <= hi)).mean())
        if acc > best_acc:
            best, best_acc = float(p), acc
        if np.median(fr) > 3 * hi:
            break
    if best_acc == 0:
        raise RuntimeError(f"k={k}: không p nào cho cascade trong {C.FRAC_RANGE}")
    if best_acc < 0.05:
        log(f"  CẢNH BÁO: k={k} tỉ lệ chấp nhận cao nhất chỉ {best_acc:.2f} (p={best:.4f})")
    return best, best_acc


def gen_cascades(A, k, p, n_casc, seed):
    """Sinh cascade IC, chỉ giữ cascade có tỉ lệ nhiễm trong FRAC_RANGE (lấy mẫu loại bỏ)."""
    n = A.shape[0]
    lo, hi = C.FRAC_RANGE
    rng = np.random.default_rng(seed)
    out, tries = [], 0
    while len(out) < n_casc:
        tries += 1
        if tries > C.MAX_REJECT * n_casc:
            raise RuntimeError(f"k={k} p={p}: không đủ cascade trong {C.FRAC_RANGE}")
        src = rng.choice(n, k, replace=False)
        inf = simulate_ic(A, src, p, rng)
        if lo <= inf.size / n <= hi:
            out.append((src, inf))
    return out


# ---------------------------------------------------------------- bộ định vị (Mục 7)
class CascadeCtx:
    """Tính một lần cho mỗi cascade, dùng chung cho mọi phân hoạch.
    - DII: khoảng cách trên toàn đồ thị G giữa các node nhiễm -> chỉ dùng để CHẤM ED.
    - A_I: đồ thị con nhiễm (cảm sinh trên tập nhiễm) -> dùng cho k-center (đúng 30/10 Mục 7.1:
      "bán kính k-center trên đồ thị con nhiễm")."""

    def __init__(self, A, sources, infected):
        self.I = infected
        self.D = shortest_path(A, method="D", unweighted=True, indices=infected)  # |I| x n, trên G
        self.DII = self.D[:, infected]
        self.A_I = A[infected][:, infected].tocsr()
        self.DIIsub = shortest_path(self.A_I, method="D", unweighted=True)       # trên đồ thị con nhiễm
        pos = {v: i for i, v in enumerate(infected)}
        self.src_pos = np.array([pos[s] for s in sources])
        self.k = len(sources)


def kcenter(M, rho):
    """Gonzalez tham lam (xấp xỉ 2) trên MỘT thành phần liên thông.
    Tâm đầu = Jordan center (độ lệch tâm nhỏ nhất); sau đó thêm điểm xa nhất cho tới khi
    bán kính <= rho. Trả về chỉ số tâm trong M."""
    c0 = int(np.argmin(M.max(axis=1)))
    centers = [c0]
    dmin = M[c0].copy()
    while dmin.max() > rho and len(centers) < M.shape[0]:
        c = int(np.argmax(dmin))
        centers.append(c)
        dmin = np.minimum(dmin, M[c])
    return centers


def kcenter_split(M, rho):
    """Đồ thị con nhiễm có thể đứt thành nhiều mảnh (khoảng cách = vô cùng).
    Chạy k-center riêng trên từng mảnh liên thông; mỗi mảnh có ít nhất 1 tâm."""
    from scipy.sparse.csgraph import connected_components
    ncomp, comp = connected_components(sp.csr_matrix(np.isfinite(M)), directed=False)
    out = []
    for c in range(ncomp):
        idx = np.flatnonzero(comp == c)
        out.extend(idx[kcenter(M[np.ix_(idx, idx)], rho)].tolist())
    return out


def comm_jordan(ctx, labels, rho):
    """B2 (30/10 Mục 7.1): với mỗi cộng đồng c có tập nhiễm I_c, ước lượng k_c = k nhỏ nhất
    sao cho bán kính k-center trên đồ thị con nhiễm của I_c <= rho; chọn k_c tâm.
    KHÔNG giả định k_c <= 1. Không có bước nào khác."""
    lab_I = labels[ctx.I]
    preds = []
    for c in np.unique(lab_I):
        X = np.flatnonzero(lab_I == c)
        Msub = shortest_path(ctx.A_I[X][:, X], method="D", unweighted=True)
        preds.extend(X[kcenter_split(Msub, rho)].tolist())
    return np.array(preds)             # vị trí trong I


def jordan_global(ctx, rho):
    """Đối chứng không dùng cộng đồng: cùng k-center, trên toàn đồ thị con nhiễm."""
    return np.array(kcenter_split(ctx.DIIsub, rho))


class LPSI:
    def __init__(self, A, alpha):
        n = A.shape[0]
        d = np.asarray(A.sum(1)).ravel()
        Dm = sp.diags(1.0 / np.sqrt(d))
        S = (Dm @ A @ Dm).toarray()
        self.Minv = np.linalg.inv(np.eye(n) - alpha * S)
        self.A = A

    def predict(self, infected):
        n = self.A.shape[0]
        Y = -np.ones(n)
        Y[infected] = 1.0
        g = self.Minv @ Y
        indptr, indices = self.A.indptr, self.A.indices
        nbmax = np.maximum.reduceat(g[indices], indptr[:-1])
        return np.flatnonzero((g > 0) & (g > nbmax))   # chỉ số node toàn đồ thị


# ---------------------------------------------------------------- chấm điểm (Mục 8)
def score(dist_true_pred, k):
    """dist_true_pred: |S| x |Ŝ| khoảng cách (hop)."""
    m = dist_true_pred.shape[1]
    out = {"khat": m, "kerr": abs(m - k)}
    if m == 0:
        out.update(ed=np.nan, **{f"f1_{h}": 0.0 for h in C.F1_HOPS})
        return out
    r, c = linear_sum_assignment(dist_true_pred)
    out["ed"] = float(dist_true_pred[r, c].mean())
    for h in C.F1_HOPS:
        prec = float((dist_true_pred.min(axis=0) <= h).mean())
        rec = float((dist_true_pred.min(axis=1) <= h).mean())
        out[f"f1_{h}"] = 0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec)
    return out


def score_pos(ctx, pred_pos):
    """Dự đoán là vị trí trong I (CommJordan, Jordan)."""
    return score(ctx.DII[ctx.src_pos][:, pred_pos], ctx.k)


def score_nodes(ctx, pred_nodes):
    """Dự đoán là chỉ số node toàn đồ thị (LPSI)."""
    return score(ctx.D[ctx.src_pos][:, pred_nodes], ctx.k)


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
