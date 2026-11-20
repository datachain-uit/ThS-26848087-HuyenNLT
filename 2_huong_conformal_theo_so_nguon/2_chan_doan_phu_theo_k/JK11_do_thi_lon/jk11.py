"""J-K11 — đồ thị 10 000 nút + khoảng tin cậy. Giao thức: JK11_PLAN.md. Chạy: python jk11.py [--smoke]"""
import _venv; _venv.ensure()
import datetime as dt
import hashlib
import os
import platform
import sys

import numpy as np
import networkx as nx
import scipy.sparse as sp
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
for p in ("2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k", "2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK2_lech_mo_hinh", "1_huong_cong_dong/5_E0_ho_so_cong_dong_da_thang"):
    sys.path.append(os.path.join(HERE, "..", p))
import jk
import e0
import pk2
from jk5 import cq, wcp_thresholds
from jk8 import prep, order_full, depth, qneed

SMOKE = "--smoke" in sys.argv
POW, ALPHA, AK, AS = 0.3, 0.10, 0.02, 0.08
SEED0 = 900 if SMOKE else 20261118
REPS = 2 if SMOKE else 50
NS = 600 if SMOKE else 8000
N_KTR, N_K, N_CAL, N_TE = (100, 150, 400, 50) if SMOKE else (1400, 2000, 5600, 400)
KS = list(range(1, 16))
MODELS = {"SI": e0.si_fixed, "IC": pk2.ic_fixed, "SIR": pk2.sir_fixed}
SETTINGS = [(g, m, t) for g in ("lfr10k_mu0.1_0", "lfr10k_mu0.3_0") for t in (50, 200) for m in MODELS]
METH = ("G", "O", "WCP", "MD", "KSU*")
STRUCT = [3, 4, 5, 6, 7, 8]
DATA = os.path.join(HERE, "..", "..", "..", "1_huong_cong_dong", "4_P6F_hieu_chinh_ti_le_nhiem", "data")
kk_ = np.arange(1, 16, dtype=float)
SCEN = {"S1": np.where(kk_ <= 3, 1.0, 0.0), "S2": np.where(kk_ >= 11, 1.0, 0.0), "S3": (16 - kk_) ** 2, "S4": kk_ ** 2}
SCEN = {k: v / v.sum() for k, v in SCEN.items()}


def wilson_lo(p, n, z=1.96):
    if n == 0:
        return np.nan
    c = (p + z * z / (2 * n) - z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)
    return float(c)


def load(gid):
    G = nx.read_edgelist(os.path.join(DATA, f"{gid}_edges.txt"), nodetype=int)
    n = G.number_of_nodes(); G.add_nodes_from(range(n))
    return n, sp.csr_matrix(nx.to_scipy_sparse_array(G, nodelist=range(n), format="csr", dtype=float))


def simulate(A, n, sim, rng, target):
    out = []
    while len(out) < NS:
        k = int(rng.integers(1, 16)); src = rng.choice(n, k, replace=False)
        inf = sim(A, src, rng, target)
        if inf is None or len(inf) != target:
            continue
        out.append((np.asarray(inf, int), np.asarray(src, int)))
    return out


