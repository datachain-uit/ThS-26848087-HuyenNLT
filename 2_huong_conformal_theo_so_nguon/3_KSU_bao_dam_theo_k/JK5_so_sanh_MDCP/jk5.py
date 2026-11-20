"""J-K5 — KS-U so với MDCP (Yang & Jin 2026) và WCP. Giao thức: JK5_PLAN.md. Chạy: python jk5.py [--smoke]"""
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

SMOKE = "--smoke" in sys.argv
CN = jk.CN
CONFIGS = [(g, r) for g in ("highSchool", "sfhh", "bkFratB") for r in ("1-15", "11-25", "21-35")]
SCORES = {"recall": (jk.recall_score, jk.recall_score_gtunknown), "prec": (avg_score, avg_score_gtunknown),
          "min": (min_score, min_score_gtunknown)}
POW, ALPHA = 0.3, 0.10
KSU_VARIANTS = {"KSU*": (0.02, 0.08, True), "KSUa": (0.05, 0.05, True), "KSUc": (0.01, 0.09, True), "KSU4": (0.05, 0.05, False)}
METH = ("G", "O", "WCP", "MD") + tuple(KSU_VARIANTS)
SEED = 900 if SMOKE else 20261118
REPS = 2 if SMOKE else jk.REPS
GROUPS, KS = jk.GROUPS, jk.KS
KSA = np.array(KS)


def cq(z, a):
    """Ngưỡng conformal đúng: phần tử thứ ceil((1-a)(n+1)) của z đã sắp; +inf nếu vượt n."""
    n = len(z)
    if n == 0:
        return np.inf
    r = int(np.ceil((1 - a) * (n + 1)))
    return np.inf if r > n else np.sort(z)[r - 1]


