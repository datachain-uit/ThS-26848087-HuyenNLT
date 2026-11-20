"""V1 — tính lại độc lập G, O, WCP, KSU* trên dữ liệu tác giả (recall), so với J-K12B."""
from common import *
import pickle, networkx as nx, scipy.sparse as sp
from sklearn.ensemble import RandomForestClassifier
import jk
from utils.score_convert import recall_score, recall_score_gtunknown, set_truncate
POW, A = 0.3, 0.10
def run(G_, RZ, reps=50):
    d = pickle.load(open(os.path.join(jk.CN, "SD-STGCN", "output", "test_res", G_, f"SIR_nsrc1-15_Rzero{RZ}_gamma0.1-0.4_ls8000_nf16", "res.pickle"), "rb"))
    n = np.asarray(d["predictions"][0][0]).shape[0]
    Gr = nx.read_edgelist(os.path.join(jk.CN, "SD-STGCN", "dataset", G_, "data", "graph", G_ + ".edgelist"), nodetype=int); Gr.add_nodes_from(range(n))
    Adj = sp.csr_matrix(nx.to_scipy_sparse_array(Gr, nodelist=range(n), format="csr", dtype=float))
    smp = [(np.nonzero(np.asarray(d["inputs"][b][j]))[0], np.asarray(d["predictions"][b][j])[:, 1], np.asarray(d["ground_truth"][b][j]))
           for b in range(len(d["inputs"])) for j in range(len(d["inputs"][b]))]
    N = len(smp); K = np.array([int(s[2].sum()) for s in smp])
    X = np.array([jk.feats(Adj, s[0]) for s in smp])
    perm = np.random.default_rng(20261118).permutation(N)
    ktr, kcal, rest = perm[:1400], perm[1400:2000], perm[2000:]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((N, 15)); P[:, rf.classes_ - 1] = rf.predict_proba(X)
    CAL = np.full(N, np.nan); TS = {}; SRC = {}
    for i in rest:
        inf, pr, gt = smp[i]
        CAL[i] = recall_score(pr, set_truncate(gt, pr, POW), "SIR", inf)
        TS[i] = np.asarray(recall_score_gtunknown(pr, "SIR", inf)); SRC[i] = np.nonzero(gt)[0]
    SK = 1 - P[np.arange(N), K - 1]
    M = ("G", "O", "WCP", "KSU*"); cov = {m: np.zeros(15) for m in M}; cnt = np.zeros(15); sz = {m: 0.0 for m in M}; nt = 0
    rng = np.random.default_rng(20261118 + 1)
    for _ in range(reps):
        p = rng.permutation(rest); cal, te = p[:5600], p[5600:6000]
        cv, ck = CAL[cal], K[cal]
        tG = qconf(cv, A); t10 = [qconf(cv[ck == c], A) for c in range(1, 16)]; t08 = [qconf(cv[ck == c], 0.08) for c in range(1, 16)]
        kk = np.concatenate([kcal, cal]); qk = [qconf(SK[kk][K[kk] == c], 0.02) for c in range(1, 16)]
        tW = wcp_vec(cv, ck, P[te], A)
        for t_i, i in enumerate(te):
            Kh = [c for c in range(1, 16) if 1 - P[i, c - 1] <= qk[c - 1]] or list(range(1, 16))
            for m, t in (("G", tG), ("O", t10[K[i] - 1]), ("WCP", tW[t_i]), ("KSU*", max(t08[c - 1] for c in Kh))):
                S = np.where(TS[i] <= t)[0]
                cov[m][K[i] - 1] += len(np.intersect1d(SRC[i], S)) / len(SRC[i]) >= POW   # đúng như main.py của tác giả
                sz[m] += len(S)
            cnt[K[i] - 1] += 1; nt += 1
    out = []
    for m in M:
        r = cov[m] / cnt; j = int(np.argmin(r))
        out.append(f"{m}: phủ biên {cov[m].sum()/nt:.3f}; phủ k xấu nhất {r[j]:.2f} (k={j+1}); kích thước {sz[m]/nt:.1f}")
    return out
if __name__ == "__main__":
    for g, rz in (("highSchool", "1-15"), ("sfhh", "21-35"), ("bkFratB", "11-25")):
        res = run(g, rz)
        with open("V1_KET_QUA.txt", "a", encoding="utf-8") as f:
            f.write(f"## {g} R0 {rz}\n" + "\n".join(res) + "\n\n")
        print(g, rz, "xong", flush=True)
