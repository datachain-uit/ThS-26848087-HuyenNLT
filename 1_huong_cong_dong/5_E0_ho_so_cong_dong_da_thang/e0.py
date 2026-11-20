"""E0 — chạy thử: hồ sơ cộng đồng đa thang của đồ thị con nhiễm và số nguồn k.
Giao thức: E0_PLAN.md (viết trước khi chạy). Seed chạy thử 9191.
Chạy:  python e0.py            (đầy đủ)
       python e0.py --smoke    (kiểm tra nhanh, ghi vào results/smoke)
Cần thêm scikit-learn trong .venv của H0 (pip install scikit-learn)."""
import _venv; _venv.ensure()
import argparse
import csv
import datetime as dt
import hashlib
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import networkx as nx
import scipy.sparse as sp
from scipy.sparse.csgraph import shortest_path, connected_components
from scipy.stats import wilcoxon, spearmanr
try:
    from sklearn.ensemble import RandomForestRegressor
except ImportError:
    raise SystemExit("Thiếu scikit-learn. Cài vào .venv của H0: pip install scikit-learn")

SEED = 9191
GRAPHS = ["lfr_mu0.1_0", "lfr_mu0.3_0", "lfr_mu0.5_0", "email_eu"]
FS = [0.05, 0.15]
KS = [1, 2, 3, 5, 8]
N_TRAIN, N_TEST = 60, 60
GAMMAS = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0]
RHOS = [1, 2, 3, 4, 5, 6]
KMAX = 15
BETA = 0.3
MIN_SIZE = 3
DATA = os.path.join("..", "..", "1_huong_cong_dong", "3_D1_D2_uoc_luong_so_nguon", "data")

F_N = ["comp"] + [f"rho_{r}" for r in RHOS]
F_S1 = ["c_1.0"]
F_P = [f"c_{g}" for g in GAMMAS] + ["q_1.0"]
FEATS = F_N + [f for f in F_P if f not in F_N]


def sub_seed(*parts):
    h = hashlib.sha256("|".join(map(str, parts)).encode()).digest()
    return int.from_bytes(h[:8], "little")


def load_graph(gid):
    G = nx.read_edgelist(os.path.join(DATA, f"{gid}_edges.txt"), nodetype=int)
    n = G.number_of_nodes()
    assert set(G.nodes) == set(range(n)), f"{gid}: node không liên tục 0..n-1"
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=np.float64))
    return G, A


def si_fixed(A, src, rng, target):
    """SI rời rạc beta=BETA; dừng khi số node nhiễm đúng bằng target
    (bước cuối chỉ nhận ngẫu nhiên đủ số node còn thiếu)."""
    ip, ix = A.indptr, A.indices
    act = np.zeros(A.shape[0], bool); act[src] = True
    stall = 0
    while act.sum() < target:
        new = set()
        for u in np.flatnonzero(act):
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[~act[nb]]
            if nb.size:
                new.update(nb[rng.random(nb.size) < BETA].tolist())
        if not new:
            stall += 1
            if stall > 200:
                return None
            continue
        new = np.array(sorted(new))
        need = int(target - act.sum())
        if new.size > need:
            new = rng.choice(new, need, replace=False)
        act[new] = True
    return np.flatnonzero(act)


def kcenter_seq(M, m):
    """Chép từ 1_huong_cong_dong/3_D1_D2_uoc_luong_so_nguon/h0b.py (bản đã sửa 07/11/2026, xem H0c_fix/BUGFIX.md)."""
    fin = np.isfinite(M)
    _, comp = connected_components(sp.csr_matrix(fin), directed=False)
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


