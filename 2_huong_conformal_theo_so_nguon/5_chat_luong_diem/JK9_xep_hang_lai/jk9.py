"""J-K9 — xếp hạng lại: so sánh công bằng. Giao thức: JK9_PLAN.md. Chạy: python jk9.py [--smoke]"""
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
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
for p in ("2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k"):
    sys.path.append(os.path.join(HERE, "..", p))
import jk
from jk5 import cq, wcp_thresholds, CONFIGS
from jk8 import prep, order_full, depth, qneed

SMOKE = "--smoke" in sys.argv
POW, ALPHA, AK, AS = 0.3, 0.10, 0.02, 0.08
SEED = 900 if SMOKE else 20261118
REPS = 2 if SMOKE else jk.REPS
N_CAL, N_TE = 5600, 400
KS = jk.KS
RANKS = ("g", "f", "s", "j")
METH = ("G", "O", "WCP", "MD", "KSU*")
STRUCT = [3, 4, 5, 6, 7, 8]  # cột cấu trúc trong base của prep (bỏ 0..2 = logit, thứ hạng GNN)
kk_ = np.arange(1, 16, dtype=float)
SCEN = {"S1": np.where(kk_ <= 3, 1.0, 0.0), "S2": np.where(kk_ >= 11, 1.0, 0.0), "S3": (16 - kk_) ** 2, "S4": kk_ ** 2}
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
    N = len(samples)
    X = np.array([jk.feats(A, s[0]) for s in samples]); K = np.array([int(s[2].sum()) for s in samples])
    SRC = [np.nonzero(s[2])[0] for s in samples]
    perm = np.random.default_rng(SEED).permutation(N)
    ktr, kcal, rest = perm[:jk.N_KTR], perm[jk.N_KTR:jk.N_K], perm[jk.N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((N, 15)); P[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X)
    SK = 1 - P[np.arange(N), K - 1]
    PR = {i: prep(A, samples[i][0], samples[i][1]) for i in np.concatenate([ktr, rest])}
    y = np.concatenate([np.isin(samples[i][0], SRC[i]).astype(int) for i in ktr])
    Xf = np.vstack([PR[i][0] for i in ktr])
    hgb = dict(max_iter=300, learning_rate=0.05, random_state=0)
    mf = HistGradientBoostingClassifier(**hgb).fit(Xf, y)
    ms = HistGradientBoostingClassifier(**hgb).fit(Xf[:, STRUCT], y)
    DEP = {r: np.zeros(N, int) for r in RANKS}; MI = np.zeros(N, int)
    for i in rest:
        inf = samples[i][0]; base = PR[i][0]; MI[i] = len(inf)
        orders = {"g": order_full(samples[i][1][inf], inf), "f": order_full(mf.predict_proba(base)[:, 1], inf),
                  "s": order_full(ms.predict_proba(base[:, STRUCT])[:, 1], inf),
                  "j": order_full(-base[:, 3] + 1e-6 * base[:, 6], inf)}
        for r in RANKS:
            DEP[r][i] = depth(orders[r], SRC[i], n, K[i])
            if SMOKE and i % 20 == 0:  # quy tắc phủ: depth <= M  <=> top-M chứa >= q nguồn
                for M in (1, 2, 3, 5, 8, 13):
                    if M <= len(inf):
                        assert (DEP[r][i] <= M) == (np.isin(SRC[i], orders[r][:M]).sum() >= qneed(K[i])), "luật phủ sai"
    cs = {(r, m): np.zeros(15) for r in RANKS for m in METH}; ss = {k: np.zeros(15) for k in cs}; cnt = np.zeros(15)
    rng = np.random.default_rng(SEED + 1)
    for _ in range(REPS):
        p = rng.permutation(rest); cal, te = p[:N_CAL], p[N_CAL:N_CAL + N_TE]
        Kc, kt = K[cal], K[te]
        kidx = np.concatenate([kcal, cal])
        qk = np.array([cq(SK[kidx][K[kidx] == c], AK) for c in KS])
        KH = (1 - P[te]) <= qk[None, :]; KH[~KH.any(1)] = True
        np.add.at(cnt, kt - 1, 1)
        for r in RANKS:
            dc = DEP[r][cal].astype(float)
            t10 = np.array([cq(dc[Kc == c], ALPHA) for c in KS]); t08 = np.array([cq(dc[Kc == c], AS) for c in KS])
            th = {"G": np.full(len(te), cq(dc, ALPHA)), "O": t10[kt - 1], "WCP": wcp_thresholds(dc, Kc, P[te]),
                  "MD": np.full(len(te), t10.max()), "KSU*": np.array([t08[h].max() for h in KH])}
            for m in METH:
                M = th[m]; whole = ~np.isfinite(M) | (M > MI[te])
                cov = whole | (DEP[r][te] <= M)
                size = np.where(whole, n, np.where(np.isfinite(M), M, 0))
                np.add.at(cs[(r, m)], kt - 1, cov); np.add.at(ss[(r, m)], kt - 1, size)
    pr0 = cnt / cnt.sum(); res = {}
    for key in cs:
        ck, sk = cs[key] / np.maximum(cnt, 1), ss[key] / np.maximum(cnt, 1)
        res[key] = {"cov": float(pr0 @ ck), "size": float(pr0 @ sk), "kmin": float(ck[cnt > 0].min()),
                    **{sc: float(w @ ck) for sc, w in SCEN.items()}}
    print(f"  {graph} R0 {rz} xong", flush=True)
    return res


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if SMOKE:
        run(*CONFIGS[-1]); print("smoke ok (luật phủ khớp)", flush=True); return
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK9_PLAN.md", "jk9.py")}
    print(f"J-K9 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {c: run(*c) for c in CONFIGS}
    sz = lambda c, r, m: R[c][(r, m)]["size"]
    A_ = sum(sz(c, "f", "WCP") <= 0.5 * sz(c, "g", "WCP") and sz(c, "f", "KSU*") <= 0.5 * sz(c, "g", "KSU*") for c in CONFIGS)
    B_ = float(np.mean([sz(c, "f", "KSU*") / sz(c, "f", "WCP") for c in CONFIGS]))
    C1 = sum(R[c][("f", "KSU*")]["kmin"] >= 0.88 for c in CONFIGS)
    C2 = sum(R[c][("f", "KSU*")][sc] >= 0.88 for c in CONFIGS for sc in SCEN)
    D_ = sum(sz(c, "s", "KSU*") <= 1.1 * sz(c, "f", "KSU*") for c in CONFIGS)
    oA, oB, oC = A_ >= 7, B_ <= 1.15, (C1 >= 8 and C2 >= 34)
    v = "GO" if oA and oB and oC else ("PHÁT HIỆN" if oA and oC else "QUAY VỀ BÀI PHÂN TÍCH")
    L = ["# J-K9 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK9_PLAN.md`.\n",
         f"## Kết luận: **{v}**\n",
         f"- A (f ≤ 0,5 × g cho cả WCP và KSU*): {A_}/9 → {'đạt' if oA else 'trượt'}",
         f"- B (KSU*-f / WCP-f ≤ 1,15): {B_:.2f} → {'đạt' if oB else 'trượt'}",
         f"- C (KSU*-f hợp lệ): phủ theo k {C1}/9, lệch prior {C2}/36 → {'đạt' if oC else 'trượt'}",
         f"- D (đọc kèm): KSU*-s ≤ 1,1 × KSU*-f ở {D_}/9 → {'GNN không thêm giá trị so với cấu trúc' if D_ >= 7 else 'GNN có thêm giá trị'}\n",
         "## Trung bình 9 cấu hình: phủ theo k thấp nhất / kích thước\n", "| Xếp hạng | " + " | ".join(METH) + " |", "|---|" + "---|" * len(METH)]
    for r in RANKS:
        L.append(f"| {r} | " + " | ".join(f"{np.mean([R[c][(r, m)]['kmin'] for c in CONFIGS]):.3f} / {np.mean([sz(c, r, m) for c in CONFIGS]):.1f}" for m in METH) + " |")
    L += ["\n## Lệch prior: phủ thấp nhất trên 9 cấu hình (S1 / S2 / S3 / S4)\n", "| Xếp hạng | " + " | ".join(METH) + " |", "|---|" + "---|" * len(METH)]
    for r in RANKS:
        L.append(f"| {r} | " + " | ".join(" / ".join(f"{min(R[c][(r, m)][sc] for c in CONFIGS):.2f}" for sc in SCEN) for m in METH) + " |")
    L += ["\n## Chi tiết kích thước (phủ theo k thấp nhất trong ngoặc)\n", "| Đồ thị | R0 | " + " | ".join(f"{r}-{m}" for r in RANKS for m in ("G", "O", "WCP", "KSU*")) + " |",
          "|---|---|" + "---|" * 16]
    for c in CONFIGS:
        L.append(f"| {c[0]} | {c[1]} | " + " | ".join(f"{sz(c, r, m):.1f} ({R[c][(r, m)]['kmin']:.2f})" for r in RANKS for m in ("G", "O", "WCP", "KSU*")) + " |")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK9_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {v}", flush=True)


if __name__ == "__main__":
    main()