def wcp_thresholds(CSc, Kc, LAM):
    """WCP (Wang et al.): với mỗi điểm kiểm, q nhỏ nhất thỏa sum_c lam_c m_c(q)/(n_c+1) >= 1-ALPHA. Vector hóa."""
    cand = np.unique(CSc)
    M = np.zeros((len(KS), len(cand)))
    for j, c in enumerate(KS):
        s = np.sort(CSc[Kc == c])
        if len(s):
            M[j] = np.searchsorted(s, cand, side="right") / (len(s) + 1)
    W = LAM @ M  # (n_test, n_cand), không giảm theo q
    ok = W >= 1 - ALPHA
    idx = ok.argmax(1)
    return np.where(ok.any(1), cand[idx], np.inf)


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
    SK = 1 - P[np.arange(len(K)), K - 1]  # điểm của nhãn k thật (KS = 1..15)
    out = {"kset": {v: [] for v in KSU_VARIANTS}}
    for sname, (fcal, ftest) in SCORES.items():
        TS = [np.asarray(ftest(s[1], jk.PROP, s[0])) for s in samples]
        CS = np.array([fcal(s[1], jk.set_truncate(s[2], s[1], POW), jk.PROP, s[0]) for s in samples])
        rng = np.random.default_rng(SEED + 1)
        acc = {m: {"cov": [], "size": [], "grp": {g: [] for g in GROUPS}, "k": {c: [] for c in KS}} for m in METH}
        for _ in range(REPS):
            p = rng.permutation(rest); cal, te = p[:jk.N_CAL], p[jk.N_CAL:jk.N_CAL + jk.N_TE]
            Kc, Cc = K[cal], CS[cal]
            th = {"G": np.full(len(te), cq(Cc, ALPHA)),
                  "O": np.array([cq(Cc[Kc == k], ALPHA) for k in K[te]]),
                  "WCP": wcp_thresholds(Cc, Kc, P[te])}
            t10 = np.array([cq(Cc[Kc == c], ALPHA) for c in KS])
            th["MD"] = np.full(len(te), t10.max())
            for v, (ak, as_, shared) in KSU_VARIANTS.items():
                kidx = np.concatenate([kcal, cal]) if shared else kcal
                qk = np.array([cq(SK[kidx][K[kidx] == c], ak) for c in KS])
                KSET = (1 - P[te]) <= qk[None, :]
                ts = np.array([cq(Cc[Kc == c], as_) for c in KS])
                th[v] = np.array([ts[row].max() if row.any() else np.inf for row in KSET])
                if sname == "recall":
                    out["kset"][v].append((min(KSET[K[te] == c, c - 1].mean() for c in KS if (K[te] == c).any()), KSET.sum(1).mean()))
            for m in METH:
                cov, size = [], []
                for i, t in zip(te, th[m]):
                    pred = np.where(TS[i] <= t)[0]; src = np.nonzero(samples[i][2])[0]
                    cov.append(len(np.intersect1d(src, pred)) / len(src) >= POW); size.append(len(pred))
                cov, size, kk = np.array(cov, float), np.array(size, float), K[te]
                acc[m]["cov"].append(cov.mean()); acc[m]["size"].append(size.mean())
                for g in GROUPS:
                    acc[m]["grp"][g].append(cov[(kk >= g[0]) & (kk <= g[1])].mean())
                for c in KS:
                    if (kk == c).any():
                        acc[m]["k"][c].append(cov[kk == c].mean())
        out[sname] = {m: dict(cov=float(np.mean(v["cov"])), size=float(np.mean(v["size"])),
                              grp={g: float(np.mean(v["grp"][g])) for g in GROUPS},
                              kmin=float(min(np.mean(x) for x in v["k"].values() if x))) for m, v in acc.items()}
        print(f"  {graph} R0 {rz} {sname} xong", flush=True)
    out["kset"] = {v: (float(np.mean([a for a, _ in x])), float(np.mean([b for _, b in x]))) for v, x in out["kset"].items()}
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if SMOKE:
        run(*CONFIGS[-1])
        print("smoke ok", flush=True)
        return
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK5_PLAN.md", "jk5.py")}
    print(f"J-K5 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {c: run(*c) for c in CONFIGS}
    combos = [(c, s) for c in CONFIGS for s in SCORES]
    mn = lambda c, s, m: min(R[c][s][m]["grp"].values())
    sz = lambda c, s, m: R[c][s][m]["size"]
    C1 = min(sum(mn(c, s, m) >= 0.88 for c, s in combos) for m in ("KSU*", "MD"))
    c2n = sum(sz(c, s, "KSU*") < sz(c, s, "MD") for c, s in combos)
    c2r = float(np.mean([sz(c, s, "KSU*") / sz(c, s, "MD") for c, s in combos]))
    c3r = float(np.mean([sz(c, s, "KSU*") / sz(c, s, "WCP") for c, s in combos]))
    ok1, ok2, ok3 = C1 >= 25, (c2n >= 20 and c2r <= 0.85), c3r <= 1.25
    v = "GO" if ok1 and ok2 and ok3 else ("MỘT PHẦN" if ok1 and ok2 else "NO-GO")
    L = ["# J-K5 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK5_PLAN.md`.\n",
         f"## Kết luận: **{v}**\n",
         f"- C1 (hợp lệ, cần ≥ 25/27 cho cả KSU* và MD): {C1}/27 → {'đạt' if ok1 else 'trượt'}",
         f"- C2 (KSU* nhỏ hơn MD, cần ≥ 20/27 và tỉ số ≤ 0,85): {c2n}/27, tỉ số {c2r:.2f} → {'đạt' if ok2 else 'trượt'}",
         f"- C3 (KSU*/WCP ≤ 1,25): {c3r:.2f} → {'đạt' if ok3 else 'trượt'}\n",
         "## Tóm tắt (trung bình 9 cấu hình): phủ nhóm thấp nhất / phủ k thấp nhất / kích thước\n",
         "| Điểm | " + " | ".join(METH) + " |", "|---|" + "---|" * len(METH)]
    for s in SCORES:
        L.append(f"| {s} | " + " | ".join(
            f"{np.mean([mn(c, s, m) for c in CONFIGS]):.2f} / {np.mean([R[c][s][m]['kmin'] for c in CONFIGS]):.2f} / {np.mean([sz(c, s, m) for c in CONFIGS]):.1f}"
            for m in METH) + " |")
    L += ["\n## Tập k K̂ (đo trên điểm recall): phủ lớp thấp nhất / cỡ trung bình\n", "| Đồ thị | R0 | " + " | ".join(KSU_VARIANTS) + " |",
          "|---|---|" + "---|" * len(KSU_VARIANTS)]
    for c in CONFIGS:
        L.append(f"| {c[0]} | {c[1]} | " + " | ".join(f"{R[c]['kset'][v][0]:.2f} / {R[c]['kset'][v][1]:.1f}" for v in KSU_VARIANTS) + " |")
    L += ["\n## Chi tiết: phủ biên / phủ nhóm thấp nhất / kích thước\n", "| Đồ thị | R0 | Điểm | " + " | ".join(METH) + " |",
          "|---|---|---|" + "---|" * len(METH)]
    for c in CONFIGS:
        for s in SCORES:
            L.append(f"| {c[0]} | {c[1]} | {s} | " + " | ".join(
                f"{R[c][s][m]['cov']:.3f} / {mn(c, s, m):.2f} / {sz(c, s, m):.1f}" for m in METH) + " |")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK5_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {v}", flush=True)


if __name__ == "__main__":
    main()
