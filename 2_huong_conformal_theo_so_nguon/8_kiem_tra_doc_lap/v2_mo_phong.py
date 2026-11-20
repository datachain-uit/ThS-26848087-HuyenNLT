"""V2 — tái hiện độc lập 1 thiết lập J-K11 (lfr10k_mu0.1_0, IC, 50 nút): kiểm mô phỏng, tính phủ bằng GIAO TẬP trực tiếp (không qua độ sâu)."""
from common import *
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
import jk, jk11
from jk8 import prep, order_full  # chỉ dùng để dựng đặc trưng cấu trúc và thứ tự nút
sys.path.append(os.path.join(B, "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k")); sys.path.append(os.path.join(B, "2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP")); sys.path.append(os.path.join(B, "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP"))
POW, A = 0.3, 0.10
si, gid, mname, target = 1, "lfr10k_mu0.1_0", "IC", 50
n, Adj = jk11.load(gid)
rng = np.random.default_rng(20261118 + si)
S = jk11.simulate(Adj, n, jk11.MODELS[mname], rng, target)
K = np.array([len(s[1]) for s in S])
chk = [len(s[0]) == target and np.isin(s[1], s[0]).all() and len(set(s[1])) == len(s[1]) for s in S]
kc = np.bincount(K, minlength=16)[1:]
X = np.array([jk.feats(Adj, s[0]) for s in S])
perm = rng.permutation(len(S)); ktr, kcal, rest = perm[:1400], perm[1400:2000], perm[2000:]
rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
P = np.zeros((len(S), 15)); P[:, rf.classes_ - 1] = rf.predict_proba(X); SK = 1 - P[np.arange(len(S)), K - 1]
half = np.full(n, 0.5); ST = [3, 4, 5, 6, 7, 8]
PR = {i: prep(Adj, S[i][0], half)[0][:, ST] for i in np.concatenate([ktr, rest])}
y = np.concatenate([np.isin(S[i][0], S[i][1]).astype(int) for i in ktr])
ms = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, random_state=0).fit(np.vstack([PR[i] for i in ktr]), y)
ORD = {i: order_full(ms.predict_proba(PR[i])[:, 1], S[i][0]) for i in rest}
def cover(i, m):  # giao tập trực tiếp, đúng tiêu chí của tác giả; m > |I| => cả đồ thị
    if not np.isfinite(m) or m > len(S[i][0]): return True, n
    m = int(m); return len(np.intersect1d(S[i][1], ORD[i][:m])) / len(S[i][1]) >= POW, m
def depth_ind(i):  # độ sâu tính lại độc lập bằng quét tuyến tính
    for m in range(1, len(ORD[i]) + 1):
        if len(np.intersect1d(S[i][1], ORD[i][:m])) / len(S[i][1]) >= POW: return m
    return n
DEP = {i: depth_ind(i) for i in rest}
M = ("G", "O", "WCP", "KSU*"); cov = {m: np.zeros(15) for m in M}; cnt = np.zeros(15); sz = {m: 0.0 for m in M}; nt = 0
r2 = np.random.default_rng(20261118 + 100 + si)
for _ in range(50):
    p = r2.permutation(rest); cal, te = p[:5600], p[5600:6000]
    dc = np.array([DEP[i] for i in cal], float); ck = K[cal]
    kk = np.concatenate([kcal, cal]); qk = [qconf(SK[kk][K[kk] == c], 0.02) for c in range(1, 16)]
    tG = qconf(dc, A); t10 = [qconf(dc[ck == c], A) for c in range(1, 16)]; t08 = [qconf(dc[ck == c], 0.08) for c in range(1, 16)]
    tW = wcp_vec(dc, ck, P[te], A)
    for t_i, i in enumerate(te):
        Kh = [c for c in range(1, 16) if 1 - P[i, c - 1] <= qk[c - 1]] or list(range(1, 16))
        for m, t in (("G", tG), ("O", t10[K[i] - 1]), ("WCP", tW[t_i]), ("KSU*", max(t08[c - 1] for c in Kh))):
            c_, s_ = cover(i, t); cov[m][K[i] - 1] += c_; sz[m] += s_
        cnt[K[i] - 1] += 1; nt += 1
with open("V2_KET_QUA.txt", "w", encoding="utf-8") as f:
    f.write(f"Mô phỏng: {len(S)} mẫu; đúng kích thước & nguồn trong vùng nhiễm & nguồn không trùng: {sum(chk)}/{len(S)}\n")
    f.write(f"Phân bố k (1..15): {kc.tolist()}\n")
    for m in M:
        r = cov[m] / cnt; j = int(np.argmin(r))
        f.write(f"{m}: phủ biên {cov[m].sum()/nt:.3f}; phủ k xấu nhất {r[j]:.2f} (k={j+1}); kích thước {sz[m]/nt:.1f}\n")
print("xong")
