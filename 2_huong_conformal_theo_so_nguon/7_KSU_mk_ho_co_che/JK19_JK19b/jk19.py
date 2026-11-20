"""J-K19 — hiệu chỉnh trên hỗn hợp cơ chế, hợp lệ theo (cơ chế, k). Giao thức: JK19_PLAN.md. Chạy: python jk19.py [--smoke]"""
import _venv; _venv.ensure()
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.append(os.path.join(B, "2_huong_conformal_theo_so_nguon/6_do_ben/JK17_18_lech_mo_hinh_thieu_nut"))
import datetime as dt, hashlib, pickle, platform, time
import numpy as np
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
import jk17  # tái dùng mô phỏng, load đồ thị, đặc trưng (đã kiểm ở J-K17)
from jk17 import simulate, load, TooHard, prep, order_full, depth, qneed, cq, wilson_lo, STRUCT, jk
os.chdir(HERE)

SMOKE = "--smoke" in sys.argv
ALPHA, AG, AS = 0.10, 0.02, 0.08
REPS = 2 if SMOKE else 50
N_CALD, N_TEST = (600, 200) if SMOKE else (8000, 4000)
N_KTR, N_K, N_CAL, N_TE = (150, 250, 250, 100) if SMOKE else (1400, 2000, 5600, 400)
FAM = ("SI", "IC", "SIR"); OUTF = ("SIR-nhanh", "SIR-dai"); TESTS = FAM + OUTF
NG = 15 * len(FAM)
METH = ("G", "O", "WCP-mk", "MD-m", "MD-mk", "KSU*-SIR", "KSU*-k", "KSU*-mk")
GR = ("lfr10k_mu0.1_0", "cora_ml")
RUNS = [(g, t, s) for s in (0, 1, 2) for g in GR for t in (50, 200)]
OUT = os.path.join(HERE, "results", "JK19_smoke.pkl" if SMOKE else "JK19_raw.pkl")


def wcp_g(calv, calg, W, ng):
    cand = np.unique(calv); M = np.zeros((ng, len(cand)))
    for g in range(ng):
        s = np.sort(calv[calg == g])
        if len(s):
            M[g] = np.searchsorted(s, cand, side="right") / (len(s) + 1)
    ok = (W @ M) >= 1 - ALPHA
    return np.where(ok.any(1), cand[ok.argmax(1)], np.inf)


