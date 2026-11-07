"""Kiểm tra hợp lý (H0_PROTOCOL.md Mục 10): cây ngẫu nhiên, 1 nguồn, snapshot đầy đủ -> Jordan center cho ED nhỏ."""
import _venv; _venv.ensure()
import numpy as np
import networkx as nx
import config as C
import h0lib as L

G = nx.random_labeled_tree(500, seed=C.SMOKE_SEED)
A = L.graph_arrays(G)
p, med = L.calibrate_p(A, 1, 100, 1)
casc = L.gen_cascades(A, 1, p, 100, 2)
eds = [L.score_pos(ctx, np.array([L.kcenter(ctx.DIIsub, np.inf)[0]]))["ed"]
       for ctx in (L.CascadeCtx(A, s, i) for s, i in casc)]
eds = np.array(eds)
print(f"Cây n=500, k=1, p={p:.3f}, tỉ lệ cascade đạt 10-20%={med:.2f}")
print(f"Jordan center: ED trung bình={eds.mean():.3f}, trung vị={np.median(eds):.1f}, ED=0 ở {np.mean(eds==0)*100:.0f}% cascade")
print("KẾT QUẢ:", "ĐẠT (ED TB <= 1 hop)" if eds.mean() <= 1 else "CẦN XEM LẠI (ED TB > 1 hop)")

import json, os
os.makedirs("results/summary", exist_ok=True)
json.dump({"n_tree": 500, "k": 1, "p": float(p), "accept_rate": float(med), "ed_mean": float(eds.mean()),
           "ed_median": float(np.median(eds)), "pct_ed0": float(np.mean(eds == 0) * 100),
           "pass": bool(eds.mean() <= 1)}, open("results/summary/sanity_tree.json", "w"), indent=1)
print("Đã lưu results/summary/sanity_tree.json")