def features(G, A, inf):
    A_I = A[inf][:, inf].tocsr()
    ncomp, _ = connected_components(A_I, directed=False)
    DI = shortest_path(A_I, method="D", unweighted=True)
    _, radii = kcenter_seq(DI, KMAX)
    f = {"comp": int(ncomp)}
    for r in RHOS:
        ok = [i + 1 for i, x in enumerate(radii) if x <= r]
        f[f"rho_{r}"] = ok[0] if ok else KMAX
    H = G.subgraph(inf.tolist())
    for g in GAMMAS:
        cs = nx.community.louvain_communities(H, resolution=g, seed=0)
        f[f"c_{g}"] = sum(1 for c in cs if len(c) >= MIN_SIZE)
        if g == 1.0:
            f["q_1.0"] = float(nx.community.modularity(H, cs)) if H.number_of_edges() else 0.0
    return f


def run_cell(gid, frac, n_train, n_test, chunk_dir):
    G, A = load_graph(gid)
    n = A.shape[0]
    target = int(round(frac * n))
    rows = []
    for split, n_casc in (("train", n_train), ("test", n_test)):
        for k in KS:
            # Điểm lưu theo (ô, split, k): chạy lại sẽ bỏ qua phần đã xong. Seed riêng từng phần
            # nên kết quả không phụ thuộc việc chạy một lần hay nhiều lần.
            ck = os.path.join(chunk_dir, f"{gid}_f{frac}_{split}_k{k}_n{n_casc}.csv")
            if os.path.exists(ck):
                with open(ck, newline="", encoding="utf-8") as fh:
                    for r in csv.DictReader(fh):
                        rows.append({c: (v if c in ("graph", "split") else float(v) if c in ("f", "q_1.0") else int(v))
                                     for c, v in r.items()})
                continue
            rng = np.random.default_rng(sub_seed(SEED, gid, frac, split, k))
            part = []
            while len(part) < n_casc:
                src = rng.choice(n, k, replace=False)
                inf = si_fixed(A, src, rng, target)
                if inf is None:
                    continue
                f = features(G, A, inf)
                part.append(dict(graph=gid, f=frac, split=split, k=k, casc=len(part), n_inf=int(inf.size), **f))
            with open(ck + ".tmp", "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(part[0].keys())); w.writeheader(); w.writerows(part)
            os.replace(ck + ".tmp", ck)
            rows += part
    return gid, frac, rows


def mae(pred, y):
    return float(np.abs(pred - y).mean())


def wil(err_a, err_b):
    """p một phía cho giả thuyết |sai số| của a nhỏ hơn của b."""
    try:
        return float(wilcoxon(err_a, err_b, alternative="less").pvalue)
    except ValueError:
        return 1.0


def fit_pred(tr, te, cols):
    X = np.array([[r[c] for c in cols] for r in tr], float)
    y = np.array([r["k"] for r in tr], float)
    Xt = np.array([[r[c] for c in cols] for r in te], float)
    m = RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=1).fit(X, y)
    return np.clip(np.rint(m.predict(Xt)), 1, KMAX)


