"""Pilot D1 (ước lượng số nguồn bằng cộng đồng) + D2 (đặt monitor theo cộng đồng). Xem D12_PLAN.md.
  python d12.py --smoke      # chạy rất nhỏ để kiểm code (thư mục smoke/)
  python d12.py              # chạy chính thức (khóa giao thức trước) + viết D12_REPORT.md
  python d12.py --analyze    # chỉ phân tích lại từ CSV thô
"""
import _venv; _venv.ensure()
import argparse, csv, datetime as dt, glob, hashlib, json, os, time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import networkx as nx
import pandas as pd
from scipy.sparse.csgraph import shortest_path, connected_components
from scipy.stats import wilcoxon

import config as C
import h0lib as L
import h0b as B

SEED, SMOKE_SEED = 6060, 6161
GRAPHS = [("lfr_mu0.1_0", 0.1), ("lfr_mu0.3_0", 0.3), ("lfr_mu0.5_0", 0.5), ("email_eu", -1.0)]
OBS = ["si_t", "ic_T"]
D1_KS = [1, 2, 3, 5, 8]
KMAX = 15
TAUS = [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6]
RHOS = [1, 2, 3, 4, 5, 6]
CONSTS = [1, 2, 3, 5, 8]
BUDGETS = [0.05, 0.10]
N_RAND = 3
FULL = dict(d1=(40, 100), d2=(80, 150))
SMOKE = dict(d1=(5, 6), d2=(5, 8))
LOCK_FILES = ("D12_PLAN.md", "d12.py", "h0b.py", "h0lib.py", "config.py")


