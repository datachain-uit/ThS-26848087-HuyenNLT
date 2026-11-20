"""J-K — pilot hiệu chỉnh tập nguồn conformal (Jian et al.) có điều kiện theo tập dự đoán k. Giao thức: JK_PLAN.md.
Chạy: python jk.py  (dùng .venv của H0; vài phút)"""
import _venv; _venv.ensure()
import datetime as dt
import hashlib
import os
import pickle
import platform
import sys
import types

import numpy as np
import networkx as nx
import scipy.sparse as sp
from scipy.sparse.csgraph import shortest_path, connected_components
from sklearn.ensemble import RandomForestClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
CN = os.path.join(HERE, "..", "..", "..", "2_huong_conformal_theo_so_nguon", "0_tai_lap_Jian2026", "cnsd")
EXP = "SIR_nsrc1-15_Rzero1-15_gamma0.1-0.4_ls8000_nf16"
for d in (CN, os.path.join(CN, "SD-STGCN"), os.path.join(CN, "SD-STGCN", "data_loader"), os.path.join(CN, "SD-STGCN", "utils"), os.path.join(CN, "DSI", "src")):
    sys.path.append(d)
_tf = types.ModuleType("tensorflow"); _tf.train = types.SimpleNamespace(); sys.modules.setdefault("tensorflow", _tf)
from utils.score_convert import recall_score, recall_score_gtunknown, set_truncate  # hàm điểm của tác giả
from utils.functions import cpquantile

sys.path.append(os.path.join(HERE, "..", "..", "..", "1_huong_cong_dong", "5_E0_ho_so_cong_dong_da_thang"))
import e0  # kcenter_seq

SEED = 20261118
ALPHA, ALPHA_K, POW, PROP = 0.10, 0.05, 0.3, "SIR"
N_K, N_KTR, REPS, N_CAL, N_TE = 2000, 1400, 50, 5600, 400
GROUPS = [(1, 3), (4, 7), (8, 11), (12, 15)]
KS = list(range(1, 16))
RHOS, KMAX = [1, 2, 3, 4, 5, 6], 15