def analyze(rows):
    out = []
    cells = sorted({(r["graph"], r["f"]) for r in rows})
    for gid, frac in cells:
        tr = [r for r in rows if r["graph"] == gid and r["f"] == frac and r["split"] == "train"]
        te = [r for r in rows if r["graph"] == gid and r["f"] == frac and r["split"] == "test"]
        ytr = np.array([r["k"] for r in tr], float); y = np.array([r["k"] for r in te], float)
        c_best = min(KS, key=lambda c: mae(np.full(len(ytr), c), ytr))
        p_const = np.full(len(y), c_best, float)
        rule = min(F_N, key=lambda c: mae(np.clip([r[c] for r in tr], 1, KMAX), ytr))
        p_rule = np.clip(np.array([r[rule] for r in te], float), 1, KMAX)
        p_s1raw = np.clip(np.array([r["c_1.0"] for r in te], float), 1, KMAX)
        P = {"const": p_const, "N_rule": p_rule, "S1_raw": p_s1raw,
             "N_reg": fit_pred(tr, te, F_N), "S1_reg": fit_pred(tr, te, F_S1),
             "P_reg": fit_pred(tr, te, F_P), "PN_reg": fit_pred(tr, te, FEATS)}
        E = {a: np.abs(p - y) for a, p in P.items()}
        M = {a: float(e.mean()) for a, e in E.items()}
        p_t0 = wil(E["P_reg"], E["const"]); p_qa = wil(E["P_reg"], E["S1_reg"]); p_qb = wil(E["PN_reg"], E["N_reg"])
        res = dict(graph=gid, f=frac, const=c_best, N_rule=rule,
                   **{f"mae_{a}": round(v, 3) for a, v in M.items()},
                   **{f"bias_{a}": round(float((P[a] - y).mean()), 3) for a in ("S1_raw", "N_reg", "P_reg", "PN_reg")},
                   p_T0=p_t0, p_Qa=p_qa, p_Qb=p_qb,
                   T0=bool(M["P_reg"] < M["const"] and p_t0 < 0.01),
                   Qa=bool(M["P_reg"] <= 0.8 * M["S1_reg"] and p_qa < 0.01),
                   Qb=bool(M["PN_reg"] <= 0.8 * M["N_reg"] and p_qb < 0.01))
        for k in KS:
            sel = y == k
            for a in ("N_reg", "P_reg", "PN_reg"):
                res[f"mae_k{k}_{a}"] = round(float(E[a][sel].mean()), 2)
        for c in ("comp", "rho_3", "c_0.1", "c_1.0", "c_4.0", "q_1.0"):
            v = np.array([r[c] for r in te], float)
            res[f"rho_s_{c}"] = round(float(spearmanr(v, y).statistic), 2) if v.std() > 0 else float("nan")
        out.append(res)
    return out