def run(si, gid, mname, target, cache):
    if gid not in cache:
        cache[gid] = load(gid)
    n, A = cache[gid]
    rng = np.random.default_rng(SEED0 + si)
    S = simulate(A, n, MODELS[mname], rng, target)
    if SMOKE:
        for inf, src in S[:50]:
            assert len(inf) == target and np.isin(src, inf).all(), "mô phỏng sai"
    N = len(S); K = np.array([len(s[1]) for s in S])
    X = np.array([jk.feats(A, s[0]) for s in S])
    perm = rng.permutation(N)
    ktr, kcal, rest = perm[:N_KTR], perm[N_KTR:N_K], perm[N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((N, 15)); P[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(X)
    SK = 1 - P[np.arange(N), K - 1]
    half = np.full(n, 0.5)
    PR = {i: prep(A, S[i][0], half)[0][:, STRUCT] for i in np.concatenate([ktr, rest])}
    y = np.concatenate([np.isin(S[i][0], S[i][1]).astype(int) for i in ktr])
    ms = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=0).fit(np.vstack([PR[i] for i in ktr]), y)
    DEP = np.zeros(N, int); MI = np.zeros(N, int)
    for i in rest:
        inf = S[i][0]; o = order_full(ms.predict_proba(PR[i])[:, 1], inf); MI[i] = len(inf)
        DEP[i] = depth(o, S[i][1], n, K[i])
        if SMOKE:
            for M in (1, 2, 3, 5, 8, 13):
                assert (DEP[i] <= M) == (np.isin(S[i][1], o[:M]).sum() >= qneed(K[i])), "luật phủ sai"
    cs = {m: np.zeros(15) for m in METH}; ss = {m: np.zeros(15) for m in METH}; cnt = np.zeros(15)
    rep_size = {m: [] for m in METH}
    r2 = np.random.default_rng(SEED0 + 100 + si)
    for _ in range(REPS):
        p = r2.permutation(rest); cal, te = p[:N_CAL], p[N_CAL:N_CAL + N_TE]
        Kc, kt = K[cal], K[te]
        kidx = np.concatenate([kcal, cal])
        qk = np.array([cq(SK[kidx][K[kidx] == c], AK) for c in KS])
        KH = (1 - P[te]) <= qk[None, :]; KH[~KH.any(1)] = True
        np.add.at(cnt, kt - 1, 1)
        dc = DEP[cal].astype(float)
        t10 = np.array([cq(dc[Kc == c], ALPHA) for c in KS]); t08 = np.array([cq(dc[Kc == c], AS) for c in KS])
        th = {"G": np.full(len(te), cq(dc, ALPHA)), "O": t10[kt - 1], "WCP": wcp_thresholds(dc, Kc, P[te]),
              "MD": np.full(len(te), t10.max()), "KSU*": np.array([t08[h].max() for h in KH])}
        for m in METH:
            M = th[m]; whole = ~np.isfinite(M) | (M > MI[te])
            sz = np.where(whole, n, np.where(np.isfinite(M), M, 0))
            np.add.at(cs[m], kt - 1, whole | (DEP[te] <= M)); np.add.at(ss[m], kt - 1, sz)
            rep_size[m].append(sz.mean())
    pr0 = cnt / cnt.sum(); res = {}
    for m in METH:
        ck, sk = cs[m] / np.maximum(cnt, 1), ss[m] / np.maximum(cnt, 1)
        j = int(np.argmin(np.where(cnt > 0, ck, np.inf)))
        rs = np.array(rep_size[m])
        res[m] = {"size": float(pr0 @ sk), "size_hw": float(1.96 * rs.std(ddof=1) / np.sqrt(len(rs))) if len(rs) > 1 else np.nan,
                  "kmin": float(ck[j]), "kmin_lo": wilson_lo(ck[j], cnt[j]), "kargmin": j + 1,
                  **{sc: float(w @ ck) for sc, w in SCEN.items()}}
    res["_kset"] = float(KH.sum(1).mean())
    print(f"  {gid} {mname} I={target} xong", flush=True)
    return res


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    cache = {}
    if SMOKE:
        run(0, "lfr10k_mu0.3_0", "IC", 50, cache); print("smoke ok (mô phỏng và luật phủ khớp)", flush=True); return
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK11_PLAN.md", "jk11.py")}
    print(f"J-K11 start {dt.datetime.now():%H:%M:%S} SHA {sha}", flush=True)
    R = {s: run(i, *s, cache) for i, s in enumerate(SETTINGS)}
    Q1 = sum(R[s]["G"]["kmin"] < 0.85 for s in SETTINGS)
    Q2 = sum(R[s]["WCP"]["kmin"] < 0.85 for s in SETTINGS)
    Q3a = sum(R[s]["KSU*"]["kmin"] >= 0.88 for s in SETTINGS)
    Q3b = sum(R[s]["KSU*"][sc] >= 0.88 for s in SETTINGS for sc in SCEN)
    o1, o2, o3 = Q1 >= 6, Q2 >= 6, (Q3a >= 11 and Q3b >= 46)
    v = "TỔNG QUÁT HÓA SANG ĐỒ THỊ LỚN" if o1 and o2 and o3 else ("MỘT PHẦN" if o3 else "KSU* TRƯỢT — XEM LẠI")
    rw = [R[s]["KSU*"]["size"] / R[s]["WCP"]["size"] for s in SETTINGS]; ro = [R[s]["KSU*"]["size"] / R[s]["O"]["size"] for s in SETTINGS]
    L = ["# J-K11 — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Giao thức: `JK11_PLAN.md`.\n",
         f"## Kết luận: **{v}**\n",
         f"- Q1 (G phủ theo k < 0,85): {Q1}/12 → {'đạt' if o1 else 'trượt'}",
         f"- Q2 (WCP phủ theo k < 0,85): {Q2}/12 → {'đạt' if o2 else 'trượt'}",
         f"- Q3 (KSU* hợp lệ): phủ theo k {Q3a}/12, lệch prior {Q3b}/48 → {'đạt' if o3 else 'trượt'}",
         f"- Q4 (mô tả): KSU*/WCP {np.mean(rw):.2f} ({min(rw):.2f}–{max(rw):.2f}); KSU*/O {np.mean(ro):.2f} ({min(ro):.2f}–{max(ro):.2f})\n",
         "## Chi tiết: phủ theo k thấp nhất [cận dưới Wilson 95%] (k xấu nhất) / kích thước ± nửa khoảng 95%\n",
         "| Đồ thị | Mô hình | |I| | |K̂| | " + " | ".join(METH) + " |", "|---|---|---|---|" + "---|" * len(METH)]
    for s in SETTINGS:
        L.append(f"| {s[0]} | {s[1]} | {s[2]} | {R[s]['_kset']:.1f} | " + " | ".join(
            f"{R[s][m]['kmin']:.2f} [{R[s][m]['kmin_lo']:.2f}] (k={R[s][m]['kargmin']}) / {R[s][m]['size']:.1f} ± {R[s][m]['size_hw']:.1f}" for m in METH) + " |")
    L += ["\n## Lệch prior: phủ (S1 / S2 / S3 / S4)\n", "| Đồ thị | Mô hình | |I| | " + " | ".join(METH) + " |", "|---|---|---|" + "---|" * len(METH)]
    for s in SETTINGS:
        L.append(f"| {s[0]} | {s[1]} | {s[2]} | " + " | ".join(" / ".join(f"{R[s][m][sc]:.2f}" for sc in SCEN) for m in METH) + " |")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    open(os.path.join(HERE, "results", "JK11_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print(f"done: {v}", flush=True)


if __name__ == "__main__":
    main()