def feats(A, inf):
    A_I = A[inf][:, inf].tocsr()
    ncomp, _ = connected_components(A_I, directed=False)
    DI = shortest_path(A_I, method="D", unweighted=True)
    _, radii = e0.kcenter_seq(DI, KMAX)
    f = [int(ncomp)]
    for r in RHOS:
        ok = [i + 1 for i, x in enumerate(radii) if x <= r]
        f.append(ok[0] if ok else KMAX)
    m = len(inf)
    ecc = np.where(np.isfinite(DI), DI, -1).max(axis=1)
    dv = DI[np.triu_indices(m, 1)]; dv = dv[np.isfinite(dv)]
    q = np.percentile(dv, [25, 50, 75, 90]) if dv.size else np.zeros(4)
    degG = np.asarray(A[inf].sum(axis=1)).ravel(); degI = np.asarray(A_I.sum(axis=1)).ravel()
    ip, ix = A_I.indptr, A_I.indices
    emin = sum(1 for i in range(m) if ip[i] == ip[i + 1] or ecc[i] < ecc[ix[ip[i]:ip[i + 1]]].min())
    f += [ecc.max(), ecc.min(), *q, degG.sum() - degI.sum(), degG.mean(), degG.max(), degI.mean(), (degI == 1).mean(), emin]
    return np.array(f, float)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK_PLAN.md", "jk.py")}
    print(f"J-K start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    G = nx.read_edgelist(os.path.join(CN, "SD-STGCN", "dataset", "highSchool", "data", "graph", "highSchool.edgelist"), nodetype=int)
    n = 774
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=float))
    d = pickle.load(open(os.path.join(CN, "SD-STGCN", "output", "test_res", "highSchool", EXP, "res.pickle"), "rb"))
    X, K, CS, TS = [], [], [], []
    for b in range(len(d["inputs"])):
        for j in range(len(d["inputs"][b])):
            inp = np.asarray(d["inputs"][b][j]); pr = np.asarray(d["predictions"][b][j])[:, 1]; gt = np.asarray(d["ground_truth"][b][j])
            inf = np.nonzero(inp)[0]
            X.append(feats(A, inf)); K.append(int(gt.sum()))
            CS.append(recall_score(pr, set_truncate(gt, pr, POW), PROP, inf))
            TS.append((np.asarray(recall_score_gtunknown(pr, PROP, inf)), gt))
    X, K, CS = np.array(X), np.array(K), np.array(CS)
    print(f"features/scores done {dt.datetime.now():%H:%M:%S}, n={len(K)}", flush=True)
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(K))
    ktr, kcal, rest = perm[:N_KTR], perm[N_KTR:N_K], perm[N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((len(K), len(KS)))
    P[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X)
    sc = 1 - P[kcal, [KS.index(k) for k in K[kcal]]]
    nk = len(sc); qk = np.quantile(sc, min(1, np.ceil((nk + 1) * (1 - ALPHA_K)) / nk), method="higher")
    KSET = P >= 1 - qk
    KHAT = np.array(KS)[P.argmax(1)]
    kcov = KSET[rest, [KS.index(k) for k in K[rest]]].mean(); ksize = KSET[rest].sum(1).mean()

    def thr(pool):
        return cpquantile(CS[pool], (1 - ALPHA) * (1 + 1 / len(pool)))

    def evalset(i, t):
        s, gt = TS[i]
        pred = np.where(s <= t)[0]
        src = np.nonzero(gt)[0]
        return (len(np.intersect1d(src, pred)) / len(src) >= POW), len(pred)

    meth = ["G", "O", "KS", "KP"]
    acc = {m: {"cov": [], "size": [], "grp": {g: [] for g in GROUPS}} for m in meth}
    mis = {name: {"cov": [], "size": []} for name in ("G_over", "G_under", "G_broad", "KS_broad")}
    for r in range(REPS):
        p = rng.permutation(rest)
        cal, te = p[:N_CAL], p[N_CAL:N_CAL + N_TE]
        tG = thr(cal)
        tk = {k: thr(cal[K[cal] == k]) for k in KS}
        cache = {}
        res = {m: [] for m in meth}
        for i in te:
            ks = tuple(np.array(KS)[KSET[i]])
            if ks not in cache:
                pool = cal[np.isin(K[cal], ks)]
                cache[ks] = thr(pool) if len(pool) else tG
            for m, t in (("G", tG), ("O", tk[K[i]]), ("KS", cache[ks]), ("KP", tk[KHAT[i]])):
                res[m].append((K[i],) + evalset(i, t))
        for m in meth:
            arr = np.array(res[m], float)
            acc[m]["cov"].append(arr[:, 1].mean()); acc[m]["size"].append(arr[:, 2].mean())
            for g in GROUPS:
                sel = (arr[:, 0] >= g[0]) & (arr[:, 0] <= g[1])
                acc[m]["grp"][g].append(arr[sel, 1].mean())
        # kịch bản lệch prior: kiểm trên k 5..10
        te5 = te[(K[te] >= 5) & (K[te] <= 10)]
        for name, t_fn in (("G_over", lambda i: thr(cal[K[cal] >= 10])), ("G_under", lambda i: thr(cal[K[cal] <= 5])),
                           ("G_broad", lambda i: tG), ("KS_broad", lambda i: cache.get(tuple(np.array(KS)[KSET[i]]), tG))):
            out = [evalset(i, t_fn(i)) for i in te5]
            mis[name]["cov"].append(np.mean([o[0] for o in out])); mis[name]["size"].append(np.mean([o[1] for o in out]))
        print(f"rep {r + 1}/{REPS}", flush=True)

    ms = lambda v: f"{np.mean(v):.3f} ± {np.std(v):.3f}"
    covG = np.mean(acc["G"]["cov"])
    minG = min(np.mean(acc["G"]["grp"][g]) for g in GROUPS)
    minKS = min(np.mean(acc["KS"]["grp"][g]) for g in GROUPS)
    ratio = np.mean(acc["KS"]["size"]) / np.mean(acc["G"]["size"])
    S, M2, M1, M3 = 0.87 <= covG <= 0.93, minG < 0.85, minKS >= 0.85, ratio <= 1.2
    if not S:
        verdict = "KIỂM TRA CÀI ĐẶT (S trượt) — không diễn giải"
    elif not M2:
        verdict = "NO-GO (M2: G đã phủ đủ theo từng nhóm k — hiệu chỉnh có điều kiện không cần thiết)"
    elif M1 and M3:
        verdict = "GO"
    else:
        verdict = "NO-GO (M1 hoặc M3 trượt)"
    L = ["# J-K — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK_PLAN.md`.\n",
         f"## Kết luận: **{verdict}**\n",
         f"- S: độ phủ G = {covG:.3f} (cần [0,87; 0,93]) → {'đạt' if S else 'trượt'}",
         f"- M2: độ phủ nhóm thấp nhất của G = {minG:.3f} (cần < 0,85) → {'đạt' if M2 else 'trượt'}",
         f"- M1: độ phủ nhóm thấp nhất của KS = {minKS:.3f} (cần ≥ 0,85) → {'đạt' if M1 else 'trượt'}",
         f"- M3: kích thước KS / G = {ratio:.2f} (cần ≤ 1,2) → {'đạt' if M3 else 'trượt'}\n",
         f"Tập dự đoán k (α_k = 0,05) trên 6000 mẫu: độ phủ {kcov:.3f}, kích thước trung bình {ksize:.2f} giá trị (trên 15).\n",
         "## Độ phủ (recall ≥ 0,3) và kích thước tập nguồn, α = 0,10, 50 lần lặp\n",
         "| Phương pháp | Độ phủ | Kích thước | phủ k 1–3 | phủ k 4–7 | phủ k 8–11 | phủ k 12–15 |", "|---|---|---|---|---|---|---|"]
    for m in meth:
        L.append(f"| {m} | {ms(acc[m]['cov'])} | {ms(acc[m]['size'])} | " + " | ".join(f"{np.mean(acc[m]['grp'][g]):.3f}" for g in GROUPS) + " |")
    L += ["\n## Kịch bản lệch prior số nguồn (kiểm trên k 5–10)\n",
          "| Hiệu chỉnh | Độ phủ | Kích thước |", "|---|---|---|"]
    lab = {"G_over": "G, chỉ k 10–15 (đoán thừa)", "G_under": "G, chỉ k 1–5 (đoán thiếu)", "G_broad": "G, đủ k 1–15", "KS_broad": "KS, đủ k 1–15"}
    for name, v in mis.items():
        L.append(f"| {lab[name]} | {ms(v['cov'])} | {ms(v['size'])} |")
    L.append("\n## Giới hạn\n\n- Một đồ thị, một cấu hình SIR, mô hình GNN của tác giả. KS làm yếu giả định trao đổi được; chưa có bảo đảm lý thuyết.\n")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {verdict}", flush=True)


if __name__ == "__main__":
    main()
