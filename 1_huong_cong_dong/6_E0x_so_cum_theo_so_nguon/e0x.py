"""E0x — E0c (số cụm của vùng nhiễm có phụ thuộc k không) và E0a (đặc trưng hình học ở vùng nhiễm lớn).
Giao thức: E0X_PLAN.md (viết và commit trước khi chạy). Seed gốc 20261117.
Chạy:  python e0x.py                           (chạy đêm, mặc định hạn 06:30; bấm Run trong VS Code cũng được)
       python e0x.py --smoke                   (kiểm tra nhanh, ghi vào results_smoke/)
       python e0x.py --analyze-only            (chỉ dựng lại báo cáo từ các chunk đã có)
Chạy lại lệnh cũ sau khi bị ngắt: các phần đã xong được giữ và bỏ qua."""
import _venv; _venv.ensure()
import argparse
import csv
import datetime as dt
import glob
import hashlib
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED

import numpy as np
import networkx as nx
from scipy.sparse.csgraph import shortest_path, connected_components
from scipy.stats import wilcoxon, t as tdist

HERE = os.path.dirname(os.path.abspath(__file__))
# append (không insert(0)): tiến trình con trên Windows thừa hưởng sys.path; insert(0) làm nó import nhầm _venv.py của E0
sys.path.append(os.path.join(HERE, "..", "..", "1_huong_cong_dong", "5_E0_ho_so_cong_dong_da_thang"))
import e0  # dùng lại nguyên hàm của E0: load_graph, si_fixed, kcenter_seq, tham số SI và Louvain
from sklearn.ensemble import RandomForestRegressor

SEED0 = 20261117
GRAPHS = e0.GRAPHS
FS = [0.02, 0.05, 0.10, 0.15, 0.25, 0.40]
KS = e0.KS
GAMMAS, RHOS, KMAX, MIN_SIZE = e0.GAMMAS, e0.RHOS, e0.KMAX, e0.MIN_SIZE
N_TR, N_TE, N_BTW, N_BFS = 60, 60, 30, 60
N_SEEDS, MIN_SEEDS = 30, 10
F_N = e0.F_N
F_C = [f"c_{g}" for g in GAMMAS] + ["q_1.0"]
F_G = ["diam", "rad", "dq25", "dq50", "dq75", "dq90", "bnd", "degG_mean", "degG_max", "degI_mean", "leaf", "ecc_min"]
F_PN = F_N + F_C
F_U = F_PN + F_G
SLOPE_MAX, EQ_MARGIN, ALPHA = 0.25, 1.0, 0.01
HA_RATIO, HA_FS = 0.8, (0.15, 0.25, 0.40)
B_BOOT = 2000


def louvain_feats(G, inf):
    H = G.subgraph(inf.tolist())
    f = {}
    for g in GAMMAS:
        cs = nx.community.louvain_communities(H, resolution=g, seed=0)
        f[f"c_{g}"] = sum(1 for c in cs if len(c) >= MIN_SIZE)
        if g == 1.0:
            f["q_1.0"] = float(nx.community.modularity(H, cs)) if H.number_of_edges() else 0.0
    return f


def feat_c(G, A, inf):
    """Chỉ số thành phần liên thông và hồ sơ Louvain (cho btw và bfs)."""
    A_I = A[inf][:, inf].tocsr()
    ncomp, _ = connected_components(A_I, directed=False)
    return {"comp": int(ncomp), **louvain_feats(G, inf)}