def report(summ, path, smoke, secs):
    n_qb = sum(r["Qb"] for r in summ); n = len(summ)
    if smoke:
        concl = "(chạy kiểm tra nhanh, không kết luận)"
    elif n_qb >= 6:
        concl = "KHẢ QUAN"
    elif n_qb <= 2:
        concl = "KHÔNG KHẢ QUAN"
    else:
        concl = "CHƯA RÕ"
    L = []
    L.append("# E0 — báo cáo chạy thử (sinh tự động từ results/raw.csv)\n")
    L.append(f"{dt.datetime.now():%d/%m/%Y %H:%M}. Seed {SEED}. Giao thức: `E0_PLAN.md`. "
             f"Môi trường: {platform.system()} {platform.machine()}, Python {platform.python_version()}. "
             f"Thời gian chạy {secs/60:.1f} phút.\n")
    L.append("**Đây là chạy thử thăm dò, chưa được GVHD duyệt, không phải số liệu chính thức.**\n")
    L.append(f"## Kết luận theo tiêu chí viết trước: {concl}\n")
    L.append(f"Qb đạt {n_qb}/{n} ô; Qa đạt {sum(r['Qa'] for r in summ)}/{n}; T0 đạt {sum(r['T0'] for r in summ)}/{n}.\n")
    L.append("## MAE trên test\n")
    L.append("| Đồ thị | f | const | N_rule | MAE const | MAE N_rule | MAE S1_raw | MAE S1_reg | MAE N_reg | MAE P_reg | MAE PN_reg | T0 (p) | Qa (p) | Qb (p) |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    mk = lambda b: "✓" if b else "✗"
    for r in summ:
        L.append(f"| {r['graph']} | {r['f']:.0%} | {r['const']} | {r['N_rule']} | {r['mae_const']:.2f} | {r['mae_N_rule']:.2f} | "
                 f"{r['mae_S1_raw']:.2f} | {r['mae_S1_reg']:.2f} | {r['mae_N_reg']:.2f} | {r['mae_P_reg']:.2f} | {r['mae_PN_reg']:.2f} | "
                 f"{mk(r['T0'])} ({r['p_T0']:.3g}) | {mk(r['Qa'])} ({r['p_Qa']:.3g}) | {mk(r['Qb'])} ({r['p_Qb']:.3g}) |")
    L.append("\n## Độ lệch k̂ − k trung bình (test)\n")
    L.append("| Đồ thị | f | S1_raw | N_reg | P_reg | PN_reg |")
    L.append("|---|---|---|---|---|---|")
    for r in summ:
        L.append(f"| {r['graph']} | {r['f']:.0%} | {r['bias_S1_raw']:+.2f} | {r['bias_N_reg']:+.2f} | {r['bias_P_reg']:+.2f} | {r['bias_PN_reg']:+.2f} |")
    L.append("\n## MAE theo k (test): N_reg / P_reg / PN_reg\n")
    L.append("| Đồ thị | f | " + " | ".join(f"k={k}" for k in KS) + " |")
    L.append("|---|---|" + "---|" * len(KS))
    for r in summ:
        L.append(f"| {r['graph']} | {r['f']:.0%} | " + " | ".join(
            f"{r[f'mae_k{k}_N_reg']:.2f} / {r[f'mae_k{k}_P_reg']:.2f} / {r[f'mae_k{k}_PN_reg']:.2f}" for k in KS) + " |")
    L.append("\n## Tương quan hạng Spearman giữa đặc trưng và k (test)\n")
    cs = ("comp", "rho_3", "c_0.1", "c_1.0", "c_4.0", "q_1.0")
    L.append("| Đồ thị | f | " + " | ".join(cs) + " |")
    L.append("|---|---|" + "---|" * len(cs))
    for r in summ:
        L.append(f"| {r['graph']} | {r['f']:.0%} | " + " | ".join(f"{r[f'rho_s_{c}']:.2f}" for c in cs) + " |")
    L.append("\n## Giới hạn\n")
    L.append("- 4 đồ thị n ≈ 1000, chỉ SI, chỉ Louvain, một bộ hồi quy, một seed; huấn luyện và kiểm trên cùng đồ thị.")
    L.append("- Kích thước vùng nhiễm bị ép cố định. Pilot D1 (07/11) trên cùng hướng đã NO-GO; E0 là lần thử thứ hai.")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    return concl


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--smoke", action="store_true"); a = ap.parse_args()
    out = os.path.join("results", "smoke") if a.smoke else "results"
    os.makedirs(out, exist_ok=True); os.makedirs("logs", exist_ok=True)
    logp = os.path.join("logs", "e0_smoke.log" if a.smoke else "e0.log")

    def log(msg):
        line = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        with open(logp, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    graphs = GRAPHS[:1] if a.smoke else GRAPHS
    fs = [0.15] if a.smoke else FS
    ntr, nte = (8, 8) if a.smoke else (N_TRAIN, N_TEST)
    t0 = time.time()
    log(f"Bắt đầu E0 ({'smoke' if a.smoke else 'đầy đủ'}): {len(graphs)} đồ thị x {len(fs)} f x {len(KS)} k x ({ntr}+{nte}) cascade; seed {SEED}; {platform.system()}")
    rows = []
    with ProcessPoolExecutor(max_workers=min(2, os.cpu_count() or 1)) as ex:
        chunk_dir = os.path.join(out, "chunks"); os.makedirs(chunk_dir, exist_ok=True)
        futs = [ex.submit(run_cell, g, f, ntr, nte, chunk_dir) for g in graphs for f in fs]
        for fu in as_completed(futs):
            gid, frac, r = fu.result()
            rows += r
            log(f"Xong ô {gid} f={frac:.0%}: {len(r)} cascade ({time.time()-t0:.0f}s)")
    rows.sort(key=lambda r: (r["graph"], r["f"], r["split"], r["k"], r["casc"]))
    with open(os.path.join(out, "raw.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    summ = analyze(rows)
    with open(os.path.join(out, "summary.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summ[0].keys())); w.writeheader(); w.writerows(summ)
    concl = report(summ, os.path.join(out, "E0_REPORT.md"), a.smoke, time.time() - t0)
    log(f"Kết thúc. Kết luận: {concl}. Báo cáo: {os.path.join(out, 'E0_REPORT.md')}")


if __name__ == "__main__":
    main()
