"""J-K15 Phần A + C — backbone GCN thứ hai và độ nhạy cách chia α trên dữ liệu tác giả. Giao thức: JK15_PLAN.md.
Chạy: python jk15a.py [--smoke]"""
import os, sys
import _venv_torch as _venv
sys.modules["_venv"] = _venv          # mọi module dự án dùng chung .venv có torch
_venv.ensure()
os.environ["NO_VENV"] = "1"
import types
try:
    import pandas  # noqa
except ImportError:  # .venv có torch thiếu pandas; data_utils của tác giả chỉ import, hàm điểm không dùng
    sys.modules["pandas"] = types.ModuleType("pandas")
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in ("2_huong_conformal_theo_so_nguon/8_kiem_tra_doc_lap", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k", "1_huong_cong_dong/5_E0_ho_so_cong_dong_da_thang"):
    sys.path.append(os.path.join(B, p))
import datetime as dt, hashlib, pickle, platform, time
import numpy as np, networkx as nx, scipy.sparse as sp
import torch, torch.nn as nn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from common import qconf, wcp_vec
import jk
from utils.score_convert import recall_score, recall_score_gtunknown, set_truncate
if "pandas" in sys.modules and not hasattr(sys.modules["pandas"], "__file__"):  # gỡ pandas rỗng để sklearn không nhầm
    del sys.modules["pandas"]
for _m in ("tensorflow",):  # jk.py chèn tensorflow giả; torch (dynamo) không chịu module thiếu __spec__
    if _m in sys.modules and getattr(sys.modules[_m], "__spec__", None) is None:
        del sys.modules[_m]
os.chdir(HERE)

SMOKE = "--smoke" in sys.argv
POW, A = 0.3, 0.10
REPS = 2 if SMOKE else 50
NCAL, NTE = (900, 300) if SMOKE else (5600, 400)
EPOCHS = 2 if SMOKE else 60
CONFIGS = [(g, r) for g in ("highSchool", "sfhh", "bkFratB") for r in ("1-15", "11-25", "21-35")]
if SMOKE:
    CONFIGS = [("bkFratB", "11-25")]
SPLITS = [0.005, 0.01, 0.02, 0.03, 0.05]
kk_ = np.arange(1, 16, dtype=float)
SCEN = {"S1": np.where(kk_ <= 3, 1.0, 0.0), "S2": np.where(kk_ >= 11, 1.0, 0.0), "S3": (16 - kk_) ** 2, "S4": kk_ ** 2}
SCEN = {k: v / v.sum() for k, v in SCEN.items()}
OUT = os.path.join(HERE, "results", "JK15A_smoke.txt" if SMOKE else "JK15A_raw.pkl")


def wilson_lo(p, n, z=1.96):
    return float((p + z * z / (2 * n) - z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n))


class GCN(nn.Module):
    def __init__(s, F, H=64):
        super().__init__()
        s.l = nn.ModuleList([nn.Linear(F, H), nn.Linear(H, H), nn.Linear(H, H)]); s.o = nn.Linear(H, 1)

    def forward(s, An, X):
        Bn, n, _ = X.shape; h = X
        for lin in s.l:
            h = lin(h)
            h = torch.sparse.mm(An, h.permute(1, 0, 2).reshape(n, -1)).reshape(n, Bn, -1).permute(1, 0, 2)
            h = nn.functional.dropout(torch.relu(h), 0.1, s.training)
        return s.o(h).squeeze(-1)


def gcn_probs(Adj, smp, ktr):
    n = Adj.shape[0]
    deg = np.asarray(Adj.sum(1)).ravel(); dinv = np.where(deg > 0, deg ** -0.5, 0)
    S = (sp.diags(dinv) @ Adj @ sp.diags(dinv)).toarray()
    M = 0.5 * np.linalg.inv(np.eye(n) - 0.5 * S)
    A2 = Adj + sp.eye(n); d2 = np.asarray(A2.sum(1)).ravel(); An = (sp.diags(d2 ** -0.5) @ A2 @ sp.diags(d2 ** -0.5)).tocoo()
    An = torch.sparse_coo_tensor(np.vstack([An.row, An.col]), An.data.astype(np.float32), (n, n)).coalesce()
    ldeg = np.log1p(deg) / max(np.log1p(deg).max(), 1e-9); Adjd = Adj.toarray(); degs = np.maximum(deg, 1)

    def feat(idx):
        out = np.zeros((len(idx), n, 5), np.float32)
        for t, i in enumerate(idx):
            v = np.zeros(n); v[smp[i][0]] = 1.0; dd = 2 * v - 1
            out[t] = np.stack([dd, M @ dd, M @ v, ldeg, (Adjd @ v) / degs], 1)
        return torch.from_numpy(out)

    torch.manual_seed(0); rng = np.random.default_rng(0)
    model = GCN(5); opt = torch.optim.Adam(model.parameters(), lr=3e-3, weight_decay=1e-4)
    Xtr = feat(ktr)
    Y = torch.zeros(len(ktr), n); MASK = torch.zeros(len(ktr), n, dtype=torch.bool)
    for t, i in enumerate(ktr):
        Y[t, np.nonzero(smp[i][2])[0]] = 1.0; MASK[t, smp[i][0]] = True
    pw = torch.tensor(float(MASK.sum() - Y[MASK].sum()) / float(Y[MASK].sum()))
    lossf = nn.BCEWithLogitsLoss(pos_weight=pw)
    for ep in range(EPOCHS):
        model.train(); perm = rng.permutation(len(ktr)); tot = 0.0
        for b in range(0, len(ktr), 32):
            j = torch.from_numpy(perm[b:b + 32]); lo = model(An, Xtr[j])
            loss = lossf(lo[MASK[j]], Y[j][MASK[j]]); opt.zero_grad(); loss.backward(); opt.step(); tot += float(loss)
        if ep % 10 == 0 or ep == EPOCHS - 1:
            print(f"    epoch {ep} loss {tot:.2f}", flush=True)
    model.eval(); PROB = np.zeros((len(smp), n))
    with torch.no_grad():
        for b in range(0, len(smp), 256):
            idx = np.arange(b, min(b + 256, len(smp))); pr = torch.sigmoid(model(An, feat(idx))).numpy()
            for t, i in enumerate(idx):
                p = np.zeros(n); p[smp[i][0]] = pr[t, smp[i][0]]; PROB[i] = p
    return PROB


def evaluate(smp, PROB, K, P, kcal, rest, n):
    CAL = np.full(len(smp), np.nan); TS = {}; SRC = {}
    for i in rest:
        inf, _, gt = smp[i]; pr = PROB[i]
        CAL[i] = recall_score(pr, set_truncate(gt, pr, POW), "SIR", inf)
        TS[i] = np.asarray(recall_score_gtunknown(pr, "SIR", inf)); SRC[i] = np.nonzero(gt)[0]
    SK = 1 - P[np.arange(len(smp)), K - 1]
    M = ["G", "O", "WCP", "MD"] + [f"KSU_{a}" for a in SPLITS]
    cov = {m: np.zeros(15) for m in M}; sz = {m: np.zeros(15) for m in M}; cnt = np.zeros(15)
    rng = np.random.default_rng(20261118 + 1)
    for _ in range(REPS):
        p = rng.permutation(rest); cal, te = p[:NCAL], p[NCAL:NCAL + NTE]
        cv, ck = CAL[cal], K[cal]
        t10 = [qconf(cv[ck == c], A) for c in range(1, 16)]
        th = {"G": np.full(len(te), qconf(cv, A)), "O": np.array([t10[K[i] - 1] for i in te]),
              "WCP": wcp_vec(cv, ck, P[te], A), "MD": np.full(len(te), max(t10))}
        kk = np.concatenate([kcal, cal])
        for ak in SPLITS:
            ts = [qconf(cv[ck == c], A - ak) for c in range(1, 16)]
            qk = np.array([qconf(SK[kk][K[kk] == c], ak) for c in range(1, 16)])
            KH = (1 - P[te]) <= qk[None, :]; KH[~KH.any(1)] = True
            th[f"KSU_{ak}"] = np.array([max(ts[c] for c in np.nonzero(h)[0]) for h in KH])
        for t_i, i in enumerate(te):
            cnt[K[i] - 1] += 1
            for m in M:
                S = np.where(TS[i] <= th[m][t_i])[0]
                cov[m][K[i] - 1] += len(np.intersect1d(SRC[i], S)) / len(SRC[i]) >= POW
                sz[m][K[i] - 1] += len(S)
    pr0 = cnt / cnt.sum(); res = {}
    for m in M:
        ck_, sk_ = cov[m] / cnt, sz[m] / cnt; j = int(np.argmin(ck_))
        res[m] = {"cov": float(pr0 @ ck_), "size": float(pr0 @ sk_), "kmin": float(ck_[j]), "kmin_lo": wilson_lo(ck_[j], cnt[j]),
                  "kargmin": j + 1, **{s: float(w @ ck_) for s, w in SCEN.items()}}
    return res


def run(g, rz):
    d = pickle.load(open(os.path.join(jk.CN, "SD-STGCN", "output", "test_res", g, f"SIR_nsrc1-15_Rzero{rz}_gamma0.1-0.4_ls8000_nf16", "res.pickle"), "rb"))
    n = np.asarray(d["predictions"][0][0]).shape[0]
    Gr = nx.read_edgelist(os.path.join(jk.CN, "SD-STGCN", "dataset", g, "data", "graph", g + ".edgelist"), nodetype=int); Gr.add_nodes_from(range(n))
    Adj = sp.csr_matrix(nx.to_scipy_sparse_array(Gr, nodelist=range(n), format="csr", dtype=float))
    smp = [(np.nonzero(np.asarray(d["inputs"][b][j]))[0], np.asarray(d["predictions"][b][j])[:, 1], np.asarray(d["ground_truth"][b][j]))
           for b in range(len(d["inputs"])) for j in range(len(d["inputs"][b]))]
    N = len(smp); K = np.array([int(s[2].sum()) for s in smp])
    X = np.array([jk.feats(Adj, s[0]) for s in smp])
    perm = np.random.default_rng(20261118).permutation(N)
    ktr, kcal, rest = perm[:1400], perm[1400:2000], perm[2000:]
    if SMOKE:
        rest = rest[:1200]
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X[ktr], K[ktr])
    P = np.zeros((N, 15)); P[:, rf.classes_ - 1] = rf.predict_proba(X)
    t0 = time.time(); PG = gcn_probs(Adj, smp, ktr); tg = time.time() - t0
    PS = np.array([s[1] for s in smp])
    auc = {}
    for nm, PP in (("gcn", PG), ("sdstgcn", PS)):
        yy, ss = [], []
        for i in rest[:1000]:
            inf = smp[i][0]; yy.append(smp[i][2][inf]); ss.append(PP[i][inf])
        auc[nm] = float(roc_auc_score(np.concatenate(yy), np.concatenate(ss)))
    if SMOKE:
        rest_s = rest
        r1 = evaluate(smp, PG, K, P, kcal, rest_s, n)
        assert all(np.isfinite(r1[m]["size"]) for m in r1), "kích thước lỗi"
        return {"auc": auc, "gcn": r1, "t_gcn": tg}
    out = {"auc": auc, "t_gcn": tg, "gcn": evaluate(smp, PG, K, P, kcal, rest, n), "sdstgcn": evaluate(smp, PS, K, P, kcal, rest, n)}
    print(f"  {g} {rz} xong: AUC gcn {auc['gcn']:.3f} / sd {auc['sdstgcn']:.3f}", flush=True)
    return out