def feat_full(G, A, inf):
    """Đặc trưng của E0 (cùng cách tính) cộng đặc trưng hình học."""
    A_I = A[inf][:, inf].tocsr()
    ncomp, _ = connected_components(A_I, directed=False)
    DI = shortest_path(A_I, method="D", unweighted=True)
    _, radii = e0.kcenter_seq(DI, KMAX)
    f = {"comp": int(ncomp)}
    for r in RHOS:
        ok = [i + 1 for i, x in enumerate(radii) if x <= r]
        f[f"rho_{r}"] = ok[0] if ok else KMAX
    f.update(louvain_feats(G, inf))
    m = len(inf)
    ecc = np.where(np.isfinite(DI), DI, -1).max(axis=1)
    dv = DI[np.triu_indices(m, 1)]
    dv = dv[np.isfinite(dv)]
    q = np.percentile(dv, [25, 50, 75, 90]) if dv.size else np.zeros(4)
    degG = np.asarray(A[inf].sum(axis=1)).ravel()
    degI = np.asarray(A_I.sum(axis=1)).ravel()
    ip, ix = A_I.indptr, A_I.indices
    emin = sum(1 for i in range(m) if ip[i] == ip[i + 1] or ecc[i] < ecc[ix[ip[i]:ip[i + 1]]].min())
    f.update(diam=float(ecc.max()), rad=float(ecc.min()), dq25=float(q[0]), dq50=float(q[1]), dq75=float(q[2]),
             dq90=float(q[3]), bnd=float(degG.sum() - degI.sum()), degG_mean=float(degG.mean()),
             degG_max=float(degG.max()), degI_mean=float(degI.mean()), leaf=float((degI == 1).mean()), ecc_min=emin)
    return f


def src_dist(A, src):
    if len(src) < 2:
        return float("nan")
    D = shortest_path(A, method="D", unweighted=True, indices=np.asarray(src))[:, src]
    v = D[np.triu_indices(len(src), 1)]
    return float(v.mean()) if np.isfinite(v).all() else float("nan")


def bfs_ball(A, rng, target):
    n = A.shape[0]
    d = shortest_path(A, method="D", unweighted=True, indices=[int(rng.integers(n))])[0]
    if np.isfinite(d).sum() < target:
        return None
    lv = np.unique(d[np.isfinite(d)])
    take = []
    for L in lv:
        layer = np.flatnonzero(d == L)
        need = target - len(take)
        if layer.size >= need:
            take += rng.choice(layer, need, replace=False).tolist()
            break
        take += layer.tolist()
    return np.array(sorted(take))


def betweenness(gid, G, out):
    p = os.path.join(out, f"btw_{gid}.npy")
    if not os.path.exists(p):
        b = nx.betweenness_centrality(G)
        np.save(p, np.array([b[i] for i in range(G.number_of_nodes())]))
    return np.load(p)


def fit_pred(tr, te, cols):
    X = np.array([[r[c] for c in cols] for r in tr], float)
    y = np.array([r["k"] for r in tr], float)
    Xt = np.array([[r[c] for c in cols] for r in te], float)
    m = RandomForestRegressor(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=1).fit(X, y)
    return np.clip(np.rint(m.predict(Xt)), 1, KMAX)


def run_task(si, gid, frac, ns, out):
    """Một (seed, đồ thị, f): sinh cascade rand/btw/bfs, fit bộ ước lượng trên train của seed này.
    Smoke dùng chỉ số seed từ 900 để không trùng dòng ngẫu nhiên với lần chạy chính."""
    ck = os.path.join(out, "chunks", f"s{si:02d}_{gid}_f{frac}.csv")
    if os.path.exists(ck):
        return si, gid, frac, 0.0, True
    t0 = time.time()
    n_tr, n_te, n_btw, n_bfs = ns
    G, A = e0.load_graph(gid)
    n = A.shape[0]
    target = int(round(frac * n))
    btw = np.load(os.path.join(out, f"btw_{gid}.npy"))
    rows = []
    for place, split, n_c in (("rand", "train", n_tr), ("rand", "test", n_te), ("btw", "test", n_btw)):
        for k in KS:
            rng = np.random.default_rng(e0.sub_seed(SEED0, si, gid, frac, place, split, k))
            src_btw = np.argsort(-btw, kind="stable")[:k]
            c = 0
            while c < n_c:
                src = rng.choice(n, k, replace=False) if place == "rand" else src_btw
                inf = e0.si_fixed(A, src, rng, target)
                if inf is None:
                    if place == "btw":
                        break
                    continue
                f = feat_full(G, A, inf) if place == "rand" else feat_c(G, A, inf)
                rows.append(dict(seed=si, graph=gid, f=frac, place=place, split=split, k=k, casc=c,
                                 dsrc=src_dist(A, src), **f))
                c += 1
    rng = np.random.default_rng(e0.sub_seed(SEED0, si, gid, frac, "bfs"))
    c = 0
    while c < n_bfs:
        inf = bfs_ball(A, rng, target)
        if inf is None:
            continue
        rows.append(dict(seed=si, graph=gid, f=frac, place="bfs", split="test", k=0, casc=c, dsrc=float("nan"),
                         **feat_c(G, A, inf)))
        c += 1
    tr = [r for r in rows if r["place"] == "rand" and r["split"] == "train"]
    te = [r for r in rows if r["place"] == "rand" and r["split"] == "test"]
    ytr = np.array([r["k"] for r in tr], float)
    cbest = min(KS, key=lambda v: float(np.abs(ytr - v).mean()))
    P = {"const": np.full(len(te), cbest, float), "N": fit_pred(tr, te, F_N),
         "PN": fit_pred(tr, te, F_PN), "U": fit_pred(tr, te, F_U)}
    for i, r in enumerate(te):
        for a, p in P.items():
            r[f"pred_{a}"] = float(p[i])
    cols = ["seed", "graph", "f", "place", "split", "k", "casc", "dsrc"] + F_U + [f"pred_{a}" for a in P]
    os.makedirs(os.path.dirname(ck), exist_ok=True)
    with open(ck + ".tmp", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, restval=""); w.writeheader(); w.writerows(rows)
    os.replace(ck + ".tmp", ck)
    return si, gid, frac, time.time() - t0, False


