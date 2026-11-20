"""P-K — pilot tập dự đoán conformal cho số nguồn k, trên cascade của E0x. Giao thức: PK_PLAN.md.
Chạy: python pk.py   (cần E0x đủ 10 seed; vài phút)"""
import _venv; _venv.ensure()
import csv
import datetime as dt
import glob
import hashlib
import os
import platform

import numpy as np
from sklearn.ensemble import RandomForestClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
CHUNKS = os.path.join(HERE, "..", "..", "..", "1_huong_cong_dong", "6_E0x_so_cum_theo_so_nguon", "results", "chunks")
GRAPHS = ["lfr_mu0.1_0", "lfr_mu0.3_0", "lfr_mu0.5_0", "email_eu"]
FS = [0.02, 0.05, 0.10, 0.15, 0.25, 0.40]
KS = [1, 2, 3, 5, 8]
GAMMAS = [0.1, 0.25, 0.5, 1.0, 2.0, 4.0]
F_U = (["comp"] + [f"rho_{r}" for r in range(1, 7)] + [f"c_{g}" for g in GAMMAS] + ["q_1.0"] +
       ["diam", "rad", "dq25", "dq50", "dq75", "dq90", "bnd", "degG_mean", "degG_max", "degI_mean", "leaf", "ecc_min"])
TR, CAL, TE = range(0, 4), range(4, 7), range(7, 10)
ALPHA = 0.1


def load():
    rows = []
    for p in sorted(glob.glob(os.path.join(CHUNKS, "s*_f*.csv"))):
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["place"] != "rand":
                    continue
                rows.append(dict(seed=int(r["seed"]), graph=r["graph"], f=float(r["f"]), k=int(r["k"]),
                                 x=[float(r[c]) for c in F_U]))
    return rows


def qhat(scores, alpha):
    n = len(scores)
    lvl = min(1.0, np.ceil((n + 1) * (1 - alpha)) / n)
    return float(np.quantile(scores, lvl, method="higher"))


def cell(rows):
    sel = lambda S: [r for r in rows if r["seed"] in S]
    tr, ca, te = sel(TR), sel(CAL), sel(TE)
    X = lambda R: np.array([r["x"] for r in R], float)
    y = lambda R: np.array([r["k"] for r in R])
    m = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(X(tr), y(tr))
    idx = {k: i for i, k in enumerate(m.classes_)}
    Pc, Pt, yc, yt = m.predict_proba(X(ca)), m.predict_proba(X(te)), y(ca), y(te)
    sc = 1 - Pc[np.arange(len(yc)), [idx[v] for v in yc]]
    q = qhat(sc, ALPHA)
    sets = {"CP": Pt >= 1 - q}
    qm = {k: qhat(sc[yc == k], ALPHA) for k in KS}
    sets["CP-M"] = np.stack([Pt[:, idx[k]] >= 1 - qm[k] for k in m.classes_], axis=1)
    top = Pt.argmax(1)
    pt = np.zeros_like(Pt, bool); pt[np.arange(len(top)), top] = True
    sets["pt"] = pt
    pos = np.array(KS)
    pm1 = np.zeros_like(Pt, bool)
    for i, t in enumerate(top):
        kh = m.classes_[t]
        pm1[i] = [abs(KS.index(c) - KS.index(kh)) <= 1 for c in m.classes_]
    sets["pm1"] = pm1
    out = {}
    hit_idx = np.array([idx[v] for v in yt])
    for name, S in sets.items():
        hit = S[np.arange(len(yt)), hit_idx]
        out[name] = dict(cov=float(hit.mean()), size=float(S.sum(1).mean()),
                         **{f"cov_k{k}": float(hit[yt == k].mean()) for k in KS})
    return out


def main():
    rows = load()
    seeds = sorted({r["seed"] for r in rows})
    have = {s: len({(r["graph"], r["f"]) for r in rows if r["seed"] == s}) for s in seeds}
    full = [s for s in seeds if have[s] == len(GRAPHS) * len(FS)]
    if not set(range(10)) <= set(full):
        print(f"Chưa đủ 10 seed hoàn tất của E0x (đang có: {full}). Chạy lại sau khi E0x xong.")
        return
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("PK_PLAN.md", "pk.py")}
    R = {}
    for g in GRAPHS:
        for f in FS:
            R[(g, f)] = cell([r for r in rows if r["graph"] == g and r["f"] == f])
            print(f"xong {g} f={f:.0%}", flush=True)
    S = sum(0.85 <= R[c]["CP"]["cov"] <= 0.95 for c in R)
    small = [c for c in R if c[1] <= 0.05]
    U = sum(R[c]["CP"]["size"] <= 2.0 for c in small)
    A = sum(R[(g, 0.40)]["CP"]["size"] >= 1.5 * R[(g, 0.02)]["CP"]["size"] for g in GRAPHS)
    if S < 20:
        verdict = "KIỂM TRA CÀI ĐẶT (S trượt) — không diễn giải"
    elif U >= 6 and A >= 3:
        verdict = "GO"
    else:
        verdict = "NO-GO"
    L = [f"# P-K — báo cáo (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA: {sha}. Giao thức: `PK_PLAN.md`.\n",
         f"## Kết luận: **{verdict}**\n",
         f"- S (độ phủ CP trong [0,85; 0,95]): {S}/24 ô\n- U (kích thước CP ≤ 2 ở f ≤ 5%): {U}/8 ô\n- A (kích thước ở 40% ≥ 1,5 × ở 2%): {A}/4 đồ thị\n",
         "## Độ phủ / kích thước tập (test, seed 7–9)\n",
         "| Đồ thị | f | CP | CP-M | pt | pm1 | CP: phủ k=1 / k=8 | CP-M: phủ k=1 / k=8 |", "|---|---|---|---|---|---|---|---|"]
    for (g, f), o in R.items():
        L.append(f"| {g} | {f:.0%} | " + " | ".join(f"{o[n]['cov']:.2f} / {o[n]['size']:.2f}" for n in ("CP", "CP-M", "pt", "pm1")) +
                 f" | {o['CP']['cov_k1']:.2f} / {o['CP']['cov_k8']:.2f} | {o['CP-M']['cov_k1']:.2f} / {o['CP-M']['cov_k8']:.2f} |")
    L.append("\n## Giới hạn\n\n- Hiệu chỉnh và kiểm tra trên cùng đồ thị, cùng SI; chưa có lệch mô hình. Lưới k thưa (5 giá trị).\n")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "PK_REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"Kết luận: {verdict}. Báo cáo: results/PK_REPORT.md", flush=True)


if __name__ == "__main__":
    main()
