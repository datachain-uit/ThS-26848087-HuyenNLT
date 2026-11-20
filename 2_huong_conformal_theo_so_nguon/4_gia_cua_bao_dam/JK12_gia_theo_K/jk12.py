"""J-K12 — A: giá ~ |K̂| (khóa trước); B: bảng chính dữ liệu tác giả kèm CI. Giao thức: JK12_PLAN.md."""
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
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
for p in ("2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK11_do_thi_lon", "2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k"):
    sys.path.append(os.path.join(HERE, "..", p))
import jk
import jk11
from jk5 import cq, wcp_thresholds, SCORES, CONFIGS
from jk7 import min_cover

SMOKE = "--smoke" in sys.argv
POW, ALPHA, AK, AS = 0.3, 0.10, 0.02, 0.08
KS = list(range(1, 16))
SET_A = [(g, m, t) for g in ("lfr10k_mu0.1_1", "lfr10k_mu0.3_1") for t in (25, 100, 300) for m in ("SI", "IC", "SIR")]
METH = ("G", "O", "WCP", "MD", "KSU*")


def part_b(graph, rz, reps, seed):
    exp = f"SIR_nsrc1-15_Rzero{rz}_gamma0.1-0.4_ls8000_nf16"
    d = pickle.load(open(os.path.join(jk.CN, "SD-STGCN", "output", "test_res", graph, exp, "res.pickle"), "rb"))
    n = np.asarray(d["predictions"][0][0]).shape[0]
    G = nx.read_edgelist(os.path.join(jk.CN, "SD-STGCN", "dataset", graph, "data", "graph", graph + ".edgelist"), nodetype=int)
    G.add_nodes_from(range(n))
    A = sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=float))
    smp = [(np.nonzero(np.asarray(d["inputs"][b][j]))[0], np.asarray(d["predictions"][b][j])[:, 1], np.asarray(d["ground_truth"][b][j]))
           for b in range(len(d["inputs"])) for j in range(len(d["inputs"][b]))]
    N = len(smp); X = np.array([jk.feats(A, s[0]) for s in smp]); K = np.array([int(s[2].sum()) for s in smp])
    perm = np.random.default_rng(seed).permutation(N)
    ktr, kcal, rest = perm[:jk.N_KTR], perm[jk.N_KTR:jk.N_K], perm[jk.N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((N, 15)); P[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X)
    SK = 1 - P[np.arange(N), K - 1]
    out = {}
    for sname, (fcal, ftest) in SCORES.items():
        TS = {i: np.asarray(ftest(smp[i][1], jk.PROP, smp[i][0])) for i in rest}
        MC = {i: min_cover(TS[i], np.nonzero(smp[i][2])[0]) for i in rest}
        CS = np.full(N, np.nan)
        for i in rest:
            CS[i] = fcal(smp[i][1], jk.set_truncate(smp[i][2], smp[i][1], POW), jk.PROP, smp[i][0])
        cs = {m: np.zeros(15) for m in METH}; cnt = np.zeros(15); rsz = {m: [] for m in METH}; ssum = {m: 0.0 for m in METH}; nt = 0
        rng = np.random.default_rng(seed + 1)
        for _ in range(reps):
            p = rng.permutation(rest); cal, te = p[:jk.N_CAL], p[jk.N_CAL:jk.N_CAL + jk.N_TE]
            Kc, Cc, kt = K[cal], CS[cal], K[te]
            kidx = np.concatenate([kcal, cal])
            qk = np.array([cq(SK[kidx][K[kidx] == c], AK) for c in KS])
            KH = (1 - P[te]) <= qk[None, :]; KH[~KH.any(1)] = True
            t10 = np.array([cq(Cc[Kc == c], ALPHA) for c in KS]); t08 = np.array([cq(Cc[Kc == c], AS) for c in KS])
            th = {"G": np.full(len(te), cq(Cc, ALPHA)), "O": t10[kt - 1], "WCP": wcp_thresholds(Cc, Kc, P[te]),
                  "MD": np.full(len(te), t10.max()), "KSU*": np.array([t08[h].max() for h in KH])}
            np.add.at(cnt, kt - 1, 1); nt += len(te)
            for m in METH:
                cov = np.array([t >= MC[i] for i, t in zip(te, th[m])])
                sz = np.array([(TS[i] <= t).sum() for i, t in zip(te, th[m])])
                np.add.at(cs[m], kt - 1, cov); rsz[m].append(sz.mean()); ssum[m] += sz.sum()
        res = {}
        for m in METH:
            ck = cs[m] / np.maximum(cnt, 1); j = int(np.argmin(np.where(cnt > 0, ck, np.inf))); rs = np.array(rsz[m])
            res[m] = dict(cov=float(cs[m].sum() / nt), kmin=float(ck[j]), lo=jk11.wilson_lo(ck[j], cnt[j]), karg=j + 1,
                          size=ssum[m] / nt, hw=float(1.96 * rs.std(ddof=1) / np.sqrt(len(rs))) if len(rs) > 1 else np.nan)
        out[sname] = res
    print(f"  B: {graph} R0 {rz} xong", flush=True)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cache = {}
    if SMOKE:
        jk11.run(100, "lfr10k_mu0.3_1", "SI", 25, cache)
        part_b(*CONFIGS[-1], reps=2, seed=900)
        print("smoke ok", flush=True); return
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK12_PLAN.md", "jk12.py")}
    print(f"J-K12 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    RA = {s: jk11.run(100 + i, *s, cache) for i, s in enumerate(SET_A)}
    x = np.array([RA[s]["_kset"] for s in SET_A])
    y = np.array([RA[s]["KSU*"]["size"] / RA[s]["WCP"]["size"] for s in SET_A])
    yo = np.array([RA[s]["KSU*"]["size"] / RA[s]["O"]["size"] for s in SET_A])
    rho = spearmanr(x, y).correlation; rho_o = spearmanr(x, yo).correlation
    pr = np.random.default_rng(7)
    perm = np.array([spearmanr(x, pr.permutation(y)).correlation for _ in range(10000)])
    pval = float((np.sum(perm >= rho) + 1) / (len(perm) + 1))
    H1 = rho >= 0.6 and pval < 0.05
    H2n = sum(RA[s]["KSU*"]["kmin"] >= 0.88 for s in SET_A); H2 = H2n >= 17
    vA = "XÁC NHẬN: giá tăng theo |K̂|" if H1 and H2 else ("KHÔNG XÁC NHẬN" if H2 else "KSU* TRƯỢT — XEM LẠI")
    RB = {c: part_b(*c, reps=jk.REPS, seed=20261118) for c in CONFIGS}
    L = ["# J-K12 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK12_PLAN.md`.\n",
         f"## Phần A — kết luận: **{vA}**\n",
         f"- H1: Spearman ρ(|K̂|, KSU*/WCP) = {rho:.2f}, p hoán vị một phía = {pval:.4f} → {'đạt' if H1 else 'trượt'}",
         f"- H2: KSU* phủ theo k ≥ 0,88 ở {H2n}/18 → {'đạt' if H2 else 'trượt'}",
         f"- Mô tả: ρ(|K̂|, KSU*/O) = {rho_o:.2f}\n",
         "| Đồ thị | Mô hình | |I| | |K̂| | KSU*/WCP | KSU*/O | phủ k thấp nhất G / WCP / KSU* [cận dưới] |", "|---|---|---|---|---|---|---|"]
    for s, xi, yi, yoi in zip(SET_A, x, y, yo):
        r = RA[s]
        L.append(f"| {s[0]} | {s[1]} | {s[2]} | {xi:.1f} | {yi:.2f} | {yoi:.2f} | {r['G']['kmin']:.2f} / {r['WCP']['kmin']:.2f} / {r['KSU*']['kmin']:.2f} [{r['KSU*']['kmin_lo']:.2f}] |")
    L += ["\n## Phần B — bảng chính dữ liệu tác giả (mô tả)\n",
          "Mỗi ô: phủ biên; phủ theo k thấp nhất [cận dưới Wilson 95%] (k xấu nhất); kích thước ± nửa khoảng 95%.\n",
          "| Đồ thị | R0 | Điểm | " + " | ".join(METH) + " |", "|---|---|---|" + "---|" * len(METH)]
    for c in CONFIGS:
        for sname in SCORES:
            L.append(f"| {c[0]} | {c[1]} | {sname} | " + " | ".join(
                f"{RB[c][sname][m]['cov']:.3f}; {RB[c][sname][m]['kmin']:.2f} [{RB[c][sname][m]['lo']:.2f}] (k={RB[c][sname][m]['karg']}); {RB[c][sname][m]['size']:.1f} ± {RB[c][sname][m]['hw']:.1f}"
                for m in METH) + " |")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK12_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {vA}", flush=True)


if __name__ == "__main__":
    main()
