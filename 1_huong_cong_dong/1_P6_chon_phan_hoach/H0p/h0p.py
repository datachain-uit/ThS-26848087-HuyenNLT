"""H0' (H0p) — thí nghiệm tiền đề H0, sửa hai lỗi đo. Xem H0p_PROTOCOL.md.

  python h0p.py --smoke              # chạy rất nhỏ (seed riêng) để kiểm code và ước lượng thời gian
  python h0p.py --workers 20         # chạy chính thức + phân tích + H0p_REPORT.md
  python h0p.py --analyze            # chỉ phân tích lại CSV thô đã có

Dùng lại: đồ thị + phân hoạch của H0 (data/ chép từ H0/data/), h0lib.py và config.py của H0,
h0b.py ĐÃ SỬA (ic_steps, si_until, calib_p, kcenter_seq) từ H0c_fix.
"""
import _venv; _venv.ensure()
import argparse
import csv
import datetime as dt
import glob
import hashlib
import json
import math
import os
import time
import warnings
warnings.filterwarnings("ignore")
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import networkx as nx
import pandas as pd
from scipy.sparse.csgraph import shortest_path

import config as C
import h0lib as L
import h0b as B

SEED = 5050                    # seed cascade mới (H0: 2026, H0b: 3030, H0c: 4040)
SMOKE_SEED = 9191
OBS = ["si_t", "ic_T"]
KS = [1, 3, 5]
N_TEST = 200
HA_ABS, HA_REL, HA_ETA2 = 0.3, 0.10, 0.20
HA_K_PASS, HA_GRAPHS = 2, 11   # đồ thị đạt khi >= 2/3 k; H-a đạt khi >= 11/16 đồ thị
HB_RHO, HB_GRAPHS = 0.5, 9     # H-b đạt khi |rho| < 0,5 trên >= 9/16 đồ thị
FIELDS = ["obs", "graph", "mu", "k", "p", "cascade", "frac_inf", "method", "part_id", "gamma", "pseed",
          "ed", "f1_0", "f1_1", "f1_2"]
LOCK_FILES = ("H0p_PROTOCOL.md", "h0p.py", "h0b.py", "h0lib.py", "config.py")


