"""H0c — kiểm tra ba điều kiện tiền đề của P6 (Đ1 H-a, Đ2 phân hoạch hợp lý, Đ3 H-b). Xem H0c_PLAN.md.

  python h0c.py --smoke      # chạy rất nhỏ để kiểm code
  python h0c.py --workers 8  # chạy chính thức + phân tích + H0c_REPORT.md
"""
import _venv; _venv.ensure()
import argparse
import csv
import datetime as dt
import glob
import hashlib
import json
import os
import time
import warnings
warnings.filterwarnings("ignore")
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import networkx as nx
import pandas as pd
import scipy.sparse as sp
from scipy.sparse.csgraph import shortest_path

import config as C
import h0lib as L
import h0b as B          # dùng lại: ic_steps, si_until, calib_p, kcenter_seq, T_STEPS, LO, HI

SEED = 4040
MUS = [0.1, 0.3, 0.5]
OBS = ["ic_T", "si_t"]
PLACE = ["random", "spread"]
KS = [3, 5]
N_TEST = 100
REASONABLE = [0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0]
CRITS = ["q_inf", "q_full", "conc", "fitk", "cons"]
PRIMARY = "q_inf"
DELTA_ABS, DELTA_REL, ETA2_MIN, PAIRS_MIN = 0.3, 0.10, 0.20, 4
METHODS = ["commjordan", "commlpsi"]
FIELDS = ["obs", "place", "graph", "mu", "k", "cascade", "method", "part_id", "gamma", "pseed", "ed", "f1_1",
          "q_inf", "q_full", "conc", "fitk", "cons", "frac_inf"]


