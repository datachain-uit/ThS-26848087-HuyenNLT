"""J-K7 — KN-CP. Giao thức: JK7_PLAN.md. Chạy: python jk7.py [--smoke]"""
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
POW, ALPHA = 0.3, 0.10
SEED = 900 if SMOKE else 20261118
REPS = 2 if SMOKE else jk.REPS
N_CAL, N_TE, N_A = 5600, 400, 2800
KS = jk.KS
BETAS = np.round(np.arange(0.5, 1.0001, 0.005), 4)
KN_VAR = {"KN": 0.05, "KN2": 0.02, "KN0": None}
METH = ("G", "O", "WCP", "MD", "KSU*") + tuple(KN_VAR)
kk_ = np.arange(1, 16, dtype=float)
SCEN = {"S1": np.where(kk_ <= 3, 1.0, 0.0), "S2": np.where(kk_ >= 11, 1.0, 0.0), "S3": (16 - kk_) ** 2, "S4": kk_ ** 2}
SCEN = {k: v / v.sum() for k, v in SCEN.items()}


def qlev(z_sorted, b):
    n = len(z_sorted); r = int(np.ceil(b * (n + 1)))
    return np.inf if (n == 0 or r > n) else z_sorted[r - 1]


def min_cover(ts, src):
    """Ngưỡng nhỏ nhất t để |{v in src: ts[v] <= t}| / |src| >= POW (đúng phép so sánh float của ev)."""
    k = len(src); q = next(q for q in range(1, k + 1) if q / k >= POW)
    return np.sort(ts[src])[q - 1]


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
    KH = {}
    for v, ak in KN_VAR.items():
        if ak is None:
            KH[v] = np.ones((len(K), 15), bool)
        else:
            qk = np.array([cq(SK[kcal][K[kcal] == c], ak) for c in KS])
            M = (1 - P) <= qk[None, :]; M[~M.any(1)] = True; KH[v] = M
    out = {}
    for sname, (fcal, ftest) in SCORES.items():
        TS = [np.asarray(ftest(s[1], jk.PROP, s[0])) for s in samples]
        CS = np.array([fcal(s[1], jk.set_truncate(s[2], s[1], POW), jk.PROP, s[0]) for s in samples])
        MC = np.array([min_cover(TS[i], np.nonzero(samples[i][2])[0]) for i in range(len(K))])
        if SMOKE:  # kiểm tra cài đặt: MC khớp cách tính trực tiếp
            rr = np.random.default_rng(5)
            for i in rr.choice(len(K), 300, replace=False):
                src = np.nonzero(samples[i][2])[0]
                for t in np.quantile(TS[i], [0.01, 0.1, 0.3, 0.6, 0.9]).tolist() + [MC[i]]:
                    direct = len(np.intersect1d(src, np.where(TS[i] <= t)[0])) / len(src) >= POW
                    assert direct == (t >= MC[i]), "MC sai"
        rng = np.random.default_rng(SEED + 1)
        cs = {m: np.zeros(15) for m in METH}; ss = {m: np.zeros(15) for m in METH}; cnt = np.zeros(15)
        for _ in range(REPS):
            p = rng.permutation(rest); cal, te = p[:N_CAL], p[N_CAL:N_CAL + N_TE]
            Kc, Cc = K[cal], CS[cal]
            th = {"G": np.full(len(te), cq(Cc, ALPHA)), "O": np.array([cq(Cc[Kc == k], ALPHA) for k in K[te]]),
                  "WCP": wcp_thresholds(Cc, Kc, P[te]),
                  "MD": np.full(len(te), max(cq(Cc[Kc == c], ALPHA) for c in KS))}
            kidx = np.concatenate([kcal, cal])
            qk2 = np.array([cq(SK[kidx][K[kidx] == c], 0.02) for c in KS])
            KS8 = (1 - P[te]) <= qk2[None, :]
            ts8 = np.array([cq(Cc[Kc == c], 0.08) for c in KS])
            th["KSU*"] = np.array([ts8[r].max() if r.any() else np.inf for r in KS8])
            a, b = cal[:N_A], cal[N_A:]
            srtA = [np.sort(CS[a][K[a] == c]) for c in KS]
            TB = np.array([[qlev(srtA[j], be) for be in BETAS] for j in range(15)])  # (15, nbeta), không giảm theo beta
            for v in KN_VAR:
                def thr(idx):  # (len(idx), nbeta)
                    H = KH[v][idx]
                    return np.where(H[:, :, None], TB[None, :, :], -np.inf).max(1)
                Tb = thr(b)
                ok = Tb >= MC[b][:, None]
                rb = BETAS[ok.argmax(1)]  # luôn có vì beta = 1 cho +inf
                bstar = max(cq(rb[K[b] == c], ALPHA) for c in KS)
                j = np.searchsorted(BETAS, bstar) if np.isfinite(bstar) else len(BETAS) - 1
                th[v] = thr(te)[:, min(j, len(BETAS) - 1)]
            kt = K[te]
            for c in KS:
                cnt[c - 1] += (kt == c).sum()
            for m in METH:
                cov = th[m] >= MC[te]
                size = np.array([(TS[i] <= t).sum() for i, t in zip(te, th[m])])
                np.add.at(cs[m], kt - 1, cov); np.add.at(ss[m], kt - 1, size)
        res = {}
        prior0 = cnt / cnt.sum()
        for m in METH:
            ck, sk = cs[m] / np.maximum(cnt, 1), ss[m] / np.maximum(cnt, 1)
            res[m] = {"cov": float(prior0 @ ck), "size": float(prior0 @ sk), "kmin": float(ck[cnt > 0].min()),
                      **{sc: (float(w @ ck), float(w @ sk)) for sc, w in SCEN.items()}}
        out[sname] = res
        print(f"  {graph} R0 {rz} {sname} xong", flush=True)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if SMOKE:
        run(*CONFIGS[-1]); print("smoke ok (MC khớp)", flush=True); return
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK7_PLAN.md", "jk7.py")}
    print(f"J-K7 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {c: run(*c) for c in CONFIGS}
    combos = [(c, s) for c in CONFIGS for s in SCORES]
    V1a = sum(R[c][s]["KN"]["kmin"] >= 0.88 for c, s in combos)
    V1b = sum(R[c][s]["KN"][sc][0] >= 0.88 for c, s in combos for sc in SCEN)
    r1 = [R[c][s]["KN"]["size"] / R[c][s]["KSU*"]["size"] for c, s in combos]
    r2 = [R[c][s]["KN"]["size"] / R[c][s]["WCP"]["size"] for c, s in combos]
    ok1 = V1a >= 25 and V1b >= 103
    okE1 = np.mean(r1) <= 0.85 and sum(x < 1 for x in r1) >= 20
    okE2 = np.mean(r2) <= 1.15
    v = "GO" if ok1 and okE1 and okE2 else ("MỘT PHẦN" if ok1 and okE1 else "NO-GO")
    L = ["# J-K7 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK7_PLAN.md`.\n",
         f"## Kết luận: **{v}**\n",
         f"- V1: phủ theo k thấp nhất ≥ 0,88 ở {V1a}/27 (cần ≥ 25); ô lệch prior ≥ 0,88 ở {V1b}/108 (cần ≥ 103) → {'đạt' if ok1 else 'trượt'}",
         f"- E1: KN/KSU* trung bình {np.mean(r1):.2f}, nhỏ hơn ở {sum(x < 1 for x in r1)}/27 → {'đạt' if okE1 else 'trượt'}",
         f"- E2: KN/WCP trung bình {np.mean(r2):.2f} → {'đạt' if okE2 else 'trượt'}\n",
         "## Tóm tắt (trung bình 9 cấu hình): phủ / phủ theo k thấp nhất / kích thước\n",
         "| Điểm | " + " | ".join(METH) + " |", "|---|" + "---|" * len(METH)]
    for s in SCORES:
        L.append(f"| {s} | " + " | ".join(
            f"{np.mean([R[c][s][m]['cov'] for c in CONFIGS]):.3f} / {np.mean([R[c][s][m]['kmin'] for c in CONFIGS]):.2f} / {np.mean([R[c][s][m]['size'] for c in CONFIGS]):.1f}"
            for m in METH) + " |")
    L += ["\n## Lệch prior: phủ thấp nhất trên 9 cấu hình (S1 / S2 / S3 / S4)\n", "| Điểm | " + " | ".join(METH) + " |", "|---|" + "---|" * len(METH)]
    for s in SCORES:
        L.append(f"| {s} | " + " | ".join(" / ".join(f"{min(R[c][s][m][sc][0] for c in CONFIGS):.2f}" for sc in SCEN) for m in METH) + " |")
    L += ["\n## Chi tiết: phủ theo k thấp nhất / kích thước\n", "| Đồ thị | R0 | Điểm | " + " | ".join(METH) + " |", "|---|---|---|" + "---|" * len(METH)]
    for c in CONFIGS:
        for s in SCORES:
            L.append(f"| {c[0]} | {c[1]} | {s} | " + " | ".join(f"{R[c][s][m]['kmin']:.2f} / {R[c][s][m]['size']:.1f}" for m in METH) + " |")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK7_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {v}", flush=True)


if __name__ == "__main__":
    main()
