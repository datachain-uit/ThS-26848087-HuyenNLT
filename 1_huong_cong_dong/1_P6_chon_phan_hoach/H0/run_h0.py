"""Chạy H0.

  python run_h0.py --smoke        # chạy thử nhỏ (seed riêng), đo thời gian, kiểm tra tất định
  python run_h0.py --stage prepare  # sinh đồ thị + phân hoạch (lượt chính)
  python run_h0.py --stage run      # chạy định vị + chấm điểm (chạy tiếp được nếu bị ngắt)
  python run_h0.py                  # prepare + run

Tham chiếu: H0_PROTOCOL.md.
"""
import _venv; _venv.ensure()
import argparse
import csv
import os
import sys
import time
import datetime as dt
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import networkx as nx

import config as C
import h0lib as L

FIELDS = ["graph", "mu", "k", "p", "frac_inf", "split", "cascade", "method", "part_id",
          "gamma", "pseed", "rho", "ed", "khat", "kerr", "f1_0", "f1_1", "f1_2"]


def setup(smoke):
    root = "smoke" if smoke else "."
    paths = {k: os.path.join(root, v) for k, v in
             dict(data="data", raw="results/raw", logs="logs").items()}
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    paths["log"] = os.path.join(paths["logs"], "h0.log")
    return paths


def make_logger(logfile):
    def log(msg):
        line = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    return log


def settings(smoke):
    if smoke:
        s = C.SMOKE
        return dict(seed=C.SMOKE_SEED, mus=s["mus"], per_mu=s["per_mu"], email=s["email"],
                    gammas=s["gammas"], part_seeds=s["part_seeds"], ks=s["ks"],
                    n_val=s["n_val"], n_test=s["n_test"], n_calib=s["n_calib"])
    return dict(seed=C.MASTER_SEED, mus=C.LFR_MUS, per_mu=C.LFR_PER_MU, email=C.USE_EMAIL_EU,
                gammas=C.GAMMAS, part_seeds=C.PART_SEEDS, ks=C.KS,
                n_val=C.N_VAL, n_test=C.N_TEST, n_calib=C.N_CALIB)


# ------------------------------------------------------------------ prepare
def prepare(S, paths, log):
    log("=== PREPARE: sinh đồ thị và phân hoạch (trước khi sinh cascade) ===")
    graphs = [(f"lfr_mu{mu}_{i}", mu, i) for mu in S["mus"] for i in range(S["per_mu"])]
    if S["email"]:
        graphs.append(("email_eu", -1.0, 0))
    manifest = {}
    for gid, mu, i in graphs:
        t0 = time.time()
        if gid == "email_eu":
            try:
                G, truth = L.load_email_eu(paths["data"])
                meta = {"source": "SNAP email-Eu-core (LCC, undirected)"}
            except Exception as e:
                log(f"  KHÔNG tải được email-Eu-core: {e}. Tải thủ công rồi chạy lại prepare.")
                continue
        else:
            G, truth, meta = L.make_lfr(mu, i, S["seed"], log)
        n, m = G.number_of_nodes(), G.number_of_edges()
        nx.write_edgelist(G, os.path.join(paths["data"], f"{gid}_edges.txt"), data=False)
        np.save(os.path.join(paths["data"], f"{gid}_truth.npy"), truth)
        parts = L.make_partitions(G, S["gammas"], S["part_seeds"])
        dflt = [q for q in parts if (q["gamma"], q["seed"]) == C.DEFAULT_PART]
        if not dflt:
            dflt = [min(parts, key=lambda q: (abs(q["gamma"] - 1.0), q["seed"]))]
        rnd = L.random_partitions(dflt[0]["labels"], C.N_RANDOM_PARTS, L.sub_seed(S["seed"], gid, "rand"))
        allp = parts + rnd
        np.savez(os.path.join(paths["data"], f"{gid}_parts.npz"),
                 labels=np.stack([q["labels"] for q in allp]),
                 gamma=np.array([q["gamma"] for q in allp]),
                 pseed=np.array([q["seed"] for q in allp]))
        ncom = [int(q["labels"].max() + 1) for q in parts]
        nm = [L.nmi(q["labels"], truth) for q in parts]
        manifest[gid] = dict(mu=mu, n=n, m=m, n_truth=int(truth.max() + 1), meta=meta,
                             n_comm_range=[min(ncom), max(ncom)],
                             nmi_range=[round(min(nm), 3), round(max(nm), 3)],
                             sha_edges=L.sha256_file(os.path.join(paths["data"], f"{gid}_edges.txt")),
                             sha_parts=L.sha256_file(os.path.join(paths["data"], f"{gid}_parts.npz")))
        log(f"  {gid}: n={n} m={m} cộng đồng thật={manifest[gid]['n_truth']} | "
            f"số cộng đồng Louvain {ncom and min(ncom)}–{ncom and max(ncom)} | "
            f"NMI {manifest[gid]['nmi_range']} | {time.time()-t0:.1f}s")
    L.save_json(manifest, os.path.join(paths["data"], "manifest.json"))
    log(f"Đã lưu {len(manifest)} đồ thị vào {paths['data']}")
    return manifest