def log(msg, root="."):
    os.makedirs(os.path.join(root, "logs"), exist_ok=True)
    line = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(os.path.join(root, "logs", "d12.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


def lock(root):
    h = {f: L.sha256_file(f) for f in LOCK_FILES}
    path = "D12_lock.json"
    if os.path.exists(path):
        old = json.load(open(path, encoding="utf-8"))["sha256"]
        if old != h:
            raise SystemExit("DỪNG: tệp đã khóa bị sửa sau khi khóa: "
                             + ", ".join(f for f in h if old.get(f) != h[f]))
        log("Khóa giao thức: khớp D12_lock.json", root)
    else:
        L.save_json({"time": f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}", "seed": SEED, "sha256": h}, path)
        log("Đã khóa giao thức: " + json.dumps(h), root)


# ------------------------------------------------------------ dữ liệu, lan truyền có thời điểm nhiễm
def load_graph(gid):
    G = nx.read_edgelist(os.path.join("data", f"{gid}_edges.txt"), nodetype=int)
    G = nx.convert_node_labels_to_integers(G, ordering="sorted")
    A = L.graph_arrays(G)
    P = np.load(os.path.join("data", f"{gid}_parts.npz"))
    truth = np.load(os.path.join("data", f"{gid}_truth.npy"))
    gam, pse = P["gamma"], P["pseed"]
    d = int(np.flatnonzero((gam == 1.0) & (pse == 0))[0])
    return G, A, P["labels"], gam, d, truth


def si_times(A, src, rng, target):
    ip, ix = A.indptr, A.indices
    t = np.full(A.shape[0], -1); t[src] = 0; step = 0
    while (t >= 0).sum() < target:
        step += 1
        new = []
        for u in np.flatnonzero(t >= 0):
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[t[nb] < 0]
            if nb.size:
                new.extend(nb[rng.random(nb.size) < B.SI_BETA].tolist())
        if new:
            t[np.array(new)] = step
    return np.flatnonzero(t >= 0), t


def ic_times(A, src, p, rng, T):
    ip, ix = A.indptr, A.indices
    t = np.full(A.shape[0], -1); t[src] = 0; fr = list(src)
    for step in range(1, T + 1):
        new = []
        for u in fr:
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[t[nb] < 0]
            if nb.size:
                h = nb[rng.random(nb.size) < p]
                if h.size:
                    t[h] = step; new += h.tolist()
        fr = new
        if not fr:
            break
    return np.flatnonzero(t >= 0), t


def calib(A, obs, k, seed):
    if obs != "ic_T":
        return None
    p, _ = B.calib_p(A, k, seed, lambda s, pp, r: B.ic_steps(A, s, pp, r, B.T_STEPS))
    return p


def make_casc(A, obs, k, n_c, seed, p):
    n = A.shape[0]; rng = np.random.default_rng(seed); out = []; tries = 0
    while len(out) < n_c:
        tries += 1
        if tries > 400 * n_c:
            raise RuntimeError(f"{obs} k={k}: không đủ cascade 10-20%")
        src = rng.choice(n, k, replace=False)
        if obs == "ic_T":
            inf, t = ic_times(A, src, p, rng, B.T_STEPS)
        else:
            inf, t = si_times(A, src, rng, int(rng.uniform(B.LO, B.HI) * n))
        if B.LO <= inf.size / n <= B.HI:
            out.append((src, inf, t))
    return out


def dhondt(counts, k):
    m = np.zeros(len(counts), int)
    for _ in range(k):
        q = np.where(m < counts, counts / (m + 1), -1)
        if q.max() < 0:
            break
        m[int(np.argmax(q))] += 1
    return m


# ------------------------------------------------------------ D1
def comm_seqs(ctx, lab):
    lab_I = lab[ctx.I]
    comms, cnt = np.unique(lab_I, return_counts=True)
    seqs = []
    for c in comms:
        X = np.flatnonzero(lab_I == c)
        Ms = shortest_path(ctx.A_I[X][:, X], method="D", unweighted=True)
        cs, rs = B.kcenter_seq(Ms, min(KMAX, len(X)))
        seqs.append((X, cs, rs))
    return cnt, seqs


def rho_count(seqs, rho):
    return sum(next((i + 1 for i, v in enumerate(rs) if v <= rho), len(rs)) for _, _, rs in seqs)


def d1_task(gid, mu, obs, k, root, seed, nval, ntest):
    out = os.path.join(root, "results", "d1", f"{obs}__{gid}__k{k}.csv")
    if os.path.exists(out):
        return out
    t0 = time.time()
    G, A, labs, gam, d, truth = load_graph(gid); n = A.shape[0]
    allP = np.vstack([labs, truth[None, :]])          # 55 phân hoạch + cộng đồng thật (cuối)
    sizes = [np.bincount(l) for l in allP]
    lpsi = L.LPSI(A, C.LPSI_ALPHA)
    p = calib(A, obs, k, L.sub_seed(seed, "d1cal", gid, k))
    rows, taus = [], {}
    for split, nc in (("val", nval), ("test", ntest)):
        casc = make_casc(A, obs, k, nc, L.sub_seed(seed, "d1", gid, obs, k, split), p)
        T = np.zeros((nc, len(allP), len(TAUS)), np.int16)
        for ci, (src, inf, _) in enumerate(casc):
            ctx = L.CascadeCtx(A, src, inf)
            r = dict(split=split, graph=gid, mu=mu, obs=obs, k=k, cascade=ci,
                     p="" if p is None else round(p, 5), frac=round(inf.size / n, 4),
                     comp=int(connected_components(ctx.A_I, directed=False)[0]),
                     lpsi=int(len(lpsi.predict(inf))))
            cs, rs = B.kcenter_seq(ctx.DIIsub, KMAX)
            for m in range(1, KMAX + 1):
                r[f"r_{m}"] = rs[min(m, len(rs)) - 1]
                sc = L.score_pos(ctx, np.array(cs[:m]))
                r[f"jo_f1_{m}"] = sc["f1_1"]
            for tag, lab in (("D", allP[d]), ("T", allP[-1])):
                cnt, seqs = comm_seqs(ctx, lab)
                for rho in RHOS:
                    r[f"rho{tag}_{rho}"] = rho_count(seqs, rho)
                if tag == "D":                      # CommJordan (phân hoạch mặc định) với m tâm, m = 1..KMAX
                    for m in range(1, KMAX + 1):
                        pred = [i for (X, c_, _), mc in zip(seqs, dhondt(cnt, m)) for i in X[c_[:mc]]]
                        sc = L.score_pos(ctx, np.array(pred))
                        r[f"cj_f1_{m}"] = sc["f1_1"]; r[f"cj_ed_{m}"] = sc["ed"]
            for pi, (l, s) in enumerate(zip(allP, sizes)):
                f = np.bincount(l[inf], minlength=len(s)) / s
                T[ci, pi] = [(f >= tau).sum() for tau in TAUS]
            rows.append(r)
        taus[split] = T
    np.savez_compressed(out.replace(".csv", ".npz"), d=d, louv=np.flatnonzero(gam > 0), **taus)
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    log(f"[D1] {obs} {gid} k={k}: XONG {len(rows)} cascade, p={p}, {time.time() - t0:.0f}s", root)
    return out


# ------------------------------------------------------------ D2
def farthest(Dall, deg, nb):
    c = [int(np.argmax(deg))]; dmin = Dall[c[0]].copy()
    while len(c) < nb:
        x = int(np.argmax(dmin)); c.append(x); dmin = np.minimum(dmin, Dall[x])
    return np.array(c)


def comm_place(A, lab, deg, nb, kind):
    sizes = np.bincount(lab)
    rows = np.repeat(np.arange(A.shape[0]), np.diff(A.indptr))
    ext = np.bincount(rows, weights=(lab[A.indices] != lab[rows]).astype(float), minlength=A.shape[0])
    key = deg if kind == "prop" else ext
    out = []
    for c, mc in enumerate(dhondt(sizes, nb)):
        if mc:
            X = np.flatnonzero(lab == c)
            out.extend(X[np.lexsort((-deg[X], -key[X]))][:mc].tolist())
    return np.array(out)


def localize(Dall, obsn, t, ic, deg):
    tt = t[obsn]; m = tt >= 0
    inf, ti = obsn[m], tt[m].astype(float)
    if inf.size == 0:
        return int(np.argmax(deg)), None, 0
    D = Dall[:, inf]
    dm = D - D.mean(1, keepdims=True); tm = ti - ti.mean()
    var = (dm ** 2).sum(1)
    c = np.clip(np.divide(dm @ tm, var, out=np.zeros_like(var), where=var > 0), 0, None)   # độ trễ/hop, ước lượng tự do, ≥ 0
    sse = ((tm[None, :] - c[:, None] * dm) ** 2).sum(1)
    if ic:
        sse = np.where((D <= ti[None, :]).all(1), sse, sse + 1e9)
    first = inf[np.argmin(ti)]
    order = np.lexsort((Dall[:, first], np.round(sse, 9)))
    return int(order[0]), order, int(inf.size)


def d2_task(gid, mu, obs, root, seed, nval, ntest):
    out = os.path.join(root, "results", "d2", f"{obs}__{gid}.csv")
    if os.path.exists(out):
        return out
    t0 = time.time()
    G, A, labs, gam, d, truth = load_graph(gid); n = A.shape[0]
    Dall = shortest_path(A, method="D", unweighted=True)
    deg = np.asarray(A.sum(1)).ravel()
    bc = nx.betweenness_centrality(G); btw = np.array([bc[i] for i in range(n)])
    rngP = np.random.default_rng(L.sub_seed(seed, "d2place", gid))
    places = {}
    for b in BUDGETS:
        nb = int(round(b * n))
        for j in range(N_RAND):
            places[("rand", b, j)] = rngP.choice(n, nb, replace=False)
        places[("deg", b, 0)] = np.argsort(-deg, kind="stable")[:nb]
        places[("btw", b, 0)] = np.argsort(-btw, kind="stable")[:nb]
        places[("spread", b, 0)] = farthest(Dall, deg, nb)
        for tag, lab in (("def", labs[d]), ("truth", truth)):
            places[(f"cprop_{tag}", b, 0)] = comm_place(A, lab, deg, nb, "prop")
            places[(f"cbound_{tag}", b, 0)] = comm_place(A, lab, deg, nb, "bound")
    places[("full", 1.0, 0)] = np.arange(n)
    ic = obs == "ic_T"
    p = calib(A, obs, 1, L.sub_seed(seed, "d2cal", gid))
    rows = []
    for split, nc in (("val", nval), ("test", ntest)):
        for ci, (src, inf, t) in enumerate(make_casc(A, obs, 1, nc, L.sub_seed(seed, "d2", gid, obs, split), p)):
            s = int(src[0])
            for (strat, b, j), on in places.items():
                pred, order, ninf = localize(Dall, on, t, ic, deg)
                rank = np.nan if order is None else float(np.flatnonzero(order == s)[0]) / n
                rows.append(dict(split=split, graph=gid, mu=mu, obs=obs, cascade=ci, strat=strat, budget=b,
                                 draw=j, ed=float(Dall[s, pred]), ninf=ninf, rank=rank))
    pd.DataFrame(rows).to_csv(out + ".tmp", index=False)
    os.replace(out + ".tmp", out)
    log(f"[D2] {obs} {gid}: XONG {len(rows)} dòng, p={p}, {time.time() - t0:.0f}s", root)
    return out


# ------------------------------------------------------------ phân tích
def wil(a, b):
    """Wilcoxon một phía: a nhỏ hơn b."""
    try:
        return float(wilcoxon(a, b, alternative="less").pvalue)
    except ValueError:
        return 1.0


def d1_estimators(df, T, d, louv):
    R = df[[f"r_{m}" for m in range(1, KMAX + 1)]].to_numpy()
    E = {"comp": df["comp"].to_numpy(), "lpsi": df["lpsi"].to_numpy()}
    noimp = R[:, 1:] >= R[:, :-1]
    E["elbow0"] = np.where(noimp.any(1), noimp.argmax(1) + 1, KMAX)
    for rho in RHOS:
        le = R <= rho
        E[f"rhoG_{rho}"] = np.where(le.any(1), le.argmax(1) + 1, KMAX)
        E[f"rhoD_{rho}"] = df[f"rhoD_{rho}"].to_numpy()
        E[f"rhoT_{rho}"] = df[f"rhoT_{rho}"].to_numpy()
    for j, tau in enumerate(TAUS):
        E[f"tauD_{tau}"] = T[:, d, j]
        E[f"tauS_{tau}"] = np.median(T[:, louv, j], axis=1)
        E[f"tauT_{tau}"] = T[:, -1, j]
    for c in CONSTS:
        E[f"const_{c}"] = np.full(len(df), c)
    return {k_: np.maximum(1, np.asarray(v, float)) for k_, v in E.items()}


FAM = {"N": ("comp", "lpsi", "elbow0", "rhoG_"), "C": ("tauD_", "tauS_", "rhoD_"),
       "Ref": ("tauT_", "rhoT_"), "Const": ("const_",)}


def in_fam(name, fam):
    return any(name == p or (p.endswith("_") and name.startswith(p)) for p in FAM[fam])


def analyze_d1(root):
    files = sorted(glob.glob(os.path.join(root, "results", "d1", "*.csv")))
    if not files:
        return None, []
    parts = {}
    for f in files:
        df = pd.read_csv(f); z = np.load(f.replace(".csv", ".npz"))
        for split in ("val", "test"):
            sub = df[df.split == split].sort_values("cascade").reset_index(drop=True)
            key = (sub.obs.iloc[0], sub.graph.iloc[0], split)
            parts.setdefault(key, []).append((sub, z[split], int(z["d"]), z["louv"]))
    res, sens = [], []
    for (obs, gid, split) in sorted({(o, g, "test") for o, g, _ in parts}):
        est, kk, cj = {}, {}, {}
        for sp in ("val", "test"):
            items = parts[(obs, gid, sp)]
            dfs = pd.concat([x[0] for x in items], ignore_index=True)
            Es = [d1_estimators(x[0], x[1], x[2], x[3]) for x in items]
            est[sp] = {n_: np.concatenate([e[n_] for e in Es]) for n_ in Es[0]}
            kk[sp] = dfs["k"].to_numpy()
            cj[sp] = dfs[[f"cj_f1_{m}" for m in range(1, KMAX + 1)]].to_numpy()
            if sp == "test":
                Tt = np.concatenate([x[1] for x in items]); dd, louv = items[0][2], items[0][3]
        mae = {sp: {n_: np.abs(v - kk[sp]).mean() for n_, v in est[sp].items()} for sp in est}
        pick = {f: min((n_ for n_ in mae["val"] if in_fam(n_, f)), key=lambda n_: mae["val"][n_]) for f in FAM}
        e = {f: np.abs(est["test"][pick[f]] - kk["test"]) for f in FAM}
        def f1_at(name):
            m = np.clip(est["test"][name].astype(int), 1, KMAX) - 1
            return float(cj["test"][np.arange(len(m)), m].mean())
        row = dict(obs=obs, graph=gid)
        for f in FAM:
            v = est["test"][pick[f]]
            row.update({f"{f}_pick": pick[f], f"{f}_mae": e[f].mean(), f"{f}_exact": (v == kk["test"]).mean(),
                        f"{f}_bias": (v - kk["test"]).mean()})
            if f in ("N", "C", "Ref"):
                row[f"{f}_f1"] = f1_at(pick[f])
        row["oracle_f1"] = float(cj["test"][np.arange(len(kk["test"])), np.minimum(kk["test"], KMAX) - 1].mean())
        row["p"] = wil(e["C"], e["N"])
        row["pass"] = bool(row["C_mae"] <= 0.8 * row["N_mae"] and row["p"] < 0.01 and row["C_mae"] < row["Const_mae"])
        bD = min((n_ for n_ in mae["val"] if n_.startswith("tauD_")), key=lambda n_: mae["val"][n_])
        bS = min((n_ for n_ in mae["val"] if n_.startswith("tauS_")), key=lambda n_: mae["val"][n_])
        row["tauD_mae"], row["tauS_mae"] = mae["test"][bD], mae["test"][bS]
        j = TAUS.index(float(bD.split("_")[1]))
        mp = np.abs(np.maximum(1, Tt[:, louv, j]) - kk["test"][:, None]).mean(0)
        row.update(sens_min=mp.min(), sens_med=float(np.median(mp)), sens_max=mp.max(), sens_tau=bD)
        for kv in D1_KS:
            mk = kk["test"] == kv
            row[f"Cmae_k{kv}"] = e["C"][mk].mean(); row[f"Nmae_k{kv}"] = e["N"][mk].mean()
        res.append(row)
    R = pd.DataFrame(res)
    os.makedirs(os.path.join(root, "results", "summary"), exist_ok=True)
    R.to_csv(os.path.join(root, "results", "summary", "d1_summary.csv"), index=False)
    return R, files


def analyze_d2(root):
    files = sorted(glob.glob(os.path.join(root, "results", "d2", "*.csv")))
    if not files:
        return None, None
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    g = df.groupby(["obs", "graph", "split", "budget", "strat", "cascade"], as_index=False)[["ed", "ninf", "rank"]].mean()
    full = g[(g.strat == "full") & (g.split == "test")].groupby("obs").ed.mean()
    res = []
    NS, CS = ["rand", "deg", "btw", "spread"], ["cprop_def", "cbound_def"]
    for (obs, gid, b), h in g[g.strat != "full"].groupby(["obs", "graph", "budget"]):
        piv = {sp: h[h.split == sp].pivot(index="cascade", columns="strat", values="ed") for sp in ("val", "test")}
        mv = piv["val"].mean()
        bn, bc = min(NS, key=lambda s: mv[s]), min(CS, key=lambda s: mv[s])
        te = piv["test"]; en, ec = te[bn].mean(), te[bc].mean()
        row = dict(obs=obs, graph=gid, budget=b, N_pick=bn, C_pick=bc, N_ed=en, C_ed=ec, delta=en - ec,
                   p=wil(te[bc].to_numpy(), te[bn].to_numpy()))
        row["pass"] = bool(row["delta"] >= min(0.3, 0.1 * en) and row["p"] < 0.01)
        for s in te.columns:
            row[f"ed_{s}"] = te[s].mean()
        ht = h[h.split == "test"]
        row["noinf_" + bc] = float((ht[ht.strat == bc].ninf == 0).mean())
        row["noinf_" + bn] = float((ht[ht.strat == bn].ninf == 0).mean())
        row["rank_C"] = float(ht[ht.strat == bc]["rank"].mean()); row["rank_N"] = float(ht[ht.strat == bn]["rank"].mean())
        res.append(row)
    R = pd.DataFrame(res)
    R.to_csv(os.path.join(root, "results", "summary", "d2_summary.csv"), index=False)
    return R, full


def verdict(passes_by_obs, n_g, valid=None):
    ok = {o: v for o, v in passes_by_obs.items() if valid is None or valid.get(o, False)}
    if len(ok) < len(passes_by_obs):
        return "CHƯA KẾT LUẬN (có mô hình quan sát không hợp lệ) — trình GVHD"
    if all(v >= 3 / 4 * n_g for v in ok.values()):
        return "GO"
    if all(v <= 1 / 4 * n_g for v in ok.values()):
        return "NO-GO"
    return "CHƯA KẾT LUẬN — trình GVHD"


def f2(x):
    return "—" if pd.isna(x) else f"{x:.2f}"


def analyze(root, n_graphs):
    os.makedirs(os.path.join(root, "results", "summary"), exist_ok=True)
    R1, _ = analyze_d1(root); R2, full = analyze_d2(root)
    L_ = [f"# Pilot D1 + D2 — báo cáo (sinh tự động từ CSV thô)\n",
          f"{dt.datetime.now():%d/%m/%Y %H:%M}. Seed {SEED if root == '.' else SMOKE_SEED}. Giao thức: `D12_PLAN.md` "
          "(SHA-256 trong `D12_lock.json`). Pilot trả lời *có tín hiệu không*, không trả lời *có mới không*.\n"]
    if R1 is not None:
        pb = R1.groupby("obs")["pass"].sum().to_dict()
        L_ += [f"## D1 — ước lượng số nguồn\n", f"**Kết luận theo quy tắc định trước: {verdict(pb, n_graphs)}** "
               f"(số đồ thị đạt: {', '.join(f'{o} {v}/{n_graphs}' for o, v in pb.items())})\n",
               "Đạt khi MAE_C ≤ 0,8·MAE_N, Wilcoxon p < 0,01, và MAE_C < MAE hằng số. Đại diện mỗi họ chọn trên val.\n",
               "| Quan sát | Đồ thị | N (chọn) | MAE N | C (chọn) | MAE C | Ref cộng đồng thật | MAE Ref | MAE hằng số | p | Đúng % N / C | Lệch N / C | Đạt |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in R1.iterrows():
            L_.append(f"| {r.obs} | {r.graph} | {r.N_pick} | {f2(r.N_mae)} | {r.C_pick} | {f2(r.C_mae)} | {r.Ref_pick} | "
                      f"{f2(r.Ref_mae)} | {f2(r.Const_mae)} | {r.p:.3g} | {100 * r.N_exact:.0f} / {100 * r.C_exact:.0f} | "
                      f"{f2(r.N_bias)} / {f2(r.C_bias)} | {'✓' if r['pass'] else '✗'} |")
        L_ += ["\n### MAE theo k (test)\n", "| Quan sát | Đồ thị | " + " | ".join(f"k={k} N / C" for k in D1_KS) + " |",
               "|---|---|" + "---|" * len(D1_KS)]
        for _, r in R1.iterrows():
            L_.append(f"| {r.obs} | {r.graph} | " + " | ".join(f"{f2(r[f'Nmae_k{k}'])} / {f2(r[f'Cmae_k{k}'])}" for k in D1_KS) + " |")
        L_ += ["\n### Thăm dò (không dùng kết luận)\n",
               "F1@1 của CommJordan (phân hoạch mặc định) khi dùng k̂ của từng họ; oracle = k thật. "
               "Độ nhạy: MAE của `tau_τ*` qua 50 phân hoạch Louvain.\n",
               "| Quan sát | Đồ thị | F1@1 N | F1@1 C | F1@1 Ref | F1@1 k thật | MAE tauD / tauS | τ* | MAE qua 50 phân hoạch: min / trung vị / max |",
               "|---|---|---|---|---|---|---|---|---|"]
        for _, r in R1.iterrows():
            L_.append(f"| {r.obs} | {r.graph} | {f2(r.N_f1)} | {f2(r.C_f1)} | {f2(r.Ref_f1)} | {f2(r.oracle_f1)} | "
                      f"{f2(r.tauD_mae)} / {f2(r.tauS_mae)} | {r.sens_tau} | {f2(r.sens_min)} / {f2(r.sens_med)} / {f2(r.sens_max)} |")
    if R2 is not None:
        valid = {o: bool(full.get(o, 99) <= 1.0) for o in OBS if o in full}
        pg = (R2.groupby(["obs", "graph"])["pass"].any().groupby("obs").sum()).to_dict()
        L_ += [f"\n## D2 — đặt monitor (k = 1)\n",
               "Kiểm tra hợp lệ V-D2 (ED của `full` ≤ 1,0): " + ", ".join(f"{o} {full[o]:.2f} {'✓' if valid[o] else '✗'}" for o in valid) + "\n",
               f"**Kết luận theo quy tắc định trước: {verdict(pg, n_graphs, valid)}** "
               f"(số đồ thị đạt: {', '.join(f'{o} {v}/{n_graphs}' for o, v in pg.items())})\n",
               "| Quan sát | Đồ thị | b | N (chọn) | ED N | C (chọn) | ED C | Δ | p | ED rand / deg / btw / spread | ED cprop / cbound (thật) | hạng % N / C | Đạt |",
               "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for _, r in R2.iterrows():
            L_.append(f"| {r.obs} | {r.graph} | {r.budget:.0%} | {r.N_pick} | {f2(r.N_ed)} | {r.C_pick} | {f2(r.C_ed)} | {f2(r.delta)} | "
                      f"{r.p:.3g} | {f2(r.ed_rand)} / {f2(r.ed_deg)} / {f2(r.ed_btw)} / {f2(r.ed_spread)} | "
                      f"{f2(r.ed_cprop_truth)} / {f2(r.ed_cbound_truth)} | {100 * r.rank_N:.1f} / {100 * r.rank_C:.1f} | {'✓' if r['pass'] else '✗'} |")
    L_ += ["\n## Nhắc lại giới hạn\n", "- 4 đồ thị, chỉ Louvain; D2 chỉ k = 1. GO ở pilot → viết giao thức chính thức (16 đồ thị, seed mới).",
           "- Tính mới chưa xét: D1 phải đối chiếu KBS 2020, D2 phải đối chiếu CSOL (CIKM 2025) bằng PDF."]
    path = os.path.join(root, "D12_REPORT.md")
    open(path, "w", encoding="utf-8").write("\n".join(L_) + "\n")
    log(f"Đã viết {path}", root)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--only", choices=["d1", "d2"]); ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    root = "smoke" if a.smoke else "."
    seed = SMOKE_SEED if a.smoke else SEED
    P = SMOKE if a.smoke else FULL
    graphs = GRAPHS[1:2] if a.smoke else GRAPHS
    ks = [1, 3] if a.smoke else D1_KS
    for sub in ("d1", "d2"):
        os.makedirs(os.path.join(root, "results", sub), exist_ok=True)
    if not a.analyze:
        if not a.smoke:
            lock(root)
        tasks = []
        if a.only != "d2":
            tasks += [(d1_task, (g, m, o, k, root, seed, *P["d1"])) for o in OBS for g, m in graphs for k in ks]
        if a.only != "d1":
            tasks += [(d2_task, (g, m, o, root, seed, *P["d2"])) for o in OBS for g, m in graphs]
        tasks.sort(key=lambda t: (t[1][0] != "email_eu", -(t[1][3] if t[0] is d1_task else 99)))
        log(f"=== {len(tasks)} việc, {a.workers} tiến trình ===", root)
        t0 = time.time(); done = 0
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for fu in as_completed([ex.submit(f, *args) for f, args in tasks]):
                fu.result(); done += 1
                el = (time.time() - t0) / 60
                log(f"--- Tiến độ {done}/{len(tasks)} ({el:.1f} phút; còn ~{el / done * (len(tasks) - done):.0f} phút) ---", root)
    analyze(root, len(graphs))
    log("=== D12 XONG ===", root)


if __name__ == "__main__":
    main()