# ---------------------------------------------------------------- phân tích
def load_rows(out):
    rows = []
    for p in sorted(glob.glob(os.path.join(out, "chunks", "s*_f*.csv"))):
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                d = {}
                for c, v in r.items():
                    if c in ("graph", "place", "split"):
                        d[c] = v
                    elif c in ("seed", "k", "casc"):
                        d[c] = int(v)
                    else:
                        d[c] = float(v) if v != "" else float("nan")
                rows.append(d)
    return rows


def complete_seeds(rows):
    have = {}
    for r in rows:
        have.setdefault(r["seed"], set()).add((r["graph"], r["f"]))
    return sorted(s for s, c in have.items() if len(c) == len(GRAPHS) * len(FS))


def slope(k, c):
    k = np.asarray(k, float); c = np.asarray(c, float)
    vk = ((k - k.mean()) ** 2).sum()
    return float(((k - k.mean()) * (c - c.mean())).sum() / vk) if vk > 0 else float("nan")


def slope_ci(seed, k, c, rng):
    """Bootstrap theo cụm seed: tổng đủ thống kê từng seed, trộn bằng trọng số đa thức."""
    us = np.unique(seed)
    S = np.array([[np.sum(seed == s), k[seed == s].sum(), c[seed == s].sum(),
                   (k[seed == s] ** 2).sum(), (k[seed == s] * c[seed == s]).sum()] for s in us])
    if len(us) < 2:
        return float("nan"), float("nan")
    W = rng.multinomial(len(us), np.full(len(us), 1 / len(us)), size=B_BOOT)
    n, sk, sc, skk, skc = (W @ S).T
    b = (skc - sk * sc / n) / (skk - sk ** 2 / n)
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def tost(a, b, margin):
    a = np.asarray(a, float); b = np.asarray(b, float)
    d = a.mean() - b.mean()
    va, vb = a.var(ddof=1) / a.size, b.var(ddof=1) / b.size
    se = np.sqrt(va + vb)
    if se == 0:
        return d, (0.0 if abs(d) < margin else 1.0)
    df = (va + vb) ** 2 / (va ** 2 / (a.size - 1) + vb ** 2 / (b.size - 1))
    p_lo = 1 - tdist.cdf((d + margin) / se, df)
    p_hi = tdist.cdf((d - margin) / se, df)
    return float(d), float(max(p_lo, p_hi))


def skill_ci(seed, e_m, e_c, rng):
    us = np.unique(seed)
    if len(us) < 2:
        return float("nan"), float("nan")
    S = np.array([[e_m[seed == s].sum(), e_c[seed == s].sum()] for s in us])
    W = rng.multinomial(len(us), np.full(len(us), 1 / len(us)), size=B_BOOT)
    t = W @ S
    sk = 1 - t[:, 0] / t[:, 1]
    return float(np.percentile(sk, 2.5)), float(np.percentile(sk, 97.5))


