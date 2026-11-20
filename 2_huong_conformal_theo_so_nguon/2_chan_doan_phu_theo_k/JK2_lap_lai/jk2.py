"""J-K2 — kiểm lặp lại phát hiện của J-K trên 9 cấu hình của Jian et al. (3 đồ thị × 3 dải R0).
Phát hiện cần kiểm (F1): hiệu chỉnh gốc (G) phủ kém có hệ thống ở dịch ít nguồn (k 1–3).
Giao thức: JK2_PLAN.md. Chạy: python jk2.py"""
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
import jk  # feats, hàm điểm của tác giả (recall_score, recall_score_gtunknown, set_truncate, cpquantile), hằng số

CN = jk.CN
CONFIGS = [(g, r) for g in ("highSchool", "sfhh", "bkFratB") for r in ("1-15", "11-25", "21-35")]
ORIGINAL = ("highSchool", "1-15")  # cấu hình đã dùng ở J-K
SEED = 20261118
GROUPS = jk.GROUPS
KS = jk.KS


def run(graph, rz):
    exp = f"SIR_nsrc1-15_Rzero{rz}_gamma0.1-0.4_ls8000_nf16"
    d = pickle.load(open(os.path.join(CN, "SD-STGCN", "output", "test_res", graph, exp, "res.pickle"), "rb"))
    n = np.asarray(d["predictions"][0][0]).shape[0]
    G = nx.read_edgelist(os.path.join(CN, "SD-STGCN", "dataset", graph, "data", "graph", graph + ".edgelist"), nodetype=int)
    G.add_nodes_from(range(n))
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=float))
    X, K, CS, TS, NI = [], [], [], [], []
    for b in range(len(d["inputs"])):
        for j in range(len(d["inputs"][b])):
            inp = np.asarray(d["inputs"][b][j]); pr = np.asarray(d["predictions"][b][j])[:, 1]; gt = np.asarray(d["ground_truth"][b][j])
            inf = np.nonzero(inp)[0]
            X.append(jk.feats(A, inf)); K.append(int(gt.sum())); NI.append(len(inf))
            CS.append(jk.recall_score(pr, jk.set_truncate(gt, pr, jk.POW), jk.PROP, inf))
            TS.append((np.asarray(jk.recall_score_gtunknown(pr, jk.PROP, inf)), gt))
    X, K, CS = np.array(X), np.array(K), np.array(CS)
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(K))
    ktr, kcal, rest = perm[:jk.N_KTR], perm[jk.N_KTR:jk.N_K], perm[jk.N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((len(K), len(KS)))
    P[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X)
    sc = 1 - P[kcal, [KS.index(k) for k in K[kcal]]]
    qk = np.quantile(sc, min(1, np.ceil((len(sc) + 1) * (1 - jk.ALPHA_K)) / len(sc)), method="higher")
    KSET = P >= 1 - qk
    thr = lambda pool: jk.cpquantile(CS[pool], (1 - jk.ALPHA) * (1 + 1 / len(pool)))

    def ev(i, t):
        s, gt = TS[i]; pred = np.where(s <= t)[0]; src = np.nonzero(gt)[0]
        return (len(np.intersect1d(src, pred)) / len(src) >= jk.POW), len(pred)

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
    return dict(n=n, inf=float(np.mean(NI)), kcov=float(KSET[rest, [KS.index(k) for k in K[rest]]].mean()),
                ksize=float(KSET[rest].sum(1).mean()),
                **{m: dict(cov=float(np.mean(v["cov"])), size=float(np.mean(v["size"])),
                           grp={g: float(np.mean(v["grp"][g])) for g in GROUPS}) for m, v in acc.items()})


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK2_PLAN.md", "jk2.py")}
    print(f"J-K2 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {}
    for c in CONFIGS:
        R[c] = run(*c)
        print(f"done {c}", flush=True)
    new = [c for c in CONFIGS if c != ORIGINAL]
    sane = [c for c in new if 0.87 <= R[c]["G"]["cov"] <= 0.93]
    f1 = [c for c in new if R[c]["G"]["grp"][GROUPS[0]] < 0.85]
    if len(sane) < 6:
        verdict = f"KIỂM TRA (độ phủ biên của G ngoài [0,87; 0,93] ở {len(new) - len(sane)}/8 cấu hình) — xem bảng"
    elif len(f1) >= 6:
        verdict = "LẶP LẠI"
    elif len(f1) <= 2:
        verdict = "KHÔNG LẶP LẠI"
    else:
        verdict = "LẶP LẠI MỘT PHẦN"
    L = ["# J-K2 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK2_PLAN.md`.\n",
         f"## Kết luận F1: **{verdict}** — G phủ < 0,85 ở nhóm k 1–3 trong {len(f1)}/8 cấu hình mới; G phủ biên hợp lệ ở {len(sane)}/8.\n",
         "| Đồ thị | R0 | n | nhiễm TB | G phủ / kích thước | G phủ k 1–3 / 4–7 / 8–11 / 12–15 | O phủ / kích thước | KS phủ / kích thước | KS phủ nhóm thấp nhất | tập k phủ / cỡ |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for c, r in R.items():
        L.append(f"| {c[0]}{' (gốc J-K)' if c == ORIGINAL else ''} | {c[1]} | {r['n']} | {r['inf']:.1f} | {r['G']['cov']:.3f} / {r['G']['size']:.1f} | "
                 + " / ".join(f"{r['G']['grp'][g]:.2f}" for g in GROUPS)
                 + f" | {r['O']['cov']:.3f} / {r['O']['size']:.1f} | {r['KS']['cov']:.3f} / {r['KS']['size']:.1f} | "
                 + f"{min(r['KS']['grp'].values()):.2f} | {r['kcov']:.2f} / {r['ksize']:.1f} |")
    L.append("\n## Giới hạn\n\n- Dùng đầu ra GNN của tác giả; chỉ điểm `recall_score`, pow 0,3, α 0,10. KS chưa có bảo đảm lý thuyết.\n")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK2_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {verdict}", flush=True)


if __name__ == "__main__":
    main()
