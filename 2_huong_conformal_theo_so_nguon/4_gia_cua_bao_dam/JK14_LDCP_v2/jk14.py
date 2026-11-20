"""J-K14 — LD2 (LD-CP sửa). Giao thức: JK14_PLAN.md. Chạy: python jk14.py [--smoke]"""
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
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, HistGradientBoostingRegressor

HERE = os.path.dirname(os.path.abspath(__file__))
for p in ("2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK13_LDCP", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK11_do_thi_lon", "2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k"):
    sys.path.append(os.path.join(HERE, "..", p))
import jk
import jk11
from jk5 import cq, wcp_thresholds, CONFIGS
from jk8 import prep, order_full, depth, qneed
from jk13 import summ, EDGES0, kk_, SCEN, HGB, STRUCT

SMOKE = "--smoke" in sys.argv
POW, ALPHA, AK, AS = 0.3, 0.10, 0.02, 0.08
REPS = 2 if SMOKE else 50
KS = list(range(1, 16))
QL = np.array([0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99])
SET_A = [(g, m, t) for g in ("lfr10k_mu0.1_2", "lfr10k_mu0.3_2") for t in (25, 100, 300) for m in ("SI", "IC", "SIR")]
METH = ("G", "O", "WCP", "MD", "KSU*", "LD13", "LD2")


def evaluate(name, n, A, S, K, X, gnn_p, seed, n_ktr, n_k, n_cal, n_te):
    N = len(S)
    perm = np.random.default_rng(seed).permutation(N)
    ktr, kcal, rest = perm[:n_ktr], perm[n_ktr:n_k], perm[n_k:]
    A1, A2 = ktr[: n_ktr // 2], ktr[n_ktr // 2:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((N, 15)); idx = np.concatenate([kcal, rest])
    P[idx][:, :] = 0
    PP = np.zeros((len(idx), 15)); PP[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X[idx]); P[idx] = PP
    SK = 1 - P[np.arange(N), K - 1]
    half = np.full(n, 0.5)
    def feat(i):
        base = prep(A, S[i][0], gnn_p[i] if gnn_p is not None else half)[0]
        return base if gnn_p is not None else base[:, STRUCT]
    FE = {i: feat(i) for i in np.concatenate([ktr, rest])}
    def fit_rs(ids):
        y = np.concatenate([np.isin(S[i][0], S[i][1]).astype(int) for i in ids])
        return HistGradientBoostingClassifier(**HGB).fit(np.vstack([FE[i] for i in ids]), y)
    rs1, rs2 = fit_rs(A1), fit_rs(A2)
    DEP = np.zeros(N, int); MI = np.zeros(N, int); Z = {}
    for model, ids in ((rs1, np.concatenate([A2, rest])), (rs2, A1)):
        lens = [len(S[i][0]) for i in ids]
        allp = model.predict_proba(np.vstack([FE[i] for i in ids]))[:, 1]
        for i, pr in zip(ids, np.split(allp, np.cumsum(lens)[:-1])):
            DEP[i] = depth(order_full(pr, S[i][0]), S[i][1], n, K[i]); MI[i] = len(S[i][0])
            Z[i] = np.concatenate([X[i], [MI[i]], summ(pr)])
    E = np.array(sorted(set([e for e in EDGES0 if e < n] + [n]))); lE = np.log(E)
    def zrows(i):
        return np.column_stack([np.repeat(Z[i][None, :], 15, 0), kk_, kk_ / MI[i], [qneed(c) for c in KS]])
    # LD2: hồi quy phân vị trên cả ktr (cross-fit)
    Xd = np.vstack([zrows(i)[K[i] - 1] for i in ktr]); yd = np.log(np.array([DEP[i] for i in ktr], float))
    qms = [HistGradientBoostingRegressor(loss="quantile", quantile=q, **HGB).fit(Xd, yd) for q in QL]
    Femp = np.zeros((15, len(E)))
    for c in KS:
        dcs = np.array([DEP[i] for i in ktr if K[i] == c]) if np.any(K[ktr] == c) else DEP[ktr]
        Femp[c - 1] = (dcs[None, :] <= E[:, None]).mean(1)
    Gm = np.log1p(E) / np.log1p(n)
    big = np.vstack([zrows(i) for i in rest])
    Qp = np.sort(np.column_stack([m.predict(big) for m in qms]), 1)
    CDF2 = {}
    for t, i in enumerate(rest):
        Q = Qp[15 * t: 15 * (t + 1)]
        Fq = np.array([np.interp(lE, Q[c], QL, left=0.0, right=1.0) for c in range(15)])
        CDF2[i] = 0.8 * Fq + 0.1 * Femp + 0.1 * Gm[None, :]
    # LD13: bản J-K13 (phân loại ngăn trên A2, lambda = 1)
    bin_of = lambda d: int(np.searchsorted(E, d, side="left"))
    dm = HistGradientBoostingClassifier(**HGB).fit(np.vstack([zrows(i)[K[i] - 1] for i in A2]), np.array([bin_of(DEP[i]) for i in A2]))
    allpb = dm.predict_proba(big); CDF1 = {}
    for t, i in enumerate(rest):
        pb = np.zeros((15, len(E))); pb[:, dm.classes_] = allpb[15 * t: 15 * (t + 1)]; CDF1[i] = np.cumsum(pb, 1)
    def H(i, C):
        w = P[i] / max(P[i].sum(), 1e-12); return w @ C[i]
    def r_of(i, h):
        j = int(np.searchsorted(E, DEP[i] - 1, side="right")) - 1
        return 0.0 if j < 0 else float(h[j])
    def m_of(h, tau):
        j = np.flatnonzero(h > tau); return E[j[0]] if len(j) else np.inf
    HR = {"LD13": {i: H(i, CDF1) for i in rest}, "LD2": {i: H(i, CDF2) for i in rest}}
    RR = {v: {i: r_of(i, HR[v][i]) for i in rest} for v in HR}
    if SMOKE:
        for i in list(rest)[:300]:
            h = HR["LD2"][i]
            assert np.all(np.diff(h) >= -1e-12), "h giảm"
            assert np.all(h[E < n] < 1 - 1e-9), "h bão hòa trước n"
            for tau in (0.2, 0.5, 0.8, 0.95):
                assert (m_of(h, tau) >= DEP[i]) == (RR["LD2"][i] <= tau), "luật phủ sai"
    cs = {m: np.zeros(15) for m in METH}; ss = {m: np.zeros(15) for m in METH}; cnt = np.zeros(15)
    rng = np.random.default_rng(seed + 1)
    for _ in range(REPS):
        p = rng.permutation(rest); cal, te = p[:n_cal], p[n_cal:n_cal + n_te]
        Kc, kt = K[cal], K[te]
        kidx = np.concatenate([kcal, cal])
        qk = np.array([cq(SK[kidx][K[kidx] == c], AK) for c in KS])
        KH = (1 - P[te]) <= qk[None, :]; KH[~KH.any(1)] = True
        dc = DEP[cal].astype(float)
        t10 = np.array([cq(dc[Kc == c], ALPHA) for c in KS]); t08 = np.array([cq(dc[Kc == c], AS) for c in KS])
        th = {"G": np.full(len(te), cq(dc, ALPHA)), "O": t10[kt - 1], "WCP": wcp_thresholds(dc, Kc, P[te]),
              "MD": np.full(len(te), t10.max()), "KSU*": np.array([t08[h].max() for h in KH])}
        for v in HR:
            rc = np.array([RR[v][i] for i in cal])
            tau = max(cq(rc[Kc == c], ALPHA) for c in KS)
            th[v] = np.array([m_of(HR[v][i], tau) for i in te], float)
        np.add.at(cnt, kt - 1, 1)
        for m in METH:
            M = th[m]; whole = ~np.isfinite(M) | (M > MI[te])
            np.add.at(cs[m], kt - 1, whole | (DEP[te] <= M))
            np.add.at(ss[m], kt - 1, np.where(whole, n, np.where(np.isfinite(M), M, 0)))
    pr0 = cnt / cnt.sum(); res = {}
    for m in METH:
        ck, sk = cs[m] / np.maximum(cnt, 1), ss[m] / np.maximum(cnt, 1)
        j = int(np.argmin(np.where(cnt > 0, ck, np.inf)))
        res[m] = {"size": float(pr0 @ sk), "kmin": float(ck[j]), "lo": jk11.wilson_lo(ck[j], cnt[j]),
                  **{sc: float(w @ ck) for sc, w in SCEN.items()}}
    print(f"  {name} xong", flush=True)
    return res


def author(graph, rz, seed):
    exp = f"SIR_nsrc1-15_Rzero{rz}_gamma0.1-0.4_ls8000_nf16"
    d = pickle.load(open(os.path.join(jk.CN, "SD-STGCN", "output", "test_res", graph, exp, "res.pickle"), "rb"))
    n = np.asarray(d["predictions"][0][0]).shape[0]
    G = nx.read_edgelist(os.path.join(jk.CN, "SD-STGCN", "dataset", graph, "data", "graph", graph + ".edgelist"), nodetype=int)
    G.add_nodes_from(range(n))
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=float))
    raw = [(np.nonzero(np.asarray(d["inputs"][b][j]))[0], np.asarray(d["predictions"][b][j])[:, 1], np.asarray(d["ground_truth"][b][j]))
           for b in range(len(d["inputs"])) for j in range(len(d["inputs"][b]))]
    S = [(r[0], np.nonzero(r[2])[0]) for r in raw]; gp = [r[1] for r in raw]
    K = np.array([len(s[1]) for s in S]); X = np.array([jk.feats(A, s[0]) for s in S])
    return evaluate(f"tác giả {graph} R0 {rz}", n, A, S, K, X, gp, seed, jk.N_KTR, jk.N_K, jk.N_CAL, jk.N_TE)