def analyze(rows, seeds):
    rng = np.random.default_rng(SEED0)
    rows = [r for r in rows if r["seed"] in set(seeds)]
    n_cells = len(GRAPHS) * len(FS)
    alpha_c = ALPHA / n_cells
    C, A_ = [], []
    for gid in GRAPHS:
        for frac in FS:
            R = [r for r in rows if r["graph"] == gid and r["f"] == frac]
            rd = [r for r in R if r["place"] == "rand"]
            k = np.array([r["k"] for r in rd], float)
            c = np.array([r["c_1.0"] for r in rd], float)
            sd = np.array([r["seed"] for r in rd])
            b = slope(k, c); lo, hi = slope_ci(sd, k, c, rng)
            d81, p_eq = tost(c[k == 8], c[k == 1], EQ_MARGIN)
            bt = [r for r in R if r["place"] == "btw"]
            bf = [r for r in R if r["place"] == "bfs"]
            C.append(dict(graph=gid, f=frac, slope=b, lo=lo, hi=hi, Hc1=bool(hi < SLOPE_MAX),
                          d81=d81, p_eq=p_eq, Hc2=bool(p_eq < alpha_c),
                          c_k1=float(c[k == 1].mean()), c_k8=float(c[k == 8].mean()),
                          slope_btw=slope([r["k"] for r in bt], [r["c_1.0"] for r in bt]) if bt else float("nan"),
                          c_bfs=float(np.mean([r["c_1.0"] for r in bf])) if bf else float("nan"),
                          slope_comp=slope(k, [r["comp"] for r in rd]),
                          **{f"slope_c{g}": slope(k, [r[f"c_{g}"] for r in rd]) for g in GAMMAS}))
            te = [r for r in rd if r["split"] == "test"]
            y = np.array([r["k"] for r in te], float)
            st = np.array([r["seed"] for r in te])
            E = {a: np.abs(np.array([r[f"pred_{a}"] for r in te]) - y) for a in ("const", "N", "PN", "U")}
            M = {a: float(e.mean()) for a, e in E.items()}
            try:
                p_u = float(wilcoxon(E["U"], E["N"], alternative="less").pvalue)
            except ValueError:
                p_u = 1.0
            skN = skill_ci(st, E["N"], E["const"], rng); skU = skill_ci(st, E["U"], E["const"], rng)
            ds = np.array([r["dsrc"] for r in te]); m2 = (y >= 2) & np.isfinite(ds)
            terc = {}
            if m2.sum() >= 30:
                cut = np.percentile(ds[m2], [100 / 3, 200 / 3])
                for j, (a, bnd) in enumerate(((-np.inf, cut[0]), (cut[0], cut[1]), (cut[1], np.inf))):
                    s = m2 & (ds > a) & (ds <= bnd)
                    terc[j] = (float(E["N"][s].mean()) if s.any() else float("nan"),
                               float(E["U"][s].mean()) if s.any() else float("nan"))
            A_.append(dict(graph=gid, f=frac, **{f"mae_{a}": v for a, v in M.items()},
                           skill_N=1 - M["N"] / M["const"], skill_U=1 - M["U"] / M["const"],
                           skN_lo=skN[0], skN_hi=skN[1], skU_lo=skU[0], skU_hi=skU[1], p_U=p_u,
                           Ha2=bool(frac in HA_FS and M["U"] <= HA_RATIO * M["N"] and p_u < ALPHA),
                           terc=terc))
    return C, A_


def verdict_c(C):
    h1 = sum(x["Hc1"] for x in C); h2 = sum(x["Hc2"] for x in C); n = len(C)
    if h1 >= 20 / 24 * n and h2 >= 20 / 24 * n:
        v = "XÁC NHẬN"
    elif h1 <= 9 / 24 * n and h2 <= 9 / 24 * n:
        v = "BÁC"
    else:
        v = "CHƯA RÕ"
    return v, h1, h2


