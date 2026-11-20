"""J-K6 — lệch prior k; đo lại độ phủ K̂. Giao thức: JK6_PLAN.md. Chạy: python jk6.py [--smoke]"""
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
sys.path.append(os.path.join(HERE, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "3_KSU_bao_dam_theo_k", "JK5_so_sanh_MDCP"))
sys.path.append(os.path.join(HERE, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "2_chan_doan_phu_theo_k", "JK1_phu_theo_k"))
import jk
from jk5 import cq, wcp_thresholds, SCORES, CONFIGS

SMOKE = "--smoke" in sys.argv
POW, ALPHA, AK, AS = 0.3, 0.10, 0.02, 0.08
SEED = 900 if SMOKE else 20261118
REPS = 2 if SMOKE else jk.REPS
N_CAL = 4000
KS = jk.KS
METH = ("G", "O", "WCP", "MD", "KSU*")
kk_ = np.arange(1, 16, dtype=float)
SCEN = {"S1 k1-3": np.where(kk_ <= 3, 1.0, 0.0), "S2 k11-15": np.where(kk_ >= 11, 1.0, 0.0),
        "S3 ~(16-k)^2": (16 - kk_) ** 2, "S4 ~k^2": kk_ ** 2}
SCEN = {k: v / v.sum() for k, v in SCEN.items()}