def simulated(si, gid, mname, target, cache):
    if gid not in cache:
        cache[gid] = jk11.load(gid)
    n, A = cache[gid]
    rng = np.random.default_rng(jk11.SEED0 + si)
    S = jk11.simulate(A, n, jk11.MODELS[mname], rng, target)
    K = np.array([len(s[1]) for s in S]); X = np.array([jk.feats(A, s[0]) for s in S])
    return evaluate(f"{gid} {mname} I={target}", n, A, S, K, X, None, int(rng.integers(1 << 30)),
                    jk11.N_KTR, jk11.N_K, jk11.N_CAL, jk11.N_TE)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cache = {}
    if SMOKE:
        simulated(200, "lfr10k_mu0.3_2", "IC", 25, cache)
        author(*CONFIGS[-1], seed=900)
        print("smoke ok", flush=True); return
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK14_PLAN.md", "jk14.py")}
    print(f"J-K14 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {}
    for c in CONFIGS:
        R[("tác giả",) + c] = author(*c, seed=20261119)
    for i, s in enumerate(SET_A):
        R[s] = simulated(200 + i, *s, cache)
    keys = list(R)
    V1 = sum(R[k]["LD2"]["kmin"] >= 0.88 for k in keys); V2 = sum(R[k]["LD2"][sc] >= 0.88 for k in keys for sc in SCEN)
    r1 = [R[k]["LD2"]["size"] / R[k]["KSU*"]["size"] for k in keys]; r2 = [R[k]["LD2"]["size"] / R[k]["WCP"]["size"] for k in keys]
    oV = V1 >= 25 and V2 >= 103; o1 = np.mean(r1) <= 0.85 and sum(x < 1 for x in r1) >= 20
    o2 = np.mean(r2) <= 1.10; oS = all(x <= 2 for x in r1)
    v = "GO" if oV and o1 and o2 and oS else ("MỘT PHẦN" if oV and o1 and oS else "NO-GO")
    L = ["# J-K14 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK14_PLAN.md`.\n",
         f"## Kết luận: **{v}**\n",
         f"- V: LD2 phủ theo k ≥ 0,88 ở {V1}/27; lệch prior ≥ 0,88 ở {V2}/108 → {'đạt' if oV else 'trượt'}",
         f"- E1: LD2/KSU* trung bình {np.mean(r1):.2f} (trung vị {np.median(r1):.2f}), nhỏ hơn ở {sum(x < 1 for x in r1)}/27 → {'đạt' if o1 else 'trượt'}",
         f"- E2: LD2/WCP trung bình {np.mean(r2):.2f} (trung vị {np.median(r2):.2f}) → {'đạt' if o2 else 'trượt'}",
         f"- S: LD2 ≤ 2 × KSU* ở {sum(x <= 2 for x in r1)}/27 → {'đạt' if oS else 'trượt'}\n",
         "## Tóm tắt: phủ theo k thấp nhất / kích thước (trung bình theo nhóm)\n",
         "| Nhóm | " + " | ".join(METH) + " |", "|---|" + "---|" * len(METH)]
    for grp, ks in (("tác giả (9)", [k for k in keys if k[0] == "tác giả"]), ("tự mô phỏng (18)", [k for k in keys if k[0] != "tác giả"])):
        L.append(f"| {grp} | " + " | ".join(f"{np.mean([R[k][m]['kmin'] for k in ks]):.3f} / {np.mean([R[k][m]['size'] for k in ks]):.1f}" for m in METH) + " |")
    L += ["\n## Chi tiết: phủ theo k thấp nhất [cận dưới] / kích thước\n", "| Tập dữ liệu | " + " | ".join(METH) + " |", "|---|" + "---|" * len(METH)]
    for k in keys:
        L.append(f"| {' '.join(map(str, k))} | " + " | ".join(f"{R[k][m]['kmin']:.2f} [{R[k][m]['lo']:.2f}] / {R[k][m]['size']:.1f}" for m in METH) + " |")
    L += ["\n## Lệch prior: phủ thấp nhất trên 27 tập (S1 / S2 / S3 / S4)\n", "| " + " | ".join(METH) + " |", "|" + "---|" * len(METH),
          "| " + " | ".join(" / ".join(f"{min(R[k][m][sc] for k in keys):.2f}" for sc in SCEN) for m in METH) + " |"]
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK14_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {v}", flush=True)


if __name__ == "__main__":
    main()