def report(C, A_, seeds, path, smoke, secs):
    vc, h1, h2 = verdict_c(C)
    ha = [x for x in A_ if x["f"] in HA_FS]
    nha = sum(x["Ha2"] for x in ha)
    va = "ĐẠT" if nha >= 0.75 * len(ha) else "TRƯỢT"
    L = [f"# E0x — báo cáo {'SMOKE (không dùng)' if smoke else ''} (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. Seed gốc {SEED0}. Số seed hoàn tất: {len(seeds)} "
         f"(mục tiêu {N_SEEDS}, tối thiểu {MIN_SEEDS}). Môi trường: {platform.system()} {platform.machine()}, "
         f"Python {platform.python_version()}. Thời gian tính (tổng các phần mới): {secs / 60:.1f} phút. Giao thức: `E0X_PLAN.md`.\n"]
    if len(seeds) < MIN_SEEDS:
        L.append(f"**THIẾU SEED ({len(seeds)} < {MIN_SEEDS}): kết luận dưới đây không có hiệu lực.**\n")
    L.append(f"## Kết luận theo tiêu chí viết trước\n\n- **E0c: {vc}** — Hc1 đạt {h1}/{len(C)} ô; Hc2 đạt {h2}/{len(C)} ô.\n"
             f"- **E0a (Ha2): {va}** — {nha}/{len(ha)} ô f ∈ {{15, 25, 40%}}.\n")
    L.append("## E0c: số cụm Louvain γ = 1 theo k (nguồn ngẫu nhiên)\n")
    L.append("| Đồ thị | f | độ dốc [95% CI] | Hc1 | c(k=8) − c(k=1) | p TOST | Hc2 | c k=1 | c k=8 | c bfs | độ dốc btw | độ dốc comp |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for x in C:
        L.append(f"| {x['graph']} | {x['f']:.0%} | {x['slope']:.2f} [{x['lo']:.2f}, {x['hi']:.2f}] | {'✓' if x['Hc1'] else '✗'} | "
                 f"{x['d81']:+.2f} | {x['p_eq']:.2g} | {'✓' if x['Hc2'] else '✗'} | {x['c_k1']:.2f} | {x['c_k8']:.2f} | "
                 f"{x['c_bfs']:.2f} | {x['slope_btw']:.2f} | {x['slope_comp']:.2f} |")
    L.append("\n## E0c: độ dốc của c theo k ở từng resolution (mô tả)\n")
    L.append("| Đồ thị | f | " + " | ".join(f"γ={g}" for g in GAMMAS) + " |")
    L.append("|---|---|" + "---|" * len(GAMMAS))
    for x in C:
        L.append(f"| {x['graph']} | {x['f']:.0%} | " + " | ".join(f"{x[f'slope_c{g}']:.2f}" for g in GAMMAS) + " |")
    L.append("\n## E0a: MAE và skill trên test (gộp seed)\n")
    L.append("| Đồ thị | f | MAE const | MAE N | MAE PN | MAE U | skill N [CI] | skill U [CI] | p (U<N) | Ha2 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for x in A_:
        L.append(f"| {x['graph']} | {x['f']:.0%} | {x['mae_const']:.2f} | {x['mae_N']:.2f} | {x['mae_PN']:.2f} | {x['mae_U']:.2f} | "
                 f"{x['skill_N']:.2f} [{x['skN_lo']:.2f}, {x['skN_hi']:.2f}] | {x['skill_U']:.2f} [{x['skU_lo']:.2f}, {x['skU_hi']:.2f}] | "
                 f"{x['p_U']:.2g} | {('✓' if x['Ha2'] else '✗') if x['f'] in HA_FS else '—'} |")
    L.append("\n## E0a: MAE theo tam phân vị khoảng cách giữa các nguồn (k ≥ 2), N / U\n")
    L.append("| Đồ thị | f | gần | giữa | xa |")
    L.append("|---|---|---|---|---|")
    for x in A_:
        t = x["terc"]
        L.append(f"| {x['graph']} | {x['f']:.0%} | " + " | ".join(
            f"{t[j][0]:.2f} / {t[j][1]:.2f}" if j in t else "—" for j in range(3)) + " |")
    L.append("\n## Giới hạn\n\n- Một bản đồ thị mỗi mức μ, n ≈ 1000; chỉ SI; kích thước vùng nhiễm ép cố định; huấn luyện và kiểm trên cùng đồ thị.\n"
             "- `U_reg` không phải cận trên lý thuyết. Tính mới chưa xác minh trên Scholar/Scopus.\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    for name, data in (("summary_E0c.csv", C), ("summary_E0a.csv", A_)):
        keys = [k for k in data[0] if k != "terc"]
        with open(os.path.join(os.path.dirname(path), name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(data)
    return vc, va


def parse_deadline(s):
    if not s:
        return None
    h, m = map(int, s.split(":"))
    now = dt.datetime.now()
    d = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return d if d > now else d + dt.timedelta(days=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--analyze-only", action="store_true")
    ap.add_argument("--deadline", default=None, help="HH:MM; ngừng nhận seed mới khi dự báo không kịp")
    ap.add_argument("--seeds", type=int, default=N_SEEDS)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    if a.deadline is None and not a.smoke and not a.analyze_only:
        a.deadline = "06:30"  # mặc định để bấm Run trong VS Code là chạy đúng lần chạy đêm
    out = os.path.join(HERE, "results_smoke" if a.smoke else "results")
    os.makedirs(os.path.join(out, "chunks"), exist_ok=True); os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    ns = (6, 6, 3, 6) if a.smoke else (N_TR, N_TE, N_BTW, N_BFS)
    n_seeds = 2 if a.smoke else a.seeds
    deadline = parse_deadline(a.deadline)
    reserve = dt.timedelta(minutes=20)
    logf = open(os.path.join(HERE, "logs", "e0x_smoke.log" if a.smoke else "e0x.log"), "a", encoding="utf-8")

    def log(msg):
        s = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
        print(s, flush=True); logf.write(s + "\n"); logf.flush()

    sha = {p: hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] for p in ("E0X_PLAN.md", "e0x.py", "../5_E0_ho_so_da_thang/e0.py") if os.path.exists(p)}
    log(f"Bắt đầu E0x {'(smoke)' if a.smoke else ''}: {len(GRAPHS)} đồ thị x {len(FS)} f; tối đa {n_seeds} seed; "
        f"{a.workers} tiến trình; hạn {deadline:%d/%m %H:%M}" if deadline else
        f"Bắt đầu E0x {'(smoke)' if a.smoke else ''}: tối đa {n_seeds} seed; {a.workers} tiến trình; không đặt hạn")
    log(f"SHA-256: {sha}")
    t_all = time.time(); secs = 0.0
    if not a.analyze_only:
        for gid in GRAPHS:
            G, _ = e0.load_graph(gid)
            betweenness(gid, G, out)
        log("Đã có betweenness của 4 đồ thị.")
        cells = sorted(((g, f) for g in GRAPHS for f in FS), key=lambda x: (-x[1], x[0] != "email_eu"))
        n_done_new, t_new = 0, 0.0
        pending = {}
        si = 0
        stop = False
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            while (si < n_seeds and not stop) or pending:
                if si < n_seeds and not stop and len(pending) < 2 * a.workers:
                    if deadline and si >= 1 and n_done_new:
                        wall_per_task = (time.time() - t_all) / max(1, n_done_new)
                        eta = dt.datetime.now() + dt.timedelta(seconds=wall_per_task * (len(pending) + len(cells)))
                        if eta > deadline - reserve:
                            log(f"Dừng nhận seed mới trước seed {si}: dự báo xong lúc {eta:%H:%M}, quá hạn trừ dự phòng.")
                            stop = True
                            continue
                    sidx = si + 900 if a.smoke else si
                    for g, f in cells:
                        pending[ex.submit(run_task, sidx, g, f, ns, out)] = (sidx, g, f)
                    si += 1
                    continue
                done, _ = wait(list(pending), return_when=FIRST_COMPLETED)
                for fu in done:
                    s, g, f = pending.pop(fu)
                    _, _, _, sec, skipped = fu.result()
                    if not skipped:
                        n_done_new += 1; secs += sec
                    if not any(v[0] == s for v in pending.values()):
                        log(f"Xong seed {s} ({n_done_new} phần mới, {(time.time() - t_all) / 60:.1f} phút từ đầu).")
    rows = load_rows(out)
    seeds = complete_seeds(rows)
    log(f"Phân tích {len(seeds)} seed hoàn tất ...")
    C, A_ = analyze(rows, seeds)
    vc, va = report(C, A_, seeds, os.path.join(out, "E0X_REPORT.md"), a.smoke, secs)
    log(f"Kết thúc. E0c: {vc}; E0a (Ha2): {va}. Báo cáo: {os.path.join(out, 'E0X_REPORT.md')}")


if __name__ == "__main__":
    main()