def run(graph, rz):
    exp = f"SIR_nsrc1-15_Rzero{rz}_gamma0.1-0.4_ls8000_nf16"
    d = pickle.load(open(os.path.join(jk.CN, "SD-STGCN", "output", "test_res", graph, exp, "res.pickle"), "rb"))
    n = np.asarray(d["predictions"][0][0]).shape[0]
    G = nx.read_edgelist(os.path.join(jk.CN, "SD-STGCN", "dataset", graph, "data", "graph", graph + ".edgelist"), nodetype=int)
    G.add_nodes_from(range(n))
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=float))
    samples = [(np.nonzero(np.asarray(d["inputs"][b][j]))[0], np.asarray(d["predictions"][b][j])[:, 1], np.asarray(d["ground_truth"][b][j]))
               for b in range(len(d["inputs"])) for j in range(len(d["inputs"][b]))]
    X = np.array([jk.feats(A, s[0]) for s in samples]); K = np.array([int(s[2].sum()) for s in samples])
    perm = np.random.default_rng(SEED).permutation(len(K))
    ktr, kcal, rest = perm[:jk.N_KTR], perm[jk.N_KTR:jk.N_K], perm[jk.N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((len(K), len(KS))); P[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X)
    SK = 1 - P[np.arange(len(K)), K - 1]
    prior0 = np.array([(K[rest] == c).mean() for c in KS])
    out = {"prior0": prior0}
    khit, kcnt = np.zeros(15), np.zeros(15)
    for sname, (fcal, ftest) in SCORES.items():
        TS = [np.asarray(ftest(s[1], jk.PROP, s[0])) for s in samples]
        CS = np.array([fcal(s[1], jk.set_truncate(s[2], s[1], POW), jk.PROP, s[0]) for s in samples])
        rng = np.random.default_rng(SEED + 1)
        cs = {m: np.zeros(15) for m in METH}; ss = {m: np.zeros(15) for m in METH}; cnt = np.zeros(15)
        for _ in range(REPS):
            p = rng.permutation(rest); cal, te = p[:N_CAL], p[N_CAL:]
            Kc, Cc = K[cal], CS[cal]
            th = {"G": np.full(len(te), cq(Cc, ALPHA)), "O": np.array([cq(Cc[Kc == k], ALPHA) for k in K[te]]),
                  "WCP": wcp_thresholds(Cc, Kc, P[te])}
            th["MD"] = np.full(len(te), max(cq(Cc[Kc == c], ALPHA) for c in KS))
            kidx = np.concatenate([kcal, cal])
            qk = np.array([cq(SK[kidx][K[kidx] == c], AK) for c in KS])
            KSET = (1 - P[te]) <= qk[None, :]
            ts = np.array([cq(Cc[Kc == c], AS) for c in KS])
            th["KSU*"] = np.array([ts[r].max() if r.any() else np.inf for r in KSET])
            kt = K[te]
            if sname == "recall":
                for c in KS:
                    sel = kt == c; khit[c - 1] += KSET[sel, c - 1].sum(); kcnt[c - 1] += sel.sum()
            for c in KS:
                cnt[c - 1] += (kt == c).sum()
            for m in METH:
                for i, t, k in zip(te, th[m], kt):
                    pred = np.where(TS[i] <= t)[0]; src = np.nonzero(samples[i][2])[0]
                    cs[m][k - 1] += len(np.intersect1d(src, pred)) / len(src) >= POW; ss[m][k - 1] += len(pred)
        res = {}
        for m in METH:
            ck, sk = cs[m] / np.maximum(cnt, 1), ss[m] / np.maximum(cnt, 1)
            res[m] = {"S0": (float(prior0 @ ck), float(prior0 @ sk)), "kmin": float(ck[cnt > 0].min())}
            for sc, w in SCEN.items():
                res[m][sc] = (float(w @ ck), float(w @ sk))
        out[sname] = res
        print(f"  {graph} R0 {rz} {sname} xong", flush=True)
    kc = khit / np.maximum(kcnt, 1)
    out["kset"] = (float(kc[kcnt > 0].min()), float(kc[kcnt > 0].mean()), int(kcnt[kcnt > 0].min()))
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if SMOKE:
        run(*CONFIGS[-1]); print("smoke ok", flush=True); return
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK6_PLAN.md", "jk6.py")}
    print(f"J-K6 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {c: run(*c) for c in CONFIGS}
    cells = [(c, s, sc) for c in CONFIGS for s in SCORES for sc in SCEN]
    P1 = sum(R[c][s]["KSU*"][sc][0] >= 0.88 for c, s, sc in cells)
    P2 = sum(R[c][s]["WCP"][sc][0] < 0.85 for c, s, sc in cells)
    P3 = sum(R[c]["kset"][0] >= 0.96 for c in CONFIGS)
    ok1, ok2, ok3 = P1 >= 103, P2 >= 27, P3 >= 8
    v = ("BẢO ĐẢM THEO k CÓ GIÁ TRỊ DƯỚI LỆCH PRIOR" if ok1 and ok2 else
         "KSU* BỀN NHƯNG WCP CŨNG BỀN" if ok1 else "KSU* KHÔNG BỀN")
    L = ["# J-K6 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK6_PLAN.md`.\n",
         f"## Kết luận: **{v}**\n",
         f"- P1 (KSU* phủ ≥ 0,88, cần ≥ 103/108): {P1}/108 → {'đạt' if ok1 else 'trượt'}",
         f"- P2 (WCP phủ < 0,85, cần ≥ 27/108): {P2}/108 → {'đạt' if ok2 else 'trượt'}",
         f"- P3 (K̂ phủ lớp thấp nhất gộp ≥ 0,96, cần ≥ 8/9): {P3}/9 → {'đạt' if ok3 else 'trượt'}\n",
         "## Độ phủ / kích thước theo kịch bản (trung bình 9 cấu hình)\n",
         "| Điểm | Kịch bản | " + " | ".join(METH) + " |", "|---|---|" + "---|" * len(METH)]
    for s in SCORES:
        for sc in ["S0"] + list(SCEN):
            L.append(f"| {s} | {sc} | " + " | ".join(
                f"{np.mean([R[c][s][m][sc][0] for c in CONFIGS]):.3f} / {np.mean([R[c][s][m][sc][1] for c in CONFIGS]):.1f}" for m in METH) + " |")
        L.append(f"| {s} | phủ k thấp nhất | " + " | ".join(f"{np.mean([R[c][s][m]['kmin'] for c in CONFIGS]):.3f}" for m in METH) + " |")
    L += ["\n## Ô thấp nhất của mỗi phương pháp (trên 108 ô lệch)\n", "| Phương pháp | phủ thấp nhất | ô |", "|---|---|---|"]
    for m in METH:
        w = min(cells, key=lambda x: R[x[0]][x[1]][m][x[2]][0])
        L.append(f"| {m} | {R[w[0]][w[1]][m][w[2]][0]:.3f} | {w[0][0]} R0 {w[0][1]} {w[1]} {w[2]} |")
    L += ["\n## K̂ (gộp 50 lần lặp): phủ lớp thấp nhất / trung bình / số điểm kiểm ít nhất mỗi lớp\n", "| Đồ thị | R0 | K̂ |", "|---|---|---|"]
    for c in CONFIGS:
        a, b, nmin = R[c]["kset"]; L.append(f"| {c[0]} | {c[1]} | {a:.3f} / {b:.3f} / {nmin} |")
    L += ["\n## Chi tiết độ phủ (S1 / S2 / S3 / S4)\n", "| Đồ thị | R0 | Điểm | " + " | ".join(METH) + " |", "|---|---|---|" + "---|" * len(METH)]
    for c in CONFIGS:
        for s in SCORES:
            L.append(f"| {c[0]} | {c[1]} | {s} | " + " | ".join(" / ".join(f"{R[c][s][m][sc][0]:.2f}" for sc in SCEN) for m in METH) + " |")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK6_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {v}", flush=True)


if __name__ == "__main__":
    main()
