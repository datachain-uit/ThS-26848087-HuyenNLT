"""V3 — tính lại |K̂| GỘP qua 50 lần lặp cho 18 thiết lập J-K12A (cùng seed), kiểm lại Spearman. Phân tích bổ sung."""
from common import *
sys.path.append(os.path.join(B, "2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP")); sys.path.append(os.path.join(B, "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP")); sys.path.append(os.path.join(B, "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k"))
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from scipy.stats import spearmanr
import jk, jk11
from jk5 import cq, wcp_thresholds
from jk8 import prep, order_full, depth
SET_A = [(g, m, t) for g in ("lfr10k_mu0.1_1", "lfr10k_mu0.3_1") for t in (25, 100, 300) for m in ("SI", "IC", "SIR")]
cache = {}; rows = []
for idx, (gid, mname, target) in enumerate(SET_A):
    si = 100 + idx
    if gid not in cache: cache[gid] = jk11.load(gid)
    n, Adj = cache[gid]
    rng = np.random.default_rng(jk11.SEED0 + si)
    S = jk11.simulate(Adj, n, jk11.MODELS[mname], rng, target)
    N = len(S); K = np.array([len(s[1]) for s in S]); X = np.array([jk.feats(Adj, s[0]) for s in S])
    perm = rng.permutation(N); ktr, kcal, rest = perm[:1400], perm[1400:2000], perm[2000:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((N, 15)); P[:, [c - 1 for c in rf.classes_]] = rf.predict_proba(X); SK = 1 - P[np.arange(N), K - 1]
    half = np.full(n, 0.5); PR = {i: prep(Adj, S[i][0], half)[0][:, [3, 4, 5, 6, 7, 8]] for i in np.concatenate([ktr, rest])}
    y = np.concatenate([np.isin(S[i][0], S[i][1]).astype(int) for i in ktr])
    ms = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=0).fit(np.vstack([PR[i] for i in ktr]), y)
    DEP = np.zeros(N, int); MI = np.zeros(N, int)
    for i in rest:
        o = order_full(ms.predict_proba(PR[i])[:, 1], S[i][0]); DEP[i] = depth(o, S[i][1], n, K[i]); MI[i] = len(S[i][0])
    r2 = np.random.default_rng(jk11.SEED0 + 100 + si); ksum = 0; kn = 0; szK = szW = 0.0; nt = 0
    for _ in range(50):
        p = r2.permutation(rest); cal, te = p[:5600], p[5600:6000]; Kc = K[cal]
        kidx = np.concatenate([kcal, cal]); qk = np.array([cq(SK[kidx][K[kidx] == c], 0.02) for c in range(1, 16)])
        KH = (1 - P[te]) <= qk[None, :]; KH[~KH.any(1)] = True; ksum += KH.sum(); kn += len(te)
        dc = DEP[cal].astype(float); t08 = np.array([cq(dc[Kc == c], 0.08) for c in range(1, 16)])
        for nm, M in (("K", np.array([t08[h].max() for h in KH])), ("W", wcp_thresholds(dc, Kc, P[te]))):
            whole = ~np.isfinite(M) | (M > MI[te]); s = np.where(whole, n, np.where(np.isfinite(M), M, 0)).sum()
            if nm == "K": szK += s
            else: szW += s
        nt += len(te)
    rows.append((gid, mname, target, ksum / kn, szK / szW))
    with open("V3_KET_QUA.txt", "a", encoding="utf-8") as f:
        f.write(f"{gid} {mname} {target}: |K̂| gộp {ksum/kn:.2f}; KSU*/WCP (theo tổng kích thước) {szK/szW:.2f}\n")
    print(idx, "xong", flush=True)
x = [r[3] for r in rows]; y = [r[4] for r in rows]; rho = spearmanr(x, y).correlation
g = np.random.default_rng(7); perm_ = [spearmanr(x, g.permutation(y)).correlation for _ in range(10000)]
pv = (np.sum(np.array(perm_) >= rho) + 1) / 10001
with open("V3_KET_QUA.txt", "a", encoding="utf-8") as f:
    f.write(f"\nSpearman ρ(|K̂| gộp, KSU*/WCP) = {rho:.3f}; p hoán vị một phía = {pv:.4f}\n")
print("xong")
