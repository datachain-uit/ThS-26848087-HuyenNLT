"""J-K4 — KS-U (có bảo đảm theo từng k) và baseline WCP (arXiv 2506.05583). Giao thức: JK4_PLAN.md. Chạy: python jk4.py"""
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
from sklearn.ensemble import RandomForestClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "2_chan_doan_phu_theo_k", "JK1_phu_theo_k"))
import jk
from utils.score_convert import avg_score, avg_score_gtunknown, min_score, min_score_gtunknown

CN = jk.CN
CONFIGS = [(g, r) for g in ("highSchool", "sfhh", "bkFratB") for r in ("1-15", "11-25", "21-35")]
SCORES = {"recall": (jk.recall_score, jk.recall_score_gtunknown), "prec": (avg_score, avg_score_gtunknown),
          "min": (min_score, min_score_gtunknown)}
POW, ALPHA, A_S, A_K = 0.3, 0.10, 0.05, 0.05
SEED = 20261118
GROUPS, KS = jk.GROUPS, jk.KS


def cq(z, a):  # ngưỡng conformal mức a (quy ước của tác giả)
    return jk.cpquantile(z, (1 - a) * (1 + 1 / len(z))) if len(z) else np.inf


def wcp_threshold(CSc, Kc, lam):
    """Ngưỡng nhỏ nhất q thỏa sum_c lam_c * m_c(q) / (n_c + 1) >= 1 - ALPHA (Wang et al. 2025)."""
    cand = np.unique(CSc)
    n = {c: (Kc == c).sum() for c in KS}
    srt = {c: np.sort(CSc[Kc == c]) for c in KS}
    lo, hi = 0, len(cand) - 1
    def ok(q):
        return sum(lam[i] * np.searchsorted(srt[c], q, side="right") / (n[c] + 1) for i, c in enumerate(KS) if n[c]) >= 1 - ALPHA
    if not ok(cand[-1]):
        return np.inf
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(cand[mid]):
            hi = mid
        else:
            lo = mid + 1
    return cand[lo]