def log(msg, root="."):
    os.makedirs(os.path.join(root, "logs"), exist_ok=True)
    line = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(os.path.join(root, "logs", "h0p.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ------------------------------------------------------------ bộ định vị khi biết trước k
def dhondt(counts, k):
    """Phân bổ k tâm theo số node nhiễm mỗi cộng đồng (D'Hondt), không vượt số node nhiễm."""
    m = np.zeros(len(counts), int)
    for _ in range(k):
        q = np.where(m < counts, counts / (m + 1), -1)
        if q.max() < 0:
            break
        m[int(np.argmax(q))] += 1
    return m


def comm_jordan_k(ctx, labels, k):
    """CommJordan biết k: D'Hondt + greedy k-center (đã sửa) trên đồ thị con nhiễm của từng cộng đồng.
    Trả về vị trí trong tập nhiễm I."""
    lab_I = labels[ctx.I]
    comms, cnt = np.unique(lab_I, return_counts=True)
    m = dhondt(cnt, k)
    pred = []
    for c, mc in zip(comms, m):
        if mc == 0:
            continue
        X = np.flatnonzero(lab_I == c)
        Ms = shortest_path(ctx.A_I[X][:, X], method="D", unweighted=True)
        cs, _ = B.kcenter_seq(Ms, mc)
        pred.extend(X[cs].tolist())
    return np.array(pred)


def make_cascades(A, obs, k, n_casc, seed, p):
    n = A.shape[0]; rng = np.random.default_rng(seed); out = []; tries = 0
    while len(out) < n_casc:
        tries += 1
        if tries > 400 * n_casc:
            raise RuntimeError(f"{obs} k={k}: không đủ cascade 10-20%")
        src = rng.choice(n, k, replace=False)
        if obs == "ic_T":
            inf = B.ic_steps(A, src, p, rng, B.T_STEPS)
        else:
            inf = B.si_until(A, src, rng, int(rng.uniform(B.LO, B.HI) * n))
        if B.LO <= inf.size / n <= B.HI:
            out.append((src, inf))
    return out


# ------------------------------------------------------------ một việc = (mô hình quan sát, đồ thị, k)
def run_task(obs, gid, mu, k, root, seed, n_test):
    raw = os.path.join(root, "results", "raw")
    out = os.path.join(raw, f"{obs}__{gid}__k{k}.csv")
    if os.path.exists(out):
        return out, 0.0
    t0 = time.time()
    G = nx.read_edgelist(os.path.join("data", f"{gid}_edges.txt"), nodetype=int)
    G = nx.convert_node_labels_to_integers(G, ordering="sorted")
    A = L.graph_arrays(G); n = A.shape[0]
    P = np.load(os.path.join("data", f"{gid}_parts.npz"))
    labels = list(P["labels"]); gam = list(P["gamma"]); pse = list(P["pseed"])
    labels.append(np.load(os.path.join("data", f"{gid}_truth.npy"))); gam.append(-2.0); pse.append(0)
    lpsi = L.LPSI(A, C.LPSI_ALPHA)
    p = None
    if obs == "ic_T":
        p, _ = B.calib_p(A, k, L.sub_seed(seed, gid, k, "cal_T"),
                         lambda s, pp, r: B.ic_steps(A, s, pp, r, B.T_STEPS))
    casc = make_cascades(A, obs, k, n_test, L.sub_seed(seed, gid, obs, k, "test"), p)
    rows = []
    for ci, (src, inf) in enumerate(casc):
        ctx = L.CascadeCtx(A, src, inf)
        base = dict(obs=obs, graph=gid, mu=mu, k=k, p="" if p is None else round(p, 5), cascade=ci,
                    frac_inf=round(inf.size / n, 4))
        for pi, lab in enumerate(labels):
            meth = "commjordan" if gam[pi] > 0 else ("random_part" if gam[pi] == -1 else "truth_part")
            sc = L.score_pos(ctx, comm_jordan_k(ctx, lab, k))
            rows.append({**base, "method": meth, "part_id": pi, "gamma": gam[pi], "pseed": pse[pi],
                         **{m_: sc[m_] for m_ in ("ed", "f1_0", "f1_1", "f1_2")}})
        sc = L.score_pos(ctx, np.array(B.kcenter_seq(ctx.DIIsub, k)[0]))
        rows.append({**base, "method": "jordan", "part_id": -1, **{m_: sc[m_] for m_ in ("ed", "f1_0", "f1_1", "f1_2")}})
        Y = -np.ones(n); Y[inf] = 1.0
        sc = L.score_nodes(ctx, np.argsort(-(lpsi.Minv @ Y))[:k])
        rows.append({**base, "method": "lpsi", "part_id": -1, **{m_: sc[m_] for m_ in ("ed", "f1_0", "f1_1", "f1_2")}})
    tmp = out + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader()
        for r in rows:
            w.writerow({a: (f"{v:.6g}" if isinstance(v, float) else v) for a, v in r.items()})
    os.replace(tmp, out)
    el = time.time() - t0
    log(f"[{obs}] {gid} k={k}: XONG {len(rows)} dòng, p={p}, {el:.0f}s", root)
    return out, el


# ------------------------------------------------------------ V1: kiểm tra cây
def tree_check(obs, seed):
    G = nx.balanced_tree(3, 7); A = L.graph_arrays(G)
    src = np.array([0]); lo, hi = 100, 200; rng = np.random.default_rng(seed)

    def sim(p):
        if obs == "ic_T":
            return B.ic_steps(A, src, p, rng, 12)     # cây sâu 7: 12 bước như H0b
        return B.si_until(A, src, rng, int(rng.uniform(lo, hi)))
    p_best = None
    if obs == "ic_T":
        best = -1
        for p in np.linspace(0.3, 1.0, 29):
            acc = np.mean([lo <= sim(p).size <= hi for _ in range(40)])
            if acc > best:
                best, p_best = acc, p
    casc = []; tries = 0
    while len(casc) < 100 and tries < 20000:
        tries += 1
        I = sim(p_best)
        if lo <= I.size <= hi:
            casc.append(I)
    eds = np.array([L.score_pos(c, np.array(B.kcenter_seq(c.DIIsub, 1)[0]))["ed"]
                    for c in (L.CascadeCtx(A, src, I) for I in casc)])
    return dict(ed_mean=float(eds.mean()), pct_ed0=float((eds == 0).mean() * 100), n=len(eds),
                pass_=bool(eds.mean() <= 1.0))


# ------------------------------------------------------------ phân tích
def eta2(E):
    gm = E.mean(); sst = ((E - gm) ** 2).sum()
    return float(E.shape[1] * ((E.mean(1) - gm) ** 2).sum() / sst) if sst > 0 else 0.0


def delta_cf(E, d):
    a, b = np.arange(0, E.shape[1], 2), np.arange(1, E.shape[1], 2)
    return float(np.mean([E[d, ev].mean() - E[int(np.argmin(E[:, fi].mean(1))), ev].mean()
                          for fi, ev in ((a, b), (b, a))]))


def spearman(x, y):
    return float(pd.Series(x).rank().corr(pd.Series(y).rank()))


def analyze(root, tree, n_graphs_expected):
    df = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(root, "results", "raw", "*.csv"))],
                   ignore_index=True)
    graphs = sorted(df.graph.unique())
    truth = {g: np.load(os.path.join("data", f"{g}_truth.npy")) for g in graphs}
    parts = {g: np.load(os.path.join("data", f"{g}_parts.npz")) for g in graphs}
    RA, RB, V2 = [], [], {}
    for obs in OBS:
        d_o = df[df.obs == obs]
        if d_o.empty:
            continue
        v2_r, v2_d = [], []
        for gid in graphs:
            g = d_o[d_o.graph == gid]
            P = parts[gid]; gam, pse = P["gamma"], P["pseed"]
            n_louv = int((gam > 0).sum()); d = int(np.flatnonzero((gam == 1.0) & (pse == 0))[0])
            for k, gk in g.groupby("k"):
                cj = gk[gk.method == "commjordan"]
                E = cj.pivot(index="part_id", columns="cascade", values="ed").sort_index()
                assert list(E.index) == list(range(n_louv))
                E = E.values
                ed_def = float(E[d].mean()); dc = delta_cf(E, d); e2 = eta2(E)
                dn = ed_def - float(E.mean(1).min())
                thr = min(HA_ABS, HA_REL * ed_def); thr_strict = max(HA_ABS, HA_REL * ed_def)
                ed_rnd = float(gk[gk.method == "random_part"].ed.mean())
                v2_r.append(ed_rnd); v2_d.append(ed_def)
                RA.append(dict(obs=obs, graph=gid, mu=gk.mu.iloc[0], k=k, ed_default=ed_def,
                               ed_best=float(E.mean(1).min()), best_gamma=float(gam[int(np.argmin(E.mean(1)))]),
                               delta_cf=dc, delta_naive=dn, eta2=e2,
                               pass_=bool(e2 >= HA_ETA2 and dc >= thr),
                               pass_strict=bool(e2 >= HA_ETA2 and dc >= thr_strict),
                               pass_naive=bool(e2 >= HA_ETA2 and dn >= thr),
                               ed_random=ed_rnd, ed_truth=float(gk[gk.method == "truth_part"].ed.mean()),
                               ed_jordan=float(gk[gk.method == "jordan"].ed.mean()),
                               ed_lpsi=float(gk[gk.method == "lpsi"].ed.mean()),
                               ed_oracle=float(E.min(0).mean()),
                               f1_default=float(cj[cj.part_id == d].f1_1.mean()),
                               f1_jordan=float(gk[gk.method == "jordan"].f1_1.mean()),
                               f1_lpsi=float(gk[gk.method == "lpsi"].f1_1.mean()),
                               frac_inf=float(gk.frac_inf.mean())))
            cj = g[g.method == "commjordan"]
            edp = cj.groupby("part_id").ed.mean().reindex(range(n_louv)).values
            nm = np.array([L.nmi(P["labels"][i], truth[gid]) for i in range(n_louv)])
            rho = spearman(nm, edp)
            RB.append(dict(obs=obs, graph=gid, spearman=rho, nmi_min=nm.min(), nmi_max=nm.max(),
                           pass_=bool(abs(rho) < HB_RHO)))
        V2[obs] = dict(ed_random=float(np.mean(v2_r)), ed_default=float(np.mean(v2_d)),
                       pass_=bool(np.mean(v2_r) > np.mean(v2_d)))
    A_ = pd.DataFrame(RA); B_ = pd.DataFrame(RB)
    os.makedirs(os.path.join(root, "results", "summary"), exist_ok=True)
    A_.to_csv(os.path.join(root, "results", "summary", "Ha_by_obs_graph_k.csv"), index=False)
    B_.to_csv(os.path.join(root, "results", "summary", "Hb_by_obs_graph.csv"), index=False)
    gam_tab = (df[df.method == "commjordan"].groupby(["obs", "mu", "gamma"]).ed.mean().reset_index())
    gam_tab.to_csv(os.path.join(root, "results", "summary", "ed_by_gamma.csv"), index=False)

    S = {}
    for obs in V2:
        a = A_[A_.obs == obs]
        gp = a.groupby("graph").agg(k_pass=("pass_", "sum"), k_strict=("pass_strict", "sum"),
                                     k_naive=("pass_naive", "sum"))
        b = B_[B_.obs == obs]
        S[obs] = dict(valid=tree[obs]["pass_"] and V2[obs]["pass_"],
                      ha_graphs=int((gp.k_pass >= HA_K_PASS).sum()),
                      ha_strict=int((gp.k_strict >= HA_K_PASS).sum()),
                      ha_naive=int((gp.k_naive >= HA_K_PASS).sum()),
                      n_graphs=len(gp), hb_graphs=int(b.pass_.sum()))
        S[obs]["ha_pass"] = S[obs]["ha_graphs"] >= HA_GRAPHS
        S[obs]["hb_pass"] = S[obs]["hb_graphs"] >= HB_GRAPHS
    valid = [o for o in S if S[o]["valid"]]
    if len(valid) == 2 and all(S[o]["ha_pass"] for o in valid):
        verdict = "GO (H-a đạt ở cả hai mô hình quan sát hợp lệ)"
    elif len(valid) == 2 and not any(S[o]["ha_pass"] for o in valid):
        verdict = "NO-GO (H-a không đạt ở cả hai mô hình quan sát hợp lệ)"
    else:
        verdict = "Chưa kết luận — trình GVHD (" + ("chỉ " + ", ".join(valid) + " hợp lệ" if len(valid) < 2
                                                   else "H-a đạt ở một mô hình, không đạt ở mô hình kia") + ")"
    json.dump(dict(tree=tree, V2=V2, summary=S, verdict=verdict),
              open(os.path.join(root, "results", "summary", "H0p_summary.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    write_report(root, A_, B_, S, tree, V2, verdict, n_graphs_expected)
    log("KẾT LUẬN: " + verdict, root)
    return verdict


def write_report(root, A_, B_, S, tree, V2, verdict, n_exp):
    f2 = lambda x: "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.2f}"
    ok = lambda b: "✓" if b else "✗"
    o = ["# H0' (H0p) — Báo cáo (sinh tự động từ CSV thô trên máy chạy)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. Seed cascade {SEED}. Giao thức: `H0p_PROTOCOL.md` "
         f"(SHA-256 trong `H0p_lock.json`). Đồ thị và phân hoạch: của H0.\n",
         f"## Kết luận theo quy tắc định trước\n\n**{verdict}**\n",
         "## 1. Kiểm tra hợp lệ và tóm tắt\n",
         "| Mô hình quan sát | V1 cây: ED (đoán trúng %) | V2: ED ngẫu nhiên / mặc định | Hợp lệ | H-a: số đồ thị đạt | H-a đạt (≥ 11) | H-b: số đồ thị đạt | H-b đạt (≥ 9) |",
         "|---|---|---|---|---|---|---|---|"]
    for obs, s in S.items():
        t = tree[obs]; v = V2[obs]
        o.append(f"| {obs} | {f2(t['ed_mean'])} ({t['pct_ed0']:.0f}%) {ok(t['pass_'])} | "
                 f"{f2(v['ed_random'])} / {f2(v['ed_default'])} {ok(v['pass_'])} | {ok(s['valid'])} | "
                 f"{s['ha_graphs']}/{s['n_graphs']} | {ok(s['ha_pass'])} | {s['hb_graphs']}/{s['n_graphs']} | {ok(s['hb_pass'])} |")
    if any(S[o_]["n_graphs"] < n_exp for o_ in S):
        o.append(f"\n> Cảnh báo: chưa đủ {n_exp} đồ thị trong CSV thô — kết quả chưa hoàn chỉnh.")
    o += ["\nCách đọc phụ của H-a (không dùng kết luận): số đồ thị đạt khi dùng ngưỡng chặt max(0,3; 10%) / Δ đơn giản:"]
    for obs, s in S.items():
        o.append(f"- {obs}: {s['ha_strict']} / {s['ha_naive']}")
    o += ["\n## 2. H-a theo (đồ thị, k)\n",
          "Đạt khi η² ≥ 0,20 và Δ_cf ≥ min(0,3; 10% ED mặc định).\n",
          "| Quan sát | Đồ thị | k | ED mặc định | ED tốt nhất (γ) | Δ_cf | η² | ED ngẫu nhiên | ED thật | ED Jordan | ED LPSI | Đạt |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in A_.sort_values(["obs", "mu", "graph", "k"]).iterrows():
        o.append(f"| {r.obs} | {r.graph} | {r.k} | {f2(r.ed_default)} | {f2(r.ed_best)} ({r.best_gamma:g}) | "
                 f"{f2(r.delta_cf)} | {f2(r.eta2)} | {f2(r.ed_random)} | {f2(r.ed_truth)} | {f2(r.ed_jordan)} | "
                 f"{f2(r.ed_lpsi)} | {ok(r.pass_)} |")
    o += ["\n## 3. H-b: NMI và ED\n", "| Quan sát | Đồ thị | Spearman ρ(NMI, ED) | Khoảng NMI | \\|ρ\\| < 0,5 |",
          "|---|---|---|---|---|"]
    for _, r in B_.sort_values(["obs", "graph"]).iterrows():
        o.append(f"| {r.obs} | {r.graph} | {f2(r.spearman)} | {f2(r.nmi_min)}–{f2(r.nmi_max)} | {ok(r.pass_)} |")
    o += ["\n## 4. So sánh bộ định vị (trung bình theo mô hình quan sát, μ, k)\n",
          "ED oracle = phân hoạch tốt nhất cho từng cascade, có độ chệch chọn lọc, chỉ để tham khảo.\n",
          "| Quan sát | μ | k | ED mặc định | ED oracle | ED thật | ED ngẫu nhiên | ED Jordan | ED LPSI | F1@1 mặc định | F1@1 Jordan | F1@1 LPSI | Tỉ lệ nhiễm |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    M = A_.groupby(["obs", "mu", "k"]).mean(numeric_only=True).reset_index()
    for _, r in M.iterrows():
        o.append(f"| {r.obs} | {r.mu:g} | {int(r.k)} | {f2(r.ed_default)} | {f2(r.ed_oracle)} | {f2(r.ed_truth)} | "
                 f"{f2(r.ed_random)} | {f2(r.ed_jordan)} | {f2(r.ed_lpsi)} | {f2(r.f1_default)} | {f2(r.f1_jordan)} | "
                 f"{f2(r.f1_lpsi)} | {r.frac_inf:.3f} |")
    o += ["\n## 5. Khác H0 ở đâu\n",
          "- Quan sát: IC dừng sau 4 bước (`ic_T`) và SI chụp khi nhiễm 10–20% (`si_t`), thay cho IC chạy đến hết.",
          "- Số nguồn biết trước k: CommJordan phân bổ k tâm theo D'Hondt; Jordan và LPSI lấy đúng k. Không còn chọn ρ theo ED.",
          "- k-center dùng bản đã sửa cho đồ thị con đứt mảnh (`H0c_fix/BUGFIX.md`).",
          "- Ngưỡng Δ của H-a đọc đúng chữ \"hoặc\" của cô: min(0,3 hop; 10% ED mặc định).",
          "- Giữ nguyên: 16 đồ thị, 55 phân hoạch, k ∈ {1, 3, 5}, 200 cascade, 10–20% nhiễm, η² ≥ 0,20, quy tắc 2/3."]
    open(os.path.join(root, "H0p_REPORT.md"), "w", encoding="utf-8").write("\n".join(o) + "\n")
    log("Đã viết H0p_REPORT.md", root)


# ------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    a = ap.parse_args()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    root = "smoke" if a.smoke else "."
    os.makedirs(os.path.join(root, "results", "raw"), exist_ok=True)
    seed = SMOKE_SEED if a.smoke else SEED
    manifest = json.load(open(os.path.join("data", "manifest.json"), encoding="utf-8"))
    graphs = [(g, m["mu"]) for g, m in manifest.items()
              if os.path.exists(os.path.join("data", f"{g}_parts.npz"))]
    if a.smoke:
        graphs = graphs[:2]
    n_test = 6 if a.smoke else N_TEST
    if not a.analyze:
        h = {fn: hashlib.sha256(open(fn, "rb").read()).hexdigest() for fn in LOCK_FILES}
        log(f"H0p bắt đầu | smoke={a.smoke} | workers={a.workers} | seed={seed} | {len(graphs)} đồ thị | "
            f"networkx {nx.__version__}", root)
        for fn, v in h.items():
            log(f"  SHA-256 {fn}: {v}", root)
        if not a.smoke:
            json.dump(dict(time=dt.datetime.now().isoformat(timespec="seconds"), sha256=h),
                      open("H0p_lock.json", "w"), indent=1)
    tree_path = os.path.join(root, "results", "tree_check.json")
    if os.path.exists(tree_path):
        tree = json.load(open(tree_path, encoding="utf-8"))
    else:
        log("V1: kiểm tra cây theo từng mô hình quan sát...", root)
        tree = {o_: tree_check(o_, L.sub_seed(seed, "tree", o_)) for o_ in OBS}
        json.dump(tree, open(tree_path, "w"), indent=1)
    for o_, t in tree.items():
        log(f"  cây | {o_}: ED TB={t['ed_mean']:.2f}, đoán trúng {t['pct_ed0']:.0f}% -> {'ĐẠT' if t['pass_'] else 'KHÔNG ĐẠT'}", root)
    if not a.analyze:
        # việc lớn trước (email_eu có nhiều cạnh nhất, k lớn chậm hơn) để cân tải
        tasks = sorted([(o_, g, m, k) for o_ in OBS for g, m in graphs for k in KS],
                       key=lambda t: (t[1] != "email_eu", -t[3]))
        log(f"=== {len(tasks)} việc ({len(OBS)} quan sát × {len(graphs)} đồ thị × {len(KS)} k), {n_test} cascade mỗi việc ===", root)
        t0 = time.time(); done = 0
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            futs = [ex.submit(run_task, o_, g, m, k, root, seed, n_test) for o_, g, m, k in tasks]
            for fu in as_completed(futs):
                fu.result(); done += 1
                el = (time.time() - t0) / 60
                log(f"--- Tiến độ: {done}/{len(tasks)} ({el:.1f} phút; còn ~{el / done * (len(tasks) - done):.0f} phút) ---", root)
    analyze(root, tree, len(graphs))
    log("=== H0p XONG ===", root)


if __name__ == "__main__":
    main()