# ------------------------------------------------------------------ run một đồ thị
def run_graph(gid, mu, S, paths):
    log = make_logger(paths["log"])
    out_csv = os.path.join(paths["raw"], f"{gid}.csv")
    if os.path.exists(out_csv):
        log(f"[{gid}] đã có kết quả, bỏ qua")
        return gid, 0.0
    t0 = time.time()
    G = nx.read_edgelist(os.path.join(paths["data"], f"{gid}_edges.txt"), nodetype=int)
    G = nx.relabel_nodes(G, {v: v for v in G.nodes()})
    G = nx.convert_node_labels_to_integers(G, ordering="sorted") if sorted(G.nodes()) != list(range(G.number_of_nodes())) else G
    A = L.graph_arrays(G)
    P = np.load(os.path.join(paths["data"], f"{gid}_parts.npz"))
    labels, gam, pse = P["labels"], P["gamma"], P["pseed"]
    n_louv = int((gam >= 0).sum())
    dflt_idx = int(np.flatnonzero((gam == C.DEFAULT_PART[0]) & (pse == C.DEFAULT_PART[1]))[0]) \
        if ((gam == C.DEFAULT_PART[0]) & (pse == C.DEFAULT_PART[1])).any() else 0
    lpsi = L.LPSI(A, C.LPSI_ALPHA)
    rows = []
    for k in S["ks"]:
        p, acc = L.calibrate_p(A, k, S["n_calib"], L.sub_seed(S["seed"], gid, k, "calib"), log)
        log(f"[{gid}] k={k}: p={p:.4f}, tỉ lệ cascade đạt 10-20% = {acc:.2f}")
        # --- chọn rho trên val ---
        val = L.gen_cascades(A, k, p, S["n_val"], L.sub_seed(S["seed"], gid, k, "val"))
        vctx = [L.CascadeCtx(A, s, i) for s, i in val]
        def val_stats(fn, grid):
            out = {}
            for key in grid:
                sc = [fn(c, key) for c in vctx]
                out[key] = (float(np.mean([x[C.RHO_CRITERION] for x in sc])),
                            float(np.nanmean([x["ed"] for x in sc])), float(np.mean([x["kerr"] for x in sc])))
            return out
        grid_cj = list(C.RHOS)
        v_cj = val_stats(lambda c, key: L.score_pos(c, L.comm_jordan(c, labels[dflt_idx], key)), grid_cj)
        v_j = val_stats(lambda c, r: L.score_pos(c, L.jordan_global(c, r)), C.RHOS)
        sgn = 1 if C.RHO_CRITERION == "ed" else -1   # ED: nhỏ là tốt; F1: lớn là tốt
        rho_cj = min(grid_cj, key=lambda key: (sgn * v_cj[key][0], key))
        rho_j = min(C.RHOS, key=lambda r: (sgn * v_j[r][0], r))
        b = v_cj[rho_cj]
        log(f"[{gid}] k={k}: val CommJordan chọn rho={rho_cj}: ED={b[1]:.2f} |k̂-k|={b[2]:.1f}")
        b = v_j[rho_j]
        log(f"[{gid}] k={k}: val Jordan     chọn rho={rho_j}: ED={b[1]:.2f} |k̂-k|={b[2]:.1f}")
        # --- test ---
        test = L.gen_cascades(A, k, p, S["n_test"], L.sub_seed(S["seed"], gid, k, "test"))
        for ci, (src, inf) in enumerate(test):
            ctx = L.CascadeCtx(A, src, inf)
            base = dict(graph=gid, mu=mu, k=k, p=round(p, 5), frac_inf=round(len(inf) / A.shape[0], 4),
                        split="test", cascade=ci)
            for pi in range(labels.shape[0]):
                sc = L.score_pos(ctx, L.comm_jordan(ctx, labels[pi], rho_cj))
                rows.append({**base, "method": "commjordan" if pi < n_louv else "random_part",
                             "part_id": pi, "gamma": gam[pi], "pseed": pse[pi], "rho": rho_cj, **sc})
            sc = L.score_pos(ctx, L.jordan_global(ctx, rho_j))
            rows.append({**base, "method": "jordan", "part_id": -1, "gamma": np.nan, "pseed": -1, "rho": rho_j, **sc})
            sc = L.score_nodes(ctx, lpsi.predict(inf))
            rows.append({**base, "method": "lpsi", "part_id": -1, "gamma": np.nan, "pseed": -1, "rho": np.nan, **sc})
            if (ci + 1) % 50 == 0 or ci + 1 == len(test):
                log(f"[{gid}] k={k}: {ci+1}/{len(test)} cascade test xong ({time.time()-t0:.0f}s)")
    tmp = out_csv + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})
    os.replace(tmp, out_csv)
    el = time.time() - t0
    log(f"[{gid}] XONG: {len(rows)} dòng, {el:.0f}s")
    return gid, el