def main():
    t0 = time.time(); allres = {}
    if os.path.exists(OUT) and not SMOKE:
        allres = pickle.load(open(OUT, "rb"))
    for g, rz in CONFIGS:
        if (g, rz) in allres:
            continue
        print(f"[{dt.datetime.now():%H:%M}] {g} {rz}", flush=True)
        allres[(g, rz)] = run(g, rz)
        if SMOKE:
            r = allres[(g, rz)]
            open(OUT, "w", encoding="utf-8").write(f"smoke ok; AUC {r['auc']}; t_gcn {r['t_gcn']:.0f}s\n")
            print("smoke ok", r["auc"], flush=True); return
        pickle.dump(allres, open(OUT, "wb"))
    report(allres, time.time() - t0)


def report(R, secs):
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK15_PLAN.md", "jk15a.py")}
    L = [f"# J-K15 Phần A + C — báo cáo (sinh tự động)", "",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}, torch {torch.__version__}. SHA {sha}. Thời gian {secs/60:.0f} phút.", ""]
    a1 = sum(R[c]["gcn"]["G"]["kmin"] < 0.85 for c in CONFIGS)
    a2k = sum(R[c]["gcn"]["KSU_0.02"]["kmin"] >= 0.88 for c in CONFIGS)
    a2p = sum(R[c]["gcn"]["KSU_0.02"][s] >= 0.88 for c in CONFIGS for s in SCEN)
    A1, A2 = a1 >= 7, (a2k == 9 and a2p == 36)
    verdict = "BỀN THEO BACKBONE" if A1 and A2 else ("MỘT PHẦN (C2 bền, C1 phụ thuộc backbone)" if A2 else "CẦN XEM LẠI")
    L += [f"## Phần A: **{verdict}**", "", f"- A1 (G < 0,85 ở k xấu nhất, backbone GCN): {a1}/9 → {'đạt' if A1 else 'trượt'}",
          f"- A2 (KSU* ≥ 0,88): theo k {a2k}/9, lệch prior {a2p}/36 → {'đạt' if A2 else 'trượt'}", ""]
    L += ["| Đồ thị | R0 | AUC GCN / SD-STGCN | Backbone | G | O | WCP | MDCP | KSU* |", "|---|---|---|---|---|---|---|---|---|"]
    for c in CONFIGS:
        for bb in ("gcn", "sdstgcn"):
            r = R[c][bb]
            cell = lambda m: f"{r[m]['cov']:.3f}; {r[m]['kmin']:.2f} [{r[m]['kmin_lo']:.2f}] (k={r[m]['kargmin']}); {r[m]['size']:.1f}"
            L.append(f"| {c[0]} | {c[1]} | {R[c]['auc']['gcn']:.3f} / {R[c]['auc']['sdstgcn']:.3f} | {bb} | " +
                     " | ".join(cell(m) for m in ("G", "O", "WCP", "MD", "KSU_0.02")) + " |")
    L += ["", "Mỗi ô: phủ biên; phủ ở k xấu nhất [cận Wilson] (k); kích thước. Hàm điểm recall.", "",
          "### Lệch prior, backbone GCN (S1 / S2 / S3 / S4)", "", "| Đồ thị | R0 | G | WCP | KSU* |", "|---|---|---|---|---|"]
    for c in CONFIGS:
        r = R[c]["gcn"]
        L.append(f"| {c[0]} | {c[1]} | " + " | ".join(" / ".join(f"{r[m][s]:.2f}" for s in SCEN) for m in ("G", "WCP", "KSU_0.02")) + " |")
    L += ["", "## Phần C — độ nhạy cách chia α (α_s = 0,10 − α_k)", ""]
    for bb in ("gcn", "sdstgcn"):
        ok = 0
        L += [f"### Backbone {bb}", "", "| Đồ thị | R0 | " + " | ".join(f"α_k={a}" for a in SPLITS) + " | 0,02 / tốt nhất |",
              "|---|---|" + "---|" * (len(SPLITS) + 1)]
        for c in CONFIGS:
            r = R[c][bb]; s = [r[f"KSU_{a}"]["size"] for a in SPLITS]; ratio = s[SPLITS.index(0.02)] / min(s); ok += ratio <= 1.10
            L.append(f"| {c[0]} | {c[1]} | " + " | ".join(f"{r[f'KSU_{a}']['size']:.1f} ({r[f'KSU_{a}']['kmin']:.2f})" for a in SPLITS) + f" | {ratio:.2f} |")
        L += ["", f"C1 ({bb}): 0,02 trong 10% tốt nhất ở {ok}/9 → {'mặc định 0,02 hợp lý' if ok >= 7 else 'trượt — xem cách chia tốt nhất'}", ""]
    L += ["Ô Phần C: kích thước KSU* (phủ ở k xấu nhất)."]
    open(os.path.join(HERE, "results", "JK15A_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:12]), flush=True)


if __name__ == "__main__":
    main()
