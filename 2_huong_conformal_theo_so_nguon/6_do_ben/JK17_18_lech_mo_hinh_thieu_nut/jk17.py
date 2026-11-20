"""J-K17 (lệch mô hình lan truyền) + J-K18 (ảnh chụp thiếu nút). Giao thức: JK17_18_PLAN.md. Chạy: python jk17.py [--smoke]"""
import _venv; _venv.ensure()
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in ("2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK11_do_thi_lon", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k", "1_huong_cong_dong/5_E0_ho_so_cong_dong_da_thang", "2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK2_lech_mo_hinh", "2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k"):
    sys.path.append(os.path.join(B, p))
import datetime as dt, hashlib, pickle, platform, time
import numpy as np, scipy.sparse as sp
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
import jk11, jk
from jk11 import wilson_lo, STRUCT
from jk5 import cq, wcp_thresholds
from jk8 import prep, order_full, depth, qneed
os.chdir(HERE)

SMOKE = "--smoke" in sys.argv
POW, ALPHA, AK, AS = 0.3, 0.10, 0.02, 0.08
REPS = 2 if SMOKE else 50
N_CALD, N_TEST = (700, 300) if SMOKE else (8000, 4000)
N_KTR, N_K, N_CAL, N_TE = (200, 300, 300, 100) if SMOKE else (1400, 2000, 5600, 400)
MAX_TRY = 400_000
KS = list(range(1, 16)); METH = ("G", "O", "WCP", "MD", "KSU*")
kk_ = np.arange(1, 16, dtype=float)
SCEN = {"S1": np.where(kk_ <= 3, 1.0, 0.0), "S2": np.where(kk_ >= 11, 1.0, 0.0), "S3": (16 - kk_) ** 2, "S4": kk_ ** 2}
SCEN = {k: v / v.sum() for k, v in SCEN.items()}
OUT = os.path.join(HERE, "results", "JK17_smoke.pkl" if SMOKE else "JK17_raw.pkl")


# ---------- mô phỏng (cùng logic e0.si_fixed / pk2.ic_fixed / pk2.sir_fixed, có tham số) ----------
def si(A, src, rng, target, beta=0.3):
    ip, ix = A.indptr, A.indices; act = np.zeros(A.shape[0], bool); act[src] = True; stall = 0
    while act.sum() < target:
        new = set()
        for u in np.flatnonzero(act):
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[~act[nb]]
            if nb.size:
                new.update(nb[rng.random(nb.size) < beta].tolist())
        if not new:
            stall += 1
            if stall > 200:
                return None
            continue
        new = np.array(sorted(new), dtype=int); need = int(target - act.sum())
        if new.size > need:
            new = rng.choice(new, need, replace=False)
        act[new] = True
    return np.flatnonzero(act)


def ic(A, src, rng, target, p=0.2):
    ip, ix = A.indptr, A.indices; act = np.zeros(A.shape[0], bool); act[src] = True; front = np.asarray(src)
    while act.sum() < target:
        if front.size == 0:
            return None
        new = set()
        for u in front:
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[~act[nb]]
            if nb.size:
                new.update(nb[rng.random(nb.size) < p].tolist())
        new = np.array(sorted(new), dtype=int); need = int(target - act.sum())
        if new.size > need:
            new = rng.choice(new, need, replace=False)
        act[new] = True; front = new
    return np.flatnonzero(act)


def sir(A, src, rng, target, beta=0.3, gamma=0.3):
    ip, ix = A.indptr, A.indices; n = A.shape[0]
    ever = np.zeros(n, bool); ever[src] = True; inf = np.zeros(n, bool); inf[src] = True
    while ever.sum() < target:
        I = np.flatnonzero(inf)
        if I.size == 0:
            return None
        new = set()
        for u in I:
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[~ever[nb]]
            if nb.size:
                new.update(nb[rng.random(nb.size) < beta].tolist())
        inf[I[rng.random(I.size) < gamma]] = False
        new = np.array(sorted(new), dtype=int); need = int(target - ever.sum())
        if new.size > need:
            new = rng.choice(new, need, replace=False)
        ever[new] = True; inf[new] = True
    return np.flatnonzero(ever)


MODELS = {"SI": si, "IC": ic, "SIR": sir,
          "SIR-nhanh": lambda A, s, r, t: sir(A, s, r, t, beta=0.5, gamma=0.3),
          "SIR-dai": lambda A, s, r, t: sir(A, s, r, t, beta=0.3, gamma=0.1)}


class TooHard(Exception):
    pass


def simulate(A, n, model, rng, target, N):
    out, tries = [], 0
    while len(out) < N:
        tries += 1
        if tries > MAX_TRY:
            raise TooHard(f"chỉ được {len(out)}/{N} mẫu")
        k = int(rng.integers(1, 16)); src = rng.choice(n, k, replace=False)
        inf = MODELS[model](A, src, rng, target)
        if inf is None or len(inf) != target:
            continue
        out.append((np.asarray(inf, int), np.asarray(src, int)))
    return out


def mask(S, q, rng):
    """Che tỉ lệ q nút nhiễm (kể cả nguồn) khỏi ảnh chụp; giữ tối thiểu 2 nút quan sát."""
    out = []
    for inf, src in S:
        keep = rng.random(len(inf)) >= q
        if keep.sum() < 2:
            keep[rng.choice(len(inf), 2, replace=False)] = True
        out.append((inf[keep], src))
    return out


GRAPHS = {}


def load(gid):
    if gid not in GRAPHS:
        if gid == "cora_ml":
            g = pickle.load(open(os.path.join(B, "1_huong_cong_dong/2_baseline_GraphSL", "data", gid), "rb"))
            A = sp.csr_matrix(g["adj_mat"], dtype=float); A = ((A + A.T) > 0).astype(float); A.setdiag(0); A.eliminate_zeros()
            GRAPHS[gid] = (A.shape[0], sp.csr_matrix(A))
        else:
            GRAPHS[gid] = jk11.load(gid)
    return GRAPHS[gid]


def evaluate(A, n, SC, ST, seed):
    """SC: dữ liệu cơ chế hiệu chỉnh; ST: dữ liệu cơ chế triển khai. Phần tử: (nút quan sát nhiễm, nguồn thật)."""
    rng = np.random.default_rng(seed)
    KC = np.array([len(s[1]) for s in SC]); KT = np.array([len(s[1]) for s in ST])
    XC = np.array([jk.feats(A, s[0]) for s in SC]); XT = np.array([jk.feats(A, s[0]) for s in ST])
    perm = rng.permutation(len(SC)); ktr, kcal, rest = perm[:N_KTR], perm[N_KTR:N_K], perm[N_K:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(XC[ktr], KC[ktr])
    PC = np.zeros((len(SC), 15)); PC[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(XC)
    PT = np.zeros((len(ST), 15)); PT[:, [KS.index(c) for c in rf.classes_]] = rf.predict_proba(XT)
    SK = 1 - PC[np.arange(len(SC)), KC - 1]
    half = np.full(n, 0.5)
    FC = {i: prep(A, SC[i][0], half)[0][:, STRUCT] for i in np.concatenate([ktr, rest])}
    y = np.concatenate([np.isin(SC[i][0], SC[i][1]).astype(int) for i in ktr])
    hgb = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=0).fit(np.vstack([FC[i] for i in ktr]), y)

    def dep(S, i, F):
        o = order_full(hgb.predict_proba(F)[:, 1], S[i][0]); return depth(o, S[i][1], n, len(S[i][1])), len(S[i][0])
    DC = np.zeros(len(SC), int); MC = np.zeros(len(SC), int)
    for i in rest:
        DC[i], MC[i] = dep(SC, i, FC[i])
    DT = np.zeros(len(ST), int); MT = np.zeros(len(ST), int)
    for i in range(len(ST)):
        DT[i], MT[i] = dep(ST, i, prep(A, ST[i][0], half)[0][:, STRUCT])
    if SMOKE:
        for i in range(0, len(ST), 25):
            o = order_full(hgb.predict_proba(prep(A, ST[i][0], half)[0][:, STRUCT])[:, 1], ST[i][0])
            for M in (1, 3, 8):
                if M <= len(o):
                    assert (DT[i] <= M) == (np.isin(ST[i][1], o[:M]).sum() >= qneed(KT[i])), "luật phủ sai"
    cs = {m: np.zeros(15) for m in METH}; ss = {m: np.zeros(15) for m in METH}; cnt = np.zeros(15); ksz = []
    for _ in range(REPS):
        cal = rng.permutation(rest)[:N_CAL]; te = rng.choice(len(ST), N_TE, replace=False)
        Kc, kt = KC[cal], KT[te]; dc = DC[cal].astype(float)
        kidx = np.concatenate([kcal, cal])
        qk = np.array([cq(SK[kidx][KC[kidx] == c], AK) for c in KS])
        KH = (1 - PT[te]) <= qk[None, :]; KH[~KH.any(1)] = True; ksz.append(KH.sum(1).mean())
        t10 = np.array([cq(dc[Kc == c], ALPHA) for c in KS]); t08 = np.array([cq(dc[Kc == c], AS) for c in KS])
        th = {"G": np.full(len(te), cq(dc, ALPHA)), "O": t10[kt - 1], "WCP": wcp_thresholds(dc, Kc, PT[te]),
              "MD": np.full(len(te), t10.max()), "KSU*": np.array([t08[h].max() for h in KH])}
        np.add.at(cnt, kt - 1, 1)
        for m in METH:
            M = th[m]; whole = ~np.isfinite(M) | (M > MT[te])
            np.add.at(cs[m], kt - 1, whole | (DT[te] <= M)); np.add.at(ss[m], kt - 1, np.where(whole, n, np.where(np.isfinite(M), M, 0)))
    pr0 = cnt / cnt.sum(); res = {"_kset": float(np.mean(ksz))}
    for m in METH:
        ck, sk = cs[m] / np.maximum(cnt, 1), ss[m] / np.maximum(cnt, 1); j = int(np.argmin(np.where(cnt > 0, ck, np.inf)))
        res[m] = {"cov": float(pr0 @ ck), "size": float(pr0 @ sk), "kmin": float(ck[j]), "lo": wilson_lo(ck[j], cnt[j]), "karg": j + 1,
                  **{s: float(w @ ck) for s, w in SCEN.items()}}
    return res


GR = ("lfr10k_mu0.1_0", "cora_ml")
J17 = [("17", g, a, b, t) for g in GR for t in (50, 200) for a in ("SI", "IC", "SIR") for b in ("SI", "IC", "SIR")] + \
      [("17", g, "SIR", b, t) for g in GR for t in (50, 200) for b in ("SIR-nhanh", "SIR-dai")]
J18 = [("18", g, m, mode, q) for g in GR for m in ("SI", "IC", "SIR") for q in (0.05, 0.15) for mode in ("test", "both")]


def run(key, idx, cacheS):
    seed = 20261119 + 1000 * idx
    if key[0] == "17":
        _, g, a, b, t = key
        n, A = load(g)
        ca = (g, a, t, "cal")
        if ca not in cacheS:  # dữ liệu hiệu chỉnh dùng chung cho mọi B cùng (đồ thị, A, kích thước); seed tất định
            sc = 20261119 + 100000 * GR.index(g) + 1000 * ("SI", "IC", "SIR").index(a) + t
            try:
                cacheS[ca] = simulate(A, n, a, np.random.default_rng(sc), t, N_CALD)
            except TooHard as e:
                cacheS[ca] = e
        if isinstance(cacheS[ca], TooHard):
            raise TooHard("dữ liệu hiệu chỉnh: " + str(cacheS[ca]))
        SC = cacheS[ca]
        ST = simulate(A, n, b, np.random.default_rng(seed + 7), t, N_TEST)
        return evaluate(A, n, SC, ST, seed + 11)
    _, g, m, mode, q = key
    n, A = load(g)
    rng = np.random.default_rng(seed)
    SC = simulate(A, n, m, rng, 50, N_CALD); ST = simulate(A, n, m, np.random.default_rng(seed + 7), 50, N_TEST)
    ST = mask(ST, q, np.random.default_rng(seed + 13))
    if mode == "both":
        SC = mask(SC, q, np.random.default_rng(seed + 17))
    return evaluate(A, n, SC, ST, seed + 11)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    keys = [J17[3], J18[1]] if SMOKE else J17 + J18
    R = pickle.load(open(OUT, "rb")) if (os.path.exists(OUT) and not SMOKE) else {}
    t0 = time.time(); cacheS = {}
    for idx, key in enumerate(J17 + J18):
        if key not in keys or key in R:
            continue
        print(f"[{dt.datetime.now():%H:%M}] {key}", flush=True)
        try:
            R[key] = run(key, idx, cacheS)
        except TooHard as e:
            R[key] = {"skip": str(e)}; print("  bỏ:", e, flush=True)
        pickle.dump(R, open(OUT, "wb"))
    if SMOKE:
        print("smoke ok", {k: (round(v["G"]["kmin"], 2), round(v["KSU*"]["kmin"], 2)) for k, v in R.items() if "skip" not in v}, flush=True); return
    report(R, time.time() - t0)


def report(R, secs):
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK17_18_PLAN.md", "jk17.py")}
    ok = lambda k: "skip" not in R[k]
    L = ["# J-K17 + J-K18 — báo cáo (sinh tự động)", "",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Thời gian lượt này {secs/60:.0f} phút.", ""]
    match = [k for k in J17 if k[2] == k[3] and ok(k)]; mis = [k for k in J17 if k[2] != k[3] and ok(k)]
    ctrl = all(R[k]["KSU*"]["kmin"] >= 0.88 for k in match)
    p1a = sum(R[k]["KSU*"]["kmin"] > R[k]["G"]["kmin"] for k in mis); p1b = sum(R[k]["KSU*"]["kmin"] >= R[k]["WCP"]["kmin"] for k in mis)
    p2 = sum(R[k]["KSU*"]["kmin"] >= 0.85 for k in mis)
    P1 = p1a >= 0.9 * len(mis) and p1b >= 0.75 * len(mis); P2 = p2 >= 0.75 * len(mis)
    v17 = "KSU* BỀN TRƯỚC LỆCH MÔ HÌNH" if P1 and P2 else ("BỀN TƯƠNG ĐỐI, MẤT BẢO ĐẢM TUYỆT ĐỐI" if P1 else "KHÔNG BỀN")
    L += [f"## J-K17: **{v17}**", "",
          f"- Đối chứng (thiết lập trùng, KSU* ≥ 0,88): {sum(R[k]['KSU*']['kmin'] >= 0.88 for k in match)}/{len(match)} → {'đạt' if ctrl else 'TRƯỢT — xem lại cài đặt'}",
          f"- Thiết lập lệch mô phỏng được: {len(mis)}/{len([k for k in J17 if k[2] != k[3]])}",
          f"- P1: KSU* > G ở {p1a}/{len(mis)}; KSU* ≥ WCP ở {p1b}/{len(mis)} → {'đạt' if P1 else 'trượt'}",
          f"- P2: KSU* ≥ 0,85 ở {p2}/{len(mis)} → {'đạt' if P2 else 'trượt'}", "",
          "| Đồ thị | Vùng nhiễm | Hiệu chỉnh → Triển khai | \\|K̂\\| | G | O | WCP | MDCP | KSU* |", "|---|---|---|---|---|---|---|---|---|"]
    cell = lambda r, m: f"{r[m]['cov']:.2f}; {r[m]['kmin']:.2f} [{r[m]['lo']:.2f}] (k={r[m]['karg']}); {r[m]['size']:.1f}"
    for k in J17:
        r = R[k]
        if not ok(k):
            L.append(f"| {k[1]} | {k[4]} | {k[2]} → {k[3]} | — | bỏ: {r['skip']} |||||"); continue
        L.append(f"| {k[1]} | {k[4]} | {k[2]} → {k[3]} | {r['_kset']:.1f} | " + " | ".join(cell(r, m) for m in METH) + " |")
    L += ["", "Mỗi ô: phủ biên; phủ k xấu nhất [cận Wilson] (k); kích thước. Phủ biên tính theo phân phối k của dữ liệu triển khai.", ""]
    both = [k for k in J18 if k[3] == "both" and ok(k)]; test = [k for k in J18 if k[3] == "test" and ok(k)]
    q1 = sum(R[k]["KSU*"]["kmin"] >= 0.88 for k in both); q2 = sum(R[k]["KSU*"]["kmin"] >= 0.85 for k in test)
    q3 = sum(R[k]["KSU*"]["kmin"] > R[k]["G"]["kmin"] for k in test)
    L += ["## J-K18 — ảnh chụp thiếu nút", "",
          f"- Q1 (cả hai bị che, KSU* ≥ 0,88): {q1}/{len(both)} → {'đạt' if q1 == len(both) and len(both) == 12 else 'trượt'}",
          f"- Q2 (chỉ kiểm tra bị che, KSU* ≥ 0,85): {q2}/{len(test)} → {'đạt' if q2 >= 0.75 * len(test) else 'trượt'}",
          f"- Q3 (chỉ kiểm tra bị che, KSU* > G): {q3}/{len(test)} → {'đạt' if q3 >= 0.9 * len(test) else 'trượt'}", "",
          "| Đồ thị | Mô hình | q | Chế độ | \\|K̂\\| | G | O | WCP | MDCP | KSU* |", "|---|---|---|---|---|---|---|---|---|---|"]
    for k in J18:
        r = R[k]
        if not ok(k):
            L.append(f"| {k[1]} | {k[2]} | {k[4]} | {k[3]} | — | bỏ: {r['skip']} |||||"); continue
        L.append(f"| {k[1]} | {k[2]} | {k[4]} | {k[3]} | {r['_kset']:.1f} | " + " | ".join(cell(r, m) for m in METH) + " |")
    open(os.path.join(HERE, "results", "JK17_18_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:12]), flush=True)


if __name__ == "__main__":
    main()