def log(msg):
    os.makedirs("logs", exist_ok=True)
    line = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open("logs/h0c.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ------------------------------------------------------------ tiện ích
def modularity(A, lab):
    """Modularity (Newman) của nhãn lab trên đồ thị vô hướng A (csr)."""
    m2 = A.sum()
    if m2 == 0:
        return 0.0
    Ac = A.tocoo()
    _, li = np.unique(lab, return_inverse=True)
    same = li[Ac.row] == li[Ac.col]
    lin = Ac.data[same].sum()
    deg = np.asarray(A.sum(1)).ravel()
    ds = np.bincount(li, weights=deg)
    return float(lin / m2 - ((ds / m2) ** 2).sum())


def dhondt(counts, k):
    """Phân bổ k tâm theo số node nhiễm mỗi cộng đồng (D'Hondt), không vượt số node nhiễm."""
    m = np.zeros(len(counts), int)
    for _ in range(k):
        q = np.where(m < counts, counts / (m + 1), -1)
        if q.max() < 0:
            break
        m[int(np.argmax(q))] += 1
    return m


def block_lpsi(A, lab, alpha):
    """Nghịch đảo LPSI cho từng khối cộng đồng (bỏ cạnh giữa cộng đồng)."""
    blocks = {}
    for c in np.unique(lab):
        Nc = np.flatnonzero(lab == c)
        Ac = A[Nc][:, Nc]
        d = np.asarray(Ac.sum(1)).ravel(); d[d == 0] = 1
        Dm = sp.diags(1 / np.sqrt(d))
        S = (Dm @ Ac @ Dm).toarray()
        blocks[c] = (Nc, np.linalg.inv(np.eye(len(Nc)) - alpha * S).astype(np.float32))
    return blocks


def make_cascades(A, obs, k, place, truth, n_casc, seed, p):
    n = A.shape[0]; rng = np.random.default_rng(seed); out = []; tries = 0
    tcomms = [np.flatnonzero(truth == c) for c in np.unique(truth)]
    while len(out) < n_casc:
        tries += 1
        if tries > 400 * n_casc:
            raise RuntimeError(f"{obs}/{place} k={k}: không đủ cascade 10-20%")
        if place == "random":
            src = rng.choice(n, k, replace=False)
        else:
            cs = rng.choice(len(tcomms), k, replace=False)
            src = np.array([rng.choice(tcomms[c]) for c in cs])
        inf = B.ic_steps(A, src, p, rng, B.T_STEPS) if obs == "ic_T" else B.si_until(A, src, rng, int(rng.uniform(B.LO, B.HI) * n))
        if B.LO <= inf.size / n <= B.HI:
            out.append((src, inf))
    return out


# ------------------------------------------------------------ một việc = (quan sát, đặt nguồn, đồ thị)
def run_task(obs, place, gid, mu, data_dir, raw_dir, n_test):
    out = os.path.join(raw_dir, f"{obs}__{place}__{gid}.csv")
    if os.path.exists(out):
        return out
    t0 = time.time()
    G = nx.read_edgelist(os.path.join(data_dir, f"{gid}_edges.txt"), nodetype=int)
    G = nx.convert_node_labels_to_integers(G, ordering="sorted")
    A = L.graph_arrays(G); n = A.shape[0]
    P = np.load(os.path.join(data_dir, f"{gid}_parts.npz"))
    labels, gam, pse, truth = P["labels"], P["gamma"], P["pseed"], P["truth"]
    cons, qfull = P["cons"], P["qfull"]
    blocks = [block_lpsi(A, labels[pi], C.LPSI_ALPHA) for pi in range(labels.shape[0])]
    lpsi = L.LPSI(A, C.LPSI_ALPHA)
    rows = []
    for k in KS:
        p = None
        if obs == "ic_T":
            p, _ = B.calib_p(A, k, L.sub_seed(SEED, gid, k, "cal_T"), lambda s, p, r: B.ic_steps(A, s, p, r, B.T_STEPS))
        test = make_cascades(A, obs, k, place, truth, n_test, L.sub_seed(SEED, gid, obs, place, k, "test"), p)
        for ci, (src, inf) in enumerate(test):
            ctx = L.CascadeCtx(A, src, inf)
            Y = -np.ones(n, np.float32); Y[inf] = 1
            base = dict(obs=obs, place=place, graph=gid, mu=mu, k=k, cascade=ci, frac_inf=round(inf.size / n, 4))
            for pi in range(labels.shape[0]):
                lab = labels[pi]; lab_I = lab[inf]
                comms, cnt = np.unique(lab_I, return_counts=True)
                m = dhondt(cnt, k)
                crit = dict(q_inf=modularity(ctx.A_I, lab_I), q_full=float(qfull[pi]),
                            conc=float(np.sort(cnt)[::-1][:k].sum() / inf.size),
                            fitk=-abs(int((cnt >= 0.10 * inf.size).sum()) - k), cons=float(cons[pi]))
                pj, pl = [], []
                for c, mc in zip(comms, m):
                    if mc == 0:
                        continue
                    X = np.flatnonzero(lab_I == c)
                    Ms = shortest_path(ctx.A_I[X][:, X], method="D", unweighted=True)
                    cs, _ = B.kcenter_seq(Ms, mc)
                    pj.extend(X[cs].tolist())
                    Nc, Mi = blocks[pi][c]
                    g = Mi @ Y[Nc]
                    pl.extend(Nc[np.argsort(-g)[:mc]].tolist())
                pr = dict(part_id=pi, gamma=gam[pi], pseed=pse[pi], **crit)
                for meth, sc in (("commjordan", L.score_pos(ctx, np.array(pj))), ("commlpsi", L.score_nodes(ctx, np.array(pl)))):
                    rows.append({**base, **pr, "method": meth, "ed": sc["ed"], "f1_1": sc["f1_1"]})
            cs, _ = B.kcenter_seq(ctx.DIIsub, k)
            sj = L.score_pos(ctx, np.array(cs))
            rows.append({**base, "method": "jordan", "part_id": -1, "ed": sj["ed"], "f1_1": sj["f1_1"]})
            sl = L.score_nodes(ctx, np.argsort(-(lpsi.Minv @ Y.astype(float)))[:k])
            rows.append({**base, "method": "lpsi", "part_id": -1, "ed": sl["ed"], "f1_1": sl["f1_1"]})
    tmp = out + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader()
        for r in rows:
            w.writerow({a: (f"{v:.6g}" if isinstance(v, float) else v) for a, v in r.items()})
    os.replace(tmp, out)
    log(f"[{obs}|{place}] {gid}: XONG {len(rows)} dòng, {time.time() - t0:.0f}s")
    return out


# ------------------------------------------------------------ phân tích theo quy tắc định trước
def delta_cf(E, d):
    a, b = np.arange(0, E.shape[1], 2), np.arange(1, E.shape[1], 2)
    return float(np.mean([E[d, ev].mean() - E[int(np.argmin(E[:, fi].mean(1))), ev].mean() for fi, ev in ((a, b), (b, a))]))


def eta2(E):
    gm = E.mean(); sst = ((E - gm) ** 2).sum()
    return float(E.shape[1] * ((E.mean(1) - gm) ** 2).sum() / sst) if sst > 0 else 0.0


def analyze(raw_dir):
    df = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(raw_dir, "*.csv"))], ignore_index=True)
    R = []
    for (obs, place, meth, gid, k), g in df[df.method.isin(METHODS)].groupby(["obs", "place", "method", "graph", "k"]):
        base = df[(df.obs == obs) & (df.place == place) & (df.graph == gid) & (df.k == k)]
        lv = g[g.gamma > 0]
        E = lv.pivot(index="part_id", columns="cascade", values="ed").sort_index()
        pid = E.index.values; Ev = E.values
        meta = lv.drop_duplicates("part_id").set_index("part_id").loc[pid]
        d = int(np.flatnonzero((meta.gamma.values == 1.0) & (meta.pseed.values == 0))[0])
        rs = np.flatnonzero(np.isin(meta.gamma.values, REASONABLE)); dr = int(np.flatnonzero(rs == d)[0])
        ed_def = Ev[d].mean()
        row = dict(obs=obs, place=place, method=meth, graph=gid, k=k, ed_default=ed_def,
                   eta2_all=eta2(Ev), dcf_all=delta_cf(Ev, d),
                   eta2_reason=eta2(Ev[rs]), dcf_reason=delta_cf(Ev[rs], dr),
                   ed_random=g[g.gamma == -1].ed.mean(), ed_truth=g[g.gamma == -2].ed.mean(),
                   ed_oracle=Ev.min(0).mean(),
                   ed_jordan=base[base.method == "jordan"].ed.mean(), ed_lpsi=base[base.method == "lpsi"].ed.mean())
        for cr in CRITS:
            Cm = lv.pivot(index="part_id", columns="cascade", values=cr).sort_index().values
            # hòa -> phân hoạch có |log γ| nhỏ nhất, rồi seed nhỏ
            tie = np.abs(np.log(meta.gamma.values)) * 10 + meta.pseed.values
            pick = [int(np.lexsort((tie, -Cm[:, j]))[0]) for j in range(Cm.shape[1])]
            row[f"ed_sel_{cr}"] = float(np.mean([Ev[pk, j] for j, pk in enumerate(pick)]))
            rho = [pd.Series(Cm[:, j]).corr(pd.Series(-Ev[:, j]), method="spearman") for j in range(Cm.shape[1])]
            row[f"spear_{cr}"] = float(np.nanmedian(rho))
        thr = max(DELTA_ABS, DELTA_REL * ed_def)
        row["pass_D1"] = bool(row["eta2_all"] >= ETA2_MIN and row["dcf_all"] >= thr)
        row["pass_D2"] = bool(row["eta2_reason"] >= ETA2_MIN and row["dcf_reason"] >= thr)
        row["pass_D3"] = bool(ed_def - row[f"ed_sel_{PRIMARY}"] >= thr)
        row["V2"] = bool(row["ed_random"] > ed_def)
        R.append(row)
    R = pd.DataFrame(R)
    S = (R.groupby(["obs", "place", "method"])
         .agg(n=("k", "size"), V2=("V2", "all"), D1=("pass_D1", "sum"), D2=("pass_D2", "sum"), D3=("pass_D3", "sum"),
              ed_default=("ed_default", "mean"), ed_jordan=("ed_jordan", "mean"), ed_lpsi=("ed_lpsi", "mean"),
              ed_truth=("ed_truth", "mean"), ed_oracle=("ed_oracle", "mean"), ed_sel_q_inf=("ed_sel_q_inf", "mean"),
              eta2_all=("eta2_all", "median"), dcf_all=("dcf_all", "median"),
              eta2_reason=("eta2_reason", "median"), dcf_reason=("dcf_reason", "median"))
         .reset_index())
    for c in ("D1", "D2", "D3"):
        S[f"{c}_ok"] = S.V2 & (S[c] >= PAIRS_MIN)
    os.makedirs("results/summary", exist_ok=True)
    R.to_csv("results/summary/H0c_by_pair.csv", index=False)
    S.to_csv("results/summary/H0c_combos.csv", index=False)
    f = lambda x: f"{x:.2f}"
    ok = lambda b: "✓" if b else "✗"
    out = ["# H0c — Báo cáo (sinh tự động từ CSV thô trên máy chạy)\n",
           f"{dt.datetime.now():%d/%m/%Y %H:%M}. Seed {SEED}. Kế hoạch khóa: xem `logs/h0c.log` (SHA-256 của H0c_PLAN.md và h0c.py).\n",
           "Tổ hợp đạt một điều kiện khi V2 đúng và ≥ 4/6 cặp (đồ thị × k) đạt. Ngưỡng: η² ≥ 0,20 và Δcf ≥ max(0,3 hop; 10%); Đ3 dùng tiêu chí chính `q_inf`.\n",
           "| Quan sát | Đặt nguồn | Bộ định vị | V2 | Đ1 (cặp) | Đ2 (cặp) | Đ3 (cặp) | ED mặc định | ED chọn q_inf | ED Jordan | ED LPSI | ED cộng đồng thật | ED oracle | η² toàn / hợp lý | Δcf toàn / hợp lý |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, s in S.iterrows():
        out.append(f"| {s.obs} | {s.place} | {s.method} | {ok(s.V2)} | {ok(s.D1_ok)} {s.D1}/6 | {ok(s.D2_ok)} {s.D2}/6 | {ok(s.D3_ok)} {s.D3}/6 | "
                   f"{f(s.ed_default)} | {f(s.ed_sel_q_inf)} | {f(s.ed_jordan)} | {f(s.ed_lpsi)} | {f(s.ed_truth)} | {f(s.ed_oracle)} | "
                   f"{f(s.eta2_all)} / {f(s.eta2_reason)} | {f(s.dcf_all)} / {f(s.dcf_reason)} |")
    out.append("\n## Tiêu chí không nhãn (thăm dò): ED khi chọn theo từng tiêu chí, trung bình mọi cặp\n")
    out.append("| Quan sát | Đặt nguồn | Bộ định vị | mặc định | " + " | ".join(CRITS) + " | Spearman trung vị (" + ", ".join(CRITS) + ") |")
    out.append("|---|---|---|---|" + "---|" * len(CRITS) + "---|")
    for (o, pl, me), g in R.groupby(["obs", "place", "method"]):
        out.append(f"| {o} | {pl} | {me} | {f(g.ed_default.mean())} | " + " | ".join(f(g[f'ed_sel_{c}'].mean()) for c in CRITS)
                   + " | " + ", ".join(f(g[f'spear_{c}'].median()) for c in CRITS) + " |")
    any2 = S.D2_ok.any(); any3 = (S.D1_ok & S.D2_ok & S.D3_ok).any()
    verdict = ("GO có điều kiện (có tổ hợp đạt cả Đ1, Đ2, Đ3)" if any3 else
               "Bài toán có nhưng chưa có tiêu chí chọn (đạt Đ2, không đạt Đ3)" if any2 else
               "NO-GO mạnh: không tổ hợp hợp lệ nào đạt Đ2")
    out.append(f"\n**Kết luận theo quy tắc định trước:** {verdict}.\n")
    open("H0c_REPORT.md", "w", encoding="utf-8").write("\n".join(out) + "\n")
    log("Đã viết H0c_REPORT.md")
    log("KẾT LUẬN: " + verdict)


# ------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    root = "smoke" if a.smoke else "."
    data_dir = os.path.join(root, "data"); raw_dir = os.path.join(root, "results", "raw")
    os.makedirs(data_dir, exist_ok=True); os.makedirs(raw_dir, exist_ok=True)
    h = {fn: hashlib.sha256(open(fn, "rb").read()).hexdigest() for fn in ("H0c_PLAN.md", "h0c.py", "h0b.py", "h0lib.py", "config.py")}
    log(f"H0c bắt đầu | smoke={a.smoke} | workers={a.workers} | seed={SEED}")
    for fn, v in h.items():
        log(f"  SHA-256 {fn}: {v}")
    json.dump(h, open(os.path.join(root, "H0c_lock.json"), "w"), indent=1)
    gammas = [0.1, 1.0, 3.0] if a.smoke else C.GAMMAS
    seeds = [0, 1] if a.smoke else C.PART_SEEDS
    graphs = []
    for mu in MUS:
        gid = f"lfr_mu{mu}"
        fp = os.path.join(data_dir, f"{gid}_parts.npz")
        if not os.path.exists(fp):
            G, truth, _ = L.make_lfr(mu, 0, SEED, log)
            nx.write_edgelist(G, os.path.join(data_dir, f"{gid}_edges.txt"), data=False)
            parts = L.make_partitions(G, gammas, seeds)
            dl = [q for q in parts if (q["gamma"], q["seed"]) == (1.0, 0)][0]["labels"]
            allp = parts + L.random_partitions(dl, C.N_RANDOM_PARTS, L.sub_seed(SEED, gid, "rand"))
            allp.append({"gamma": -2.0, "seed": 0, "labels": truth})
            lab = np.stack([q["labels"] for q in allp])
            A = L.graph_arrays(G); nl = len(parts)
            qf = np.array([modularity(A, l) for l in lab])
            cons = np.array([np.mean([L.nmi(lab[i], lab[j]) for j in range(nl) if j != i]) if i < nl else np.nan
                             for i in range(len(lab))])
            np.savez(fp, labels=lab, gamma=np.array([q["gamma"] for q in allp]), pseed=np.array([q["seed"] for q in allp]),
                     truth=truth, qfull=qf, cons=cons)
            log(f"  {gid}: n={G.number_of_nodes()} m={G.number_of_edges()} | {len(np.unique(truth))} cộng đồng thật | "
                f"Q mặc định={qf[[i for i, q in enumerate(allp) if (q['gamma'], q['seed']) == (1.0, 0)][0]]:.3f}")
        graphs.append((gid, mu))
    tasks = [(o, pl, g, m) for o in OBS for pl in PLACE for g, m in graphs]
    log(f"=== {len(tasks)} việc (2 quan sát × 2 đặt nguồn × {len(graphs)} đồ thị), {2 if a.smoke else N_TEST} cascade mỗi k ===")
    t0 = time.time(); done = 0
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(run_task, o, pl, g, m, data_dir, raw_dir, 4 if a.smoke else N_TEST) for o, pl, g, m in tasks]
        for fu in as_completed(futs):
            fu.result(); done += 1
            log(f"--- Tiến độ: {done}/{len(tasks)} ({(time.time() - t0) / 60:.1f} phút) ---")
    if a.smoke:
        os.chdir(root)
    analyze(os.path.join("results", "raw"))
    log("=== H0c XONG ===")


if __name__ == "__main__":
    main()