def run_all(S, paths, log, workers):
    import json
    manifest = json.load(open(os.path.join(paths["data"], "manifest.json"), encoding="utf-8"))
    log(f"=== RUN: {len(manifest)} đồ thị, {workers} tiến trình ===")
    t0 = time.time()
    if workers <= 1:
        for gid, m in manifest.items():
            run_graph(gid, m["mu"], S, paths)
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(run_graph, gid, m["mu"], S, paths): gid for gid, m in manifest.items()}
            done = 0
            for f in as_completed(futs):
                gid, el = f.result()
                done += 1
                log(f"--- Tiến độ: {done}/{len(futs)} đồ thị ({(time.time()-t0)/60:.1f} phút) ---")
    log(f"=== RUN xong sau {(time.time()-t0)/60:.1f} phút ===")


def smoke_extra(S, paths, log):
    """Kiểm tra tất định + ước lượng thời gian lượt chính."""
    import pandas as pd
    import json
    manifest = json.load(open(os.path.join(paths["data"], "manifest.json"), encoding="utf-8"))
    gid = next(iter(manifest))
    df1 = pd.read_csv(os.path.join(paths["raw"], f"{gid}.csv"))
    h1 = L.sha256_file(os.path.join(paths["raw"], f"{gid}.csv"))
    os.rename(os.path.join(paths["raw"], f"{gid}.csv"), os.path.join(paths["raw"], f"{gid}_run1.csv"))
    t0 = time.time()
    run_graph(gid, manifest[gid]["mu"], S, paths)
    el = time.time() - t0
    h2 = L.sha256_file(os.path.join(paths["raw"], f"{gid}.csv"))
    log(f"Tất định: {'ĐẠT' if h1 == h2 else 'KHÔNG ĐẠT'} (hash lần 1 == lần 2: {h1 == h2})")
    n_units = len(S["ks"]) * S["n_test"] * (len(S["gammas"]) * len(S["part_seeds"]) + C.N_RANDOM_PARTS)
    full_units = len(C.KS) * C.N_TEST * (len(C.GAMMAS) * len(C.PART_SEEDS) + C.N_RANDOM_PARTS)
    per_graph = el * full_units / n_units
    n_graphs = len(C.LFR_MUS) * C.LFR_PER_MU + (1 if C.USE_EMAIL_EU else 0)
    workers = max(1, (os.cpu_count() or 2) - 1)
    log(f"Ước lượng lượt chính: ~{per_graph/60:.1f} phút/đồ thị x {n_graphs} đồ thị "
        f"= ~{per_graph*n_graphs/3600:.1f} CPU-giờ; với {workers} tiến trình ~{per_graph*n_graphs/3600/workers:.1f} giờ")
    cj = df1[df1.method == "commjordan"]
    log("Tóm tắt chạy thử (chỉ để kiểm code, KHÔNG dùng cho H-a):")
    for (k,), g in df1.groupby(["k"]):
        log(f"  k={k}: ED CommJordan TB={g[g.method=='commjordan'].ed.mean():.2f} | "
            f"phân hoạch ngẫu nhiên={g[g.method=='random_part'].ed.mean():.2f} | "
            f"Jordan={g[g.method=='jordan'].ed.mean():.2f} | LPSI={g[g.method=='lpsi'].ed.mean():.2f} | "
            f"|k̂-k| CommJordan={g[g.method=='commjordan'].kerr.mean():.2f} | tỉ lệ nhiễm TB={g.frac_inf.mean():.3f}")
    rnd_worse = df1[df1.method == "random_part"].ed.mean() > cj.ed.mean()
    log(f"Kiểm tra hợp lý: phân hoạch ngẫu nhiên kém hơn Louvain: {'ĐẠT' if rnd_worse else 'KHÔNG ĐẠT'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--stage", choices=["prepare", "run", "all"], default="all")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    S = settings(a.smoke)
    paths = setup(a.smoke)
    log = make_logger(paths["log"])
    log(f"H0 bắt đầu | smoke={a.smoke} | seed={S['seed']} | python {sys.version.split()[0]} | networkx {nx.__version__} | CPU {os.cpu_count()}")
    if a.smoke:
        prepare(S, paths, log)
        run_all(S, paths, log, 1)
        smoke_extra(S, paths, log)
        log("CHẠY THỬ XONG. Xem smoke/logs/h0.log")
        return
    if a.stage in ("prepare", "all"):
        if not os.path.exists("H0_PROTOCOL.sha256"):
            log("DỪNG: chưa khóa giao thức (thiếu H0_PROTOCOL.sha256). Chạy: python lock_protocol.py")
            return
        prepare(S, paths, log)
    if a.stage in ("run", "all"):
        run_all(S, paths, log, a.workers)


if __name__ == "__main__":
    main()
