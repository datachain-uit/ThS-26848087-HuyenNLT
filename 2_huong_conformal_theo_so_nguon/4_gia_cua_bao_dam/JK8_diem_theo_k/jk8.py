"""J-K8 — xếp hạng nút có điều kiện theo k (KC). Giao thức: JK8_PLAN.md. Chạy: python jk8.py [--smoke]"""
import _venv; _venv.ensure()
import datetime as dt
import hashlib
import os
import pickle
import platform
import sys

import numpy as np
import networkx as nx
import scipy.sparse as sp
from scipy.sparse.csgraph import shortest_path
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "3_KSU_bao_dam_theo_k", "JK5_so_sanh_MDCP"))
sys.path.append(os.path.join(HERE, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "4_gia_cua_bao_dam", "JK7_KNCP"))
sys.path.append(os.path.join(HERE, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "2_chan_doan_phu_theo_k", "JK1_phu_theo_k"))
import jk
from jk5 import cq, wcp_thresholds, SCORES, CONFIGS
from jk7 import min_cover

SMOKE = "--smoke" in sys.argv
POW, ALPHA, AK, AS = 0.3, 0.10, 0.02, 0.08
SEED = 900 if SMOKE else 20261118
REPS = 2 if SMOKE else jk.REPS
N_CAL, N_TE = 5600, 400
KS = jk.KS
METH = ("Dg-O", "KC-O", "Dg-KSU", "Df-KSU", "KC", "KC-MD")


def qneed(k):
    return next(q for q in range(1, k + 1) if q / k >= POW)


def prep(A, inf, p):
    m = len(inf)
    A_I = A[inf][:, inf].tocsr()
    DI = shortest_path(A_I, method="D", unweighted=True)
    centers, radii = jk.e0.kcenter_seq(DI, 15)
    DIf = np.where(np.isfinite(DI), DI, m + 1.0)
    ecc = DIf.max(1)
    pv = np.clip(p[inf], 1e-6, 1 - 1e-6)
    rank = np.empty(m); rank[np.argsort(-pv, kind="stable")] = np.arange(m)
    degG = np.asarray(A[inf].sum(1)).ravel(); degI = np.asarray(A_I.sum(1)).ravel()
    base = np.column_stack([np.log(pv / (1 - pv)), rank, rank / m, DIf[centers[0]] / (ecc.max() + 1), ecc / (ecc.max() + 1),
                            degG, degI, degI / np.maximum(degG, 1), np.full(m, m)])
    Dc = np.empty((15, m)); dmin = np.full(m, np.inf)
    for c in range(15):
        if c < len(centers):
            dmin = np.minimum(dmin, DIf[centers[c]])
        Dc[c] = dmin
    R = np.array([radii[min(c, len(radii) - 1)] for c in range(15)])
    return base, Dc, R


def kc_rows(base, Dc, R, c):
    m = base.shape[0]
    return np.column_stack([base, np.full(m, c), np.full(m, c / m), Dc[c - 1], Dc[c - 1] / (R[c - 1] + 1)])


def order_full(score_I, inf):
    return inf[np.argsort(-score_I, kind="stable")]


def depth(order, src, n, k):
    pos = np.full(n, n); pos[order] = np.arange(1, len(order) + 1)
    r = np.sort(pos[src]); return int(r[qneed(k) - 1])


def topset(order, mdep, n):
    if not np.isfinite(mdep) or mdep > len(order):
        return None  # cả đồ thị
    return order[:int(mdep)]