def run(g, t, s):
    seed = 20261120 + 1000 * s + 100 * GR.index(g) + t
    n, A = load(g)
    S = {m: simulate(A, n, m, np.random.default_rng(seed + 11 * i), t, N_CALD) for i, m in enumerate(FAM)}
    T = {m: simulate(A, n, m, np.random.default_rng(seed + 500 + 11 * i), t, N_TEST) for i, m in enumerate(TESTS)}
    rng = np.random.default_rng(seed + 999)
    # gộp dữ liệu hiệu chỉnh; nhóm g = chỉ số cơ chế*15 + k-1
    smp, grp, part = [], [], []
    for i, m in enumerate(FAM):
        p = rng.permutation(N_CALD)
        lab = np.empty(N_CALD, object); lab[p[:N_KTR]] = "ktr"; lab[p[N_KTR:N_K]] = "kcal"; lab[p[N_K:]] = "rest"
        for j, (inf, src) in enumerate(S[m]):
            smp.append((inf, src)); grp.append(i * 15 + len(src) - 1); part.append(lab[j])
    grp = np.array(grp); part = np.array(part); mech = grp // 15; K = grp % 15 + 1
    X = np.array([jk.feats(A, x[0]) for x in smp])
    ktr = np.flatnonzero(part == "ktr"); kcal = np.flatnonzero(part == "kcal"); rest = np.flatnonzero(part == "rest")
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], grp[ktr])
    P = np.zeros((len(smp), NG)); P[:, rf.classes_] = rf.predict_proba(X)
    half = np.full(n, 0.5)
    F = {i: prep(A, smp[i][0], half)[0][:, STRUCT] for i in np.concatenate([ktr, rest])}
    y = np.concatenate([np.isin(smp[i][0], smp[i][1]).astype(int) for i in ktr])
    hgb = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=0).fit(np.vstack([F[i] for i in ktr]), y)
    D = np.zeros(len(smp), int); MI = np.zeros(len(smp), int)
    for i in rest:
        D[i] = depth(order_full(hgb.predict_proba(F[i])[:, 1], smp[i][0]), smp[i][1], n, K[i]); MI[i] = len(smp[i][0])
    TD = {}
    for m in TESTS:
        XT = np.array([jk.feats(A, x[0]) for x in T[m]]); PT = np.zeros((len(T[m]), NG)); PT[:, rf.classes_] = rf.predict_proba(XT)
        dt_ = np.zeros(len(T[m]), int); mt = np.zeros(len(T[m]), int)
        for i, (inf, src) in enumerate(T[m]):
            o = order_full(hgb.predict_proba(prep(A, inf, half)[0][:, STRUCT])[:, 1], inf)
            dt_[i] = depth(o, src, n, len(src)); mt[i] = len(inf)
            if SMOKE and i % 40 == 0:
                for M_ in (1, 3, 8):
                    if M_ <= len(o):
                        assert (dt_[i] <= M_) == (np.isin(src, o[:M_]).sum() >= qneed(len(src))), "luật phủ sai"
        TD[m] = (dt_, mt, np.array([len(x[1]) for x in T[m]]), PT)
    SG = 1 - P[np.arange(len(smp)), grp]
    PK = P.reshape(len(smp), len(FAM), 15).sum(1)                     # P̂(k | x)
    SKk = 1 - PK[np.arange(len(smp)), K - 1]
    PKs = P[:, 30:45] / np.maximum(P[:, 30:45].sum(1, keepdims=True), 1e-12)  # P̂(k | x, SIR)
    SKs = 1 - PKs[np.arange(len(smp)), K - 1]
    cs = {(m, me): np.zeros(15) for m in TESTS for me in METH}; ss = {k: np.zeros(15) for k in cs}
    cnt = {m: np.zeros(15) for m in TESTS}; ksz = {m: [] for m in TESTS}
    for _ in range(REPS):
        cal = np.concatenate([rng.permutation(rest[mech[rest] == i])[:N_CAL] for i in range(len(FAM))])
        dc = D[cal].astype(float); gc = grp[cal]; kc = K[cal]; mc = mech[cal]
        kidx = np.concatenate([kcal, cal])
        t10 = np.array([cq(dc[gc == q], ALPHA) for q in range(NG)]); t08 = np.array([cq(dc[gc == q], AS) for q in range(NG)])
        qg = np.array([cq(SG[kidx][grp[kidx] == q], AG) for q in range(NG)])
        tk08 = np.array([cq(dc[kc == c], AS) for c in range(1, 16)])
        qk = np.array([cq(SKk[kidx][K[kidx] == c], AG) for c in range(1, 16)])
        sir = mech[kidx] == 2; qks = np.array([cq(SKs[kidx][sir & (K[kidx] == c)], AG) for c in range(1, 16)])
        ts08 = t08[30:45]
        tG = cq(dc, ALPHA); tMDm = max(cq(dc[mc == i], ALPHA) for i in range(len(FAM))); tMDmk = t10.max()
        for m in TESTS:
            dt_, mt, kt_, PT = TD[m]
            te = rng.choice(len(dt_), N_TE, replace=False); kt = kt_[te]; W = PT[te]
            KHg = (1 - W) <= qg[None, :]; KHg[~KHg.any(1)] = True; ksz[m].append(KHg.sum(1).mean())
            Wk = W.reshape(len(te), len(FAM), 15).sum(1)
            KHk = (1 - Wk) <= qk[None, :]; KHk[~KHk.any(1)] = True
            Ws = W[:, 30:45] / np.maximum(W[:, 30:45].sum(1, keepdims=True), 1e-12)
            KHs = (1 - Ws) <= qks[None, :]; KHs[~KHs.any(1)] = True
            mi = FAM.index(m) if m in FAM else 2
            th = {"G": np.full(N_TE, tG), "O": t10[mi * 15 + kt - 1], "WCP-mk": wcp_g(dc, gc, W, NG),
                  "MD-m": np.full(N_TE, tMDm), "MD-mk": np.full(N_TE, tMDmk),
                  "KSU*-SIR": np.array([ts08[h].max() for h in KHs]), "KSU*-k": np.array([tk08[h].max() for h in KHk]),
                  "KSU*-mk": np.array([t08[h].max() for h in KHg])}
            np.add.at(cnt[m], kt - 1, 1)
            for me in METH:
                M_ = th[me]; whole = ~np.isfinite(M_) | (M_ > mt[te])
                np.add.at(cs[(m, me)], kt - 1, whole | (dt_[te] <= M_)); np.add.at(ss[(m, me)], kt - 1, np.where(whole, n, np.where(np.isfinite(M_), M_, 0)))
    res = {}
    for m in TESTS:
        pr0 = cnt[m] / cnt[m].sum(); res[m] = {"_kset": float(np.mean(ksz[m]))}
        for me in METH:
            ck = cs[(m, me)] / np.maximum(cnt[m], 1); sk = ss[(m, me)] / np.maximum(cnt[m], 1)
            j = int(np.argmin(np.where(cnt[m] > 0, ck, np.inf)))
            res[m][me] = {"cov": float(pr0 @ ck), "size": float(pr0 @ sk), "kmin": float(ck[j]), "lo": wilson_lo(ck[j], cnt[m][j]), "karg": j + 1}
    return res


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    runs = [("lfr10k_mu0.1_0", 50, 0)] if SMOKE else RUNS
    R = pickle.load(open(OUT, "rb")) if (os.path.exists(OUT) and not SMOKE) else {}
    t0 = time.time()
    for key in runs:
        if key in R:
            continue
        print(f"[{dt.datetime.now():%H:%M}] {key}", flush=True)
        try:
            R[key] = run(*key)
        except TooHard as e:
            R[key] = {"skip": str(e)}; print("  bỏ:", e, flush=True)
        pickle.dump(R, open(OUT, "wb"))
    if SMOKE:
        r = R[runs[0]]; print("smoke ok", {m: (round(r[m]["KSU*-mk"]["kmin"], 2), round(r[m]["KSU*-mk"]["size"], 1), round(r[m]["MD-mk"]["size"], 1)) for m in TESTS}, flush=True); return
    report(R, time.time() - t0)


