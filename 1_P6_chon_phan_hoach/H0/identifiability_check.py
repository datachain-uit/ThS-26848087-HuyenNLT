"""Kiểm tra phụ (không thuộc H-a): so khả năng đoán trúng nguồn khi IC chạy đến hết (thiết kế của cô)
với IC dừng sau T bước. Dùng seed riêng (SMOKE_SEED), không chạm dữ liệu lượt chính.
Kết quả ghi results/summary/identifiability.json để báo cáo trích."""
import _venv; _venv.ensure()
import json
import os

import numpy as np
import networkx as nx

import config as C
import h0lib as L


def ic_steps(A, src, p, rng, T):
    ip, ix = A.indptr, A.indices
    act = np.zeros(A.shape[0], bool); act[src] = True; fr = list(src)
    for _ in range(T):
        new = []
        for u in fr:
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[~act[nb]]
            h = nb[rng.random(nb.size) < p]; act[h] = True; new += h.tolist()
        fr = new
    return np.flatnonzero(act)


def measure(G, p, T, n=100, seed=1):
    A = L.graph_arrays(G); rng = np.random.default_rng(seed); eds = []; tries = 0
    lo, hi = C.FRAC_RANGE
    while len(eds) < n and tries < 200 * n:
        tries += 1
        s = rng.choice(A.shape[0], 1, replace=False)
        I = ic_steps(A, s, p, rng, T) if T else L.simulate_ic(A, s, p, rng)
        if not (lo <= I.size / A.shape[0] <= hi):
            continue
        c = L.CascadeCtx(A, s, I)
        eds.append(L.score_pos(c, np.array(L.kcenter(c.DIIsub, np.inf)[:1]))["ed"])
    eds = np.array(eds)
    return dict(n=len(eds), p=p, T=T, ed_mean=float(eds.mean()), pct_ed0=float((eds == 0).mean() * 100))


tree = nx.random_labeled_tree(500, seed=C.SMOKE_SEED)
lfr = nx.LFR_benchmark_graph(1000, mu=0.3, seed=11, **C.LFR_PARAMS)
lfr = nx.convert_node_labels_to_integers(lfr.subgraph(max(nx.connected_components(lfr), key=len)).copy())
out = {
    "tree_ic_full": measure(tree, 0.9, None),
    "tree_ic_T6": measure(tree, 1.0, 6),
    "lfr_mu0.3_ic_full": measure(lfr, 0.09, None),
    "lfr_mu0.3_ic_p0.3_T3": measure(lfr, 0.3, 3),
}
for k, v in out.items():
    print(f"{k:24s} ED TB={v['ed_mean']:.2f} | đoán trúng (ED=0): {v['pct_ed0']:.0f}% | {v['n']} cascade", flush=True)
os.makedirs("results/summary", exist_ok=True)
json.dump(out, open("results/summary/identifiability.json", "w"), indent=1)
print("Đã lưu results/summary/identifiability.json")