def run(graph, rz):
    exp = f"SIR_nsrc1-15_Rzero{rz}_gamma0.1-0.4_ls8000_nf16"
    d = pickle.load(open(os.path.join(jk.CN, "SD-STGCN", "output", "test_res", graph, exp, "res.pickle"), "rb"))
    n = np.asarray(d["predictions"][0][0]).shape[0]
    G = nx.read_edgelist(os.path.join(jk.CN, "SD-STGCN", "dataset", graph, "data", "graph", graph + ".edgelist"), nodetype=int)
    G.add_nodes_from(range(n))
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=float))
    samples = [(np.nonzero(np.asarray(d["inputs"][b][j]))[0], np.asarray(d["predictions"][b][j])[:, 1], np.asarray(d["ground_truth"][b][j]))
               for b in range(len(d["inputs"])) for j in range(len(d["inputs"][b]))]
    N = len(samples)
    X = np.array([jk.feats(A, s[0]) for s in samples]); K = np.array([int(s[2].sum()) for s in samples])
    SRC = [np.nonzero(s[2])[0] for s in samples]
    perm = np.random.default_rng(SEED).permutation(N)
    ktr, kcal, rest = perm[:jk.N_KTR], perm[jk.N_KTR:jk.N_K], perm[jk.N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((N, 15)); P[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X)
    SK = 1 - P[np.arange(N), K - 1]
    PR = [prep(A, s[0], s[1]) for s in samples]
    outside = float(np.mean([not np.isin(SRC[i], samples[i][0]).all() for i in rest]))
    # bộ xếp hạng lại: chỉ học trên ktr
    yb = [np.isin(samples[i][0], SRC[i]).astype(int) for i in ktr]
    Xf = np.vstack([PR[i][0] for i in ktr]); Xk = np.vstack([kc_rows(*PR[i], K[i]) for i in ktr]); y = np.concatenate(yb)
    hgb = dict(max_iter=300, learning_rate=0.05, random_state=0)
    mf = HistGradientBoostingClassifier(**hgb).fit(Xf, y)
    mk = HistGradientBoostingClassifier(**hgb).fit(Xk, y)
    # thứ tự nút cho mọi mẫu trong rest
    ORD_g, ORD_f, ORD_k = {}, {}, {}
    for i in rest:
        inf = samples[i][0]; base, Dc, R = PR[i]
        ORD_g[i] = order_full(samples[i][1][inf], inf)
        ORD_f[i] = order_full(mf.predict_proba(base)[:, 1], inf)
        sc = mk.predict_proba(np.vstack([kc_rows(base, Dc, R, c) for c in KS]))[:, 1].reshape(15, len(inf))
        ORD_k[i] = [order_full(sc[c], inf) for c in range(15)]
    if SMOKE:  # kiểm tra cài đặt độ sâu
        for i in np.random.default_rng(5).choice(rest, 300, replace=False):
            o = ORD_g[i]; dp = depth(o, SRC[i], n, K[i]); q = qneed(K[i])
            if dp <= len(o):
                assert np.isin(SRC[i], o[:dp]).sum() >= q and np.isin(SRC[i], o[:dp - 1]).sum() < q, "depth sai"
    DEP_g = {i: depth(ORD_g[i], SRC[i], n, K[i]) for i in rest}
    DEP_f = {i: depth(ORD_f[i], SRC[i], n, K[i]) for i in rest}
    DEP_k = {i: depth(ORD_k[i][K[i] - 1], SRC[i], n, K[i]) for i in rest}
    # điểm tác giả cho tham chiếu
    TSd, MCd, CSd = {}, {}, {}
    for sname, (fcal, ftest) in SCORES.items():
        TSd[sname] = {i: np.asarray(ftest(samples[i][1], jk.PROP, samples[i][0])) for i in rest}
        MCd[sname] = {i: min_cover(TSd[sname][i], SRC[i]) for i in rest}
        CSd[sname] = np.array([fcal(samples[i][1], jk.set_truncate(samples[i][2], samples[i][1], POW), jk.PROP, samples[i][0]) if i in TSd[sname] else np.nan
                               for i in range(N)])
    refs = [f"{m}-{s}" for m in ("WCP", "KSU") for s in SCORES]
    allm = METH + tuple(refs)
    cs = {m: np.zeros(15) for m in allm}; ss = {m: 0.0 for m in allm}; cnt = np.zeros(15); ntest = 0
    rng = np.random.default_rng(SEED + 1)
    for _ in range(REPS):
        p = rng.permutation(rest); cal, te = p[:N_CAL], p[N_CAL:N_CAL + N_TE]
        Kc = K[cal]
        kidx = np.concatenate([kcal, cal])
        qk = np.array([cq(SK[kidx][K[kidx] == c], AK) for c in KS])
        KH = (1 - P[te]) <= qk[None, :]; KH[~KH.any(1)] = True
        def thr(dep, lev):
            v = np.array([dep[i] for i in cal], float)
            return np.array([cq(v[Kc == c], lev) for c in KS])
        mg10, mk10 = thr(DEP_g, ALPHA), thr(DEP_k, ALPHA)
        mg08, mf08, mk08 = thr(DEP_g, AS), thr(DEP_f, AS), thr(DEP_k, AS)
        for t_i, i in enumerate(te):
            k = K[i]; q = qneed(k); src = SRC[i]; h = np.flatnonzero(KH[t_i])
            sets = {"Dg-O": topset(ORD_g[i], mg10[k - 1], n), "KC-O": topset(ORD_k[i][k - 1], mk10[k - 1], n),
                    "Dg-KSU": topset(ORD_g[i], mg08[h].max(), n), "Df-KSU": topset(ORD_f[i], mf08[h].max(), n)}
            for name, cl, mm in (("KC", h, mk08), ("KC-MD", np.arange(15), mk10)):
                parts = [topset(ORD_k[i][c], mm[c], n) for c in cl]
                sets[name] = None if any(x is None for x in parts) else np.unique(np.concatenate(parts))
            for m, S in sets.items():
                if S is None:
                    cs[m][k - 1] += 1; ss[m] += n
                else:
                    cs[m][k - 1] += np.isin(src, S).sum() >= q; ss[m] += len(S)
            cnt[k - 1] += 1; ntest += 1
        for sname in SCORES:
            Cc = CSd[sname][cal]
            tW = wcp_thresholds(Cc, Kc, P[te])
            ts8 = np.array([cq(Cc[Kc == c], AS) for c in KS])
            tK = np.array([ts8[r].max() for r in KH])
            for m, th in ((f"WCP-{sname}", tW), (f"KSU-{sname}", tK)):
                for i, t in zip(te, th):
                    cs[m][K[i] - 1] += t >= MCd[sname][i]; ss[m] += (TSd[sname][i] <= t).sum()
    res = {m: {"kmin": float((cs[m] / np.maximum(cnt, 1))[cnt > 0].min()), "cov": float(cs[m].sum() / ntest), "size": ss[m] / ntest} for m in allm}
    res["_outside"] = outside
    print(f"  {graph} R0 {rz} xong", flush=True)
    return res


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if SMOKE:
        run(*CONFIGS[-1]); print("smoke ok (độ sâu khớp)", flush=True); return
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK8_PLAN.md", "jk8.py")}
    print(f"J-K8 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {c: run(*c) for c in CONFIGS}
    best = lambda c, f: min(R[c][f"{f}-{s}"]["size"] for s in SCORES)
    V = sum(R[c]["KC"]["kmin"] >= 0.88 for c in CONFIGS)
    K1 = sum(R[c]["KC"]["size"] <= 0.85 * R[c]["Df-KSU"]["size"] for c in CONFIGS)
    K2 = sum(R[c]["KC"]["size"] <= 0.85 * best(c, "KSU") for c in CONFIGS)
    K3 = float(np.mean([R[c]["KC"]["size"] / best(c, "WCP") for c in CONFIGS]))
    oV, o1, o2, o3 = V >= 8, K1 >= 7, K2 >= 7, K3 <= 1.10
    v = ("GO" if oV and o1 and o2 and o3 else "MỘT PHẦN" if oV and o1 and o2 else
         "ĐIỀU KIỆN THEO k CÓ TÁC DỤNG, CHƯA ĐỦ" if oV and o1 else "NO-GO")
    cols = METH + tuple(f"{m}-{s}" for m in ("WCP", "KSU") for s in SCORES)
    L = ["# J-K8 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK8_PLAN.md`.\n",
         f"## Kết luận: **{v}**\n",
         f"- V (KC phủ theo k ≥ 0,88): {V}/9 → {'đạt' if oV else 'trượt'}",
         f"- K1 (KC ≤ 0,85 × Df-KSU): {K1}/9 → {'đạt' if o1 else 'trượt'}",
         f"- K2 (KC ≤ 0,85 × KSU*-a tốt nhất): {K2}/9 → {'đạt' if o2 else 'trượt'}",
         f"- K3 (KC / WCP-a tốt nhất ≤ 1,10): {K3:.2f} → {'đạt' if o3 else 'trượt'}\n",
         "## Trung bình 9 cấu hình: phủ / phủ theo k thấp nhất / kích thước\n", "| Phương pháp | phủ | phủ k thấp nhất | kích thước |", "|---|---|---|---|"]
    for m in cols:
        L.append(f"| {m} | {np.mean([R[c][m]['cov'] for c in CONFIGS]):.3f} | {np.mean([R[c][m]['kmin'] for c in CONFIGS]):.3f} | {np.mean([R[c][m]['size'] for c in CONFIGS]):.1f} |")
    L += ["\n## Chi tiết: phủ theo k thấp nhất / kích thước\n", "| Đồ thị | R0 | nguồn ngoài I | " + " | ".join(cols) + " |", "|---|---|---|" + "---|" * len(cols)]
    for c in CONFIGS:
        L.append(f"| {c[0]} | {c[1]} | {R[c]['_outside']:.3f} | " + " | ".join(f"{R[c][m]['kmin']:.2f} / {R[c][m]['size']:.1f}" for m in cols) + " |")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK8_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {v}", flush=True)


if __name__ == "__main__":
    main()
