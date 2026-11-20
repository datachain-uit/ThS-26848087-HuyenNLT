"""J-K3 — độ bền của phát hiện F1 theo hàm điểm (recall / prec / min của tác giả) và mức pow (0,3 / 0,5 / 0,7).
Giao thức: JK3_PLAN.md. Chạy: python jk3.py"""
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
POWS = [0.3, 0.5, 0.7]
SEED = 20261118
GROUPS, KS = jk.GROUPS, jk.KS


def run(graph, rz):
    exp = f"SIR_nsrc1-15_Rzero{rz}_gamma0.1-0.4_ls8000_nf16"
    d = pickle.load(open(os.path.join(CN, "SD-STGCN", "output", "test_res", graph, exp, "res.pickle"), "rb"))
    n = np.asarray(d["predictions"][0][0]).shape[0]
    G = nx.read_edgelist(os.path.join(CN, "SD-STGCN", "dataset", graph, "data", "graph", graph + ".edgelist"), nodetype=int)
    G.add_nodes_from(range(n))
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=float))
    samples = []
    for b in range(len(d["inputs"])):
        for j in range(len(d["inputs"][b])):
            inp = np.asarray(d["inputs"][b][j]); pr = np.asarray(d["predictions"][b][j])[:, 1]; gt = np.asarray(d["ground_truth"][b][j])
            samples.append((np.nonzero(inp)[0], pr, gt))
    X = np.array([jk.feats(A, s[0]) for s in samples]); K = np.array([int(s[2].sum()) for s in samples])
    rng0 = np.random.default_rng(SEED)
    perm = rng0.permutation(len(K))
    ktr, kcal, rest = perm[:jk.N_KTR], perm[jk.N_KTR:jk.N_K], perm[jk.N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((len(K), len(KS))); P[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X)
    sc = 1 - P[kcal, [KS.index(k) for k in K[kcal]]]
    qk = np.quantile(sc, min(1, np.ceil((len(sc) + 1) * (1 - jk.ALPHA_K)) / len(sc)), method="higher")
    KSET = P >= 1 - qk
    out = {}
    for sname, (fcal, ftest) in SCORES.items():
        TS = [np.asarray(ftest(s[1], jk.PROP, s[0])) for s in samples]
        for pw in POWS:
            CS = np.array([fcal(s[1], jk.set_truncate(s[2], s[1], pw), jk.PROP, s[0]) for s in samples])
            thr = lambda pool: jk.cpquantile(CS[pool], (1 - jk.ALPHA) * (1 + 1 / len(pool)))

            def ev(i, t):
                pred = np.where(TS[i] <= t)[0]; src = np.nonzero(samples[i][2])[0]
                return (len(np.intersect1d(src, pred)) / len(src) >= pw), len(pred)

            rng = np.random.default_rng(SEED + 1)
            acc = {m: {"cov": [], "size": [], "grp": {g: [] for g in GROUPS}} for m in ("G", "O", "KS")}
            for _ in range(jk.REPS):
                p = rng.permutation(rest); cal, te = p[:jk.N_CAL], p[jk.N_CAL:jk.N_CAL + jk.N_TE]
                tG = thr(cal); tk = {k: thr(cal[K[cal] == k]) for k in KS}; cache = {}
                res = {m: [] for m in acc}
                for i in te:
                    ks = tuple(np.array(KS)[KSET[i]])
                    if ks not in cache:
                        pool = cal[np.isin(K[cal], ks)]; cache[ks] = thr(pool) if len(pool) else tG
                    for m, t in (("G", tG), ("O", tk[K[i]]), ("KS", cache[ks])):
                        res[m].append((K[i],) + ev(i, t))
                for m in acc:
                    arr = np.array(res[m], float)
                    acc[m]["cov"].append(arr[:, 1].mean()); acc[m]["size"].append(arr[:, 2].mean())
                    for g in GROUPS:
                        sel = (arr[:, 0] >= g[0]) & (arr[:, 0] <= g[1]); acc[m]["grp"][g].append(arr[sel, 1].mean())
            out[(sname, pw)] = {m: dict(cov=float(np.mean(v["cov"])), size=float(np.mean(v["size"])),
                                        grp={g: float(np.mean(v["grp"][g])) for g in GROUPS}) for m, v in acc.items()}
            print(f"  {graph} R0 {rz} {sname} pow {pw} xong", flush=True)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK3_PLAN.md", "jk3.py")}
    print(f"J-K3 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {c: run(*c) for c in CONFIGS}
    combos = [(c, s, p) for c in CONFIGS for s in SCORES for p in POWS]
    sane = [x for x in combos if 0.87 <= R[x[0]][(x[1], x[2])]["G"]["cov"] <= 0.93]
    f1 = [x for x in sane if R[x[0]][(x[1], x[2])]["G"]["grp"][GROUPS[0]] < 0.85]
    frac = len(f1) / max(1, len(sane))
    verdict = "BỀN" if frac >= 0.8 else ("KHÔNG BỀN" if frac <= 0.4 else "BỀN MỘT PHẦN")
    L = ["# J-K3 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK3_PLAN.md`.\n",
         f"## Kết luận: **F1 {verdict}** — G phủ < 0,85 ở nhóm k 1–3 trong {len(f1)}/{len(sane)} tổ hợp hợp lệ "
         f"(độ phủ biên G trong [0,87; 0,93] ở {len(sane)}/{len(combos)} tổ hợp).\n",
         "## Tóm tắt theo hàm điểm × pow (trung bình trên 9 cấu hình)\n",
         "| Điểm | pow | G phủ | G phủ k 1–3 (min–max) | G kích thước | KS phủ nhóm thấp nhất (TB) | KS kích thước | O kích thước | số cấu hình F1 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for s in SCORES:
        for p in POWS:
            rows = [R[c][(s, p)] for c in CONFIGS]
            g13 = [r["G"]["grp"][GROUPS[0]] for r in rows]
            nf1 = sum(1 for c in CONFIGS if (c, s, p) in f1)
            L.append(f"| {s} | {p} | {np.mean([r['G']['cov'] for r in rows]):.3f} | {min(g13):.2f}–{max(g13):.2f} | "
                     f"{np.mean([r['G']['size'] for r in rows]):.1f} | {np.mean([min(r['KS']['grp'].values()) for r in rows]):.2f} | "
                     f"{np.mean([r['KS']['size'] for r in rows]):.1f} | {np.mean([r['O']['size'] for r in rows]):.1f} | {nf1}/9 |")
    L += ["\n## Chi tiết\n", "| Đồ thị | R0 | Điểm | pow | G phủ / cỡ | G phủ k 1–3 / 4–7 / 8–11 / 12–15 | KS phủ / cỡ / nhóm thấp nhất | O phủ / cỡ |",
          "|---|---|---|---|---|---|---|---|"]
    for c in CONFIGS:
        for s in SCORES:
            for p in POWS:
                r = R[c][(s, p)]
                L.append(f"| {c[0]} | {c[1]} | {s} | {p} | {r['G']['cov']:.3f} / {r['G']['size']:.1f} | "
                         + " / ".join(f"{r['G']['grp'][g]:.2f}" for g in GROUPS)
                         + f" | {r['KS']['cov']:.3f} / {r['KS']['size']:.1f} / {min(r['KS']['grp'].values()):.2f} | {r['O']['cov']:.3f} / {r['O']['size']:.1f} |")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK3_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: F1 {verdict}", flush=True)


if __name__ == "__main__":
    main()