def report(R, secs):
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK19_PLAN.md", "jk19.py")}
    ok = [k for k in RUNS if "skip" not in R[k]]
    inb = [(k, m) for k in ok for m in FAM]
    v = [R[k][m]["KSU*-mk"]["kmin"] for k, m in inb]
    V1 = sum(x >= 0.88 for x in v) >= 34 and min(v) >= 0.86 and len(inb) == 36
    v2 = sum(R[k][m]["KSU*-mk"]["size"] < R[k][m]["MD-mk"]["size"] for k, m in inb); V2 = v2 >= 27
    verdict = "J-K19 ĐẠT — đóng góp phương pháp cho bản journal" if V1 and V2 else ("HỢP LỆ NHƯNG KHÔNG HIỆU QUẢ HƠN MDCP" if V1 else "CẦN XEM LẠI")
    L = ["# J-K19 — báo cáo (sinh tự động)", "",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Thời gian lượt này {secs/60:.0f} phút.", "",
         f"## Kết luận: **{verdict}**", "",
         f"- Lượt chạy được: {len(ok)}/{len(RUNS)}; bộ trong họ: {len(inb)}/36",
         f"- V1: KSU*-mk ≥ 0,88 ở {sum(x >= 0.88 for x in v)}/{len(v)}, thấp nhất {min(v):.3f} → {'đạt' if V1 else 'trượt'}",
         f"- V2: KSU*-mk nhỏ hơn MD-mk ở {v2}/{len(inb)} → {'đạt' if V2 else 'trượt'}", "",
         "Mỗi ô: phủ k xấu nhất [cận Wilson] (k) / kích thước.", ""]
    for k in RUNS:
        if "skip" in R[k]:
            L.append(f"### {k}: bỏ — {R[k]['skip']}"); continue
        L += [f"### {k[0]}, vùng nhiễm {k[1]}, seed {k[2]}", "", "| Triển khai | \\|K̂\\| | " + " | ".join(METH) + " |", "|---|---|" + "---|" * len(METH)]
        for m in TESTS:
            r = R[k][m]
            L.append(f"| {m}{'' if m in FAM else ' (ngoài họ)'} | {r['_kset']:.1f} | " + " | ".join(f"{r[me]['kmin']:.2f} [{r[me]['lo']:.2f}] (k={r[me]['karg']}) / {r[me]['size']:.1f}" for me in METH) + " |")
        L.append("")
    L += ["## Tóm tắt trung bình trên các bộ trong họ", "", "| Phương pháp | phủ k xấu nhất (min / trung vị) | kích thước trung vị | tỉ số kích thước / KSU*-mk (trung vị) |", "|---|---|---|---|"]
    for me in METH:
        km = [R[k][m][me]["kmin"] for k, m in inb]; sz = [R[k][m][me]["size"] for k, m in inb]
        rt = [R[k][m][me]["size"] / R[k][m]["KSU*-mk"]["size"] for k, m in inb]
        L.append(f"| {me} | {min(km):.2f} / {np.median(km):.2f} | {np.median(sz):.1f} | {np.median(rt):.2f} |")
    open(os.path.join(HERE, "results", "JK19_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:10]), flush=True)


if __name__ == "__main__":
    main()