def run(graph, rz):
    exp = f"SIR_nsrc1-15_Rzero{rz}_gamma0.1-0.4_ls8000_nf16"
    d = pickle.load(open(os.path.join(CN, "SD-STGCN", "output", "test_res", graph, exp, "res.pickle"), "rb"))
    n = np.asarray(d["predictions"][0][0]).shape[0]
    G = nx.read_edgelist(os.path.join(CN, "SD-STGCN", "dataset", graph, "data", "graph", graph + ".edgelist"), nodetype=int)
    G.add_nodes_from(range(n))
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=float))
    samples = [(np.nonzero(np.asarray(d["inputs"][b][j]))[0], np.asarray(d["predictions"][b][j])[:, 1], np.asarray(d["ground_truth"][b][j]))
               for b in range(len(d["inputs"])) for j in range(len(d["inputs"][b]))]
    X = np.array([jk.feats(A, s[0]) for s in samples]); K = np.array([int(s[2].sum()) for s in samples])
    rng0 = np.random.default_rng(SEED)
    perm = rng0.permutation(len(K))
    ktr, kcal, rest = perm[:jk.N_KTR], perm[jk.N_KTR:jk.N_K], perm[jk.N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((len(K), len(KS))); P[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X)
    sk = 1 - P[kcal, [KS.index(k) for k in K[kcal]]]
    # tập k gộp (như J-K) và tập k Mondrian theo lớp (cho KS-U)
    qk = np.quantile(sk, min(1, np.ceil((len(sk) + 1) * (1 - jk.ALPHA_K)) / len(sk)), method="higher")
    KSET = P >= 1 - qk
    qkc = np.array([cq(sk[K[kcal] == c], A_K) for c in KS])
    KSET_M = (1 - P) <= qkc[None, :]
    kcovM = {c: float(KSET_M[rest][K[rest] == c, KS.index(c)].mean()) for c in KS}
    out = {}
    for sname, (fcal, ftest) in SCORES.items():
        TS = [np.asarray(ftest(s[1], jk.PROP, s[0])) for s in samples]
        CS = np.array([fcal(s[1], jk.set_truncate(s[2], s[1], POW), jk.PROP, s[0]) for s in samples])

        def ev(i, t):
            pred = np.where(TS[i] <= t)[0]; src = np.nonzero(samples[i][2])[0]
            return (len(np.intersect1d(src, pred)) / len(src) >= POW), len(pred)

        rng = np.random.default_rng(SEED + 1)
        meth = ("G", "O", "KS", "KSU", "WCP")
        acc = {m: {"cov": [], "size": [], "grp": {g: [] for g in GROUPS}} for m in meth}
        for _ in range(jk.REPS):
            p = rng.permutation(rest); cal, te = p[:jk.N_CAL], p[jk.N_CAL:jk.N_CAL + jk.N_TE]
            tG = cq(CS[cal], ALPHA)
            tk10 = {c: cq(CS[cal][K[cal] == c], ALPHA) for c in KS}
            tk05 = np.array([cq(CS[cal][K[cal] == c], A_S) for c in KS])
            cache, wcache = {}, {}
            res = {m: [] for m in meth}
            for i in te:
                ks = tuple(np.array(KS)[KSET[i]])
                if ks not in cache:
                    pool = cal[np.isin(K[cal], ks)]; cache[ks] = cq(CS[pool], ALPHA) if len(pool) else tG
                tU = tk05[KSET_M[i]].max() if KSET_M[i].any() else np.inf
                tW = wcp_threshold(CS[cal], K[cal], P[i])
                for m, t in (("G", tG), ("O", tk10[K[i]]), ("KS", cache[ks]), ("KSU", tU), ("WCP", tW)):
                    res[m].append((K[i],) + ev(i, t))
            for m in meth:
                arr = np.array(res[m], float)
                acc[m]["cov"].append(arr[:, 1].mean()); acc[m]["size"].append(arr[:, 2].mean())
                for g in GROUPS:
                    sel = (arr[:, 0] >= g[0]) & (arr[:, 0] <= g[1]); acc[m]["grp"][g].append(arr[sel, 1].mean())
        out[sname] = {m: dict(cov=float(np.mean(v["cov"])), size=float(np.mean(v["size"])),
                              grp={g: float(np.mean(v["grp"][g])) for g in GROUPS}) for m, v in acc.items()}
        print(f"  {graph} R0 {rz} {sname} xong", flush=True)
    out["kcovM_min"] = min(kcovM.values())
    out["ksizeM"] = float(KSET_M[rest].sum(1).mean())
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK4_PLAN.md", "jk4.py")}
    print(f"J-K4 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {c: run(*c) for c in CONFIGS}
    combos = [(c, s) for c in CONFIGS for s in SCORES]
    mn = lambda c, s, m: min(R[c][s][m]["grp"].values())
    T1 = sum(mn(c, s, "KSU") >= 0.88 for c, s in combos)
    T2 = sum(mn(c, s, "WCP") < 0.85 for c, s in combos)
    v1 = "KS-U CÓ BẢO ĐẢM, KIỂM CHỨNG" if T1 >= 25 else "KS-U CHƯA ĐẠT"
    v2 = "WCP KHÔNG THAY ĐƯỢC" if T2 >= 14 else "WCP GIẢI QUYẾT ĐƯỢC PHẦN LỚN"
    L = ["# J-K4 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK4_PLAN.md`.\n",
         f"## Kết luận\n\n- T1: **{v1}** — KS-U phủ nhóm thấp nhất ≥ 0,88 ở {T1}/27 tổ hợp.\n- T2: **{v2}** — WCP phủ nhóm thấp nhất < 0,85 ở {T2}/27 tổ hợp.\n",
         "## Tóm tắt theo hàm điểm (trung bình 9 cấu hình): phủ nhóm thấp nhất / kích thước\n",
         "| Điểm | G | O | KS | KS-U | WCP |", "|---|---|---|---|---|---|"]
    for s in SCORES:
        L.append(f"| {s} | " + " | ".join(f"{np.mean([mn(c, s, m) for c in CONFIGS]):.2f} / {np.mean([R[c][s][m]['size'] for c in CONFIGS]):.1f}"
                                         for m in ("G", "O", "KS", "KSU", "WCP")) + " |")
    L += ["\n## Chi tiết: phủ biên / phủ nhóm thấp nhất / kích thước\n",
          "| Đồ thị | R0 | Điểm | G | O | KS | KS-U | WCP | tập k Mondrian: phủ lớp thấp nhất / cỡ |", "|---|---|---|---|---|---|---|---|---|"]
    for c in CONFIGS:
        for s in SCORES:
            L.append(f"| {c[0]} | {c[1]} | {s} | " + " | ".join(
                f"{R[c][s][m]['cov']:.3f} / {mn(c, s, m):.2f} / {R[c][s][m]['size']:.1f}" for m in ("G", "O", "KS", "KSU", "WCP"))
                + f" | {R[c]['kcovM_min']:.2f} / {R[c]['ksizeM']:.1f} |")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK4_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {v1}; {v2}", flush=True)


if __name__ == "__main__":
    main()
