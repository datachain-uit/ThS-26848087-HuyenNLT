"""Kiểm tra bản sửa kcenter_seq: (1) đồ thị liên thông -> trùng bản cũ; (2) đồ thị đứt mảnh -> tâm là Jordan center từng mảnh."""
import _venv; _venv.ensure()
import numpy as np, networkx as nx
from scipy.sparse.csgraph import shortest_path
import h0b as B

def old(M, m):
    M = np.where(np.isfinite(M), M, 1e6)
    c0 = int(np.argmin(M.max(axis=1))); centers = [c0]; dmin = M[c0].copy()
    while len(centers) < min(m, M.shape[0]):
        c = int(np.argmax(dmin)); centers.append(c); dmin = np.minimum(dmin, M[c])
    return centers

rng = np.random.default_rng(0); ok = 0
for t in range(200):
    G = nx.connected_watts_strogatz_graph(60, 4, 0.2, seed=t)
    M = shortest_path(nx.to_scipy_sparse_array(G), unweighted=True)
    for m in (1, 3, 5):
        assert B.kcenter_seq(M, m)[0] == old(M, m)
        ok += 1
print(f"(1) đồ thị liên thông: {ok}/{ok} trường hợp trùng bản cũ")
# (2) hai đường thẳng rời: 0-1-2-3-4 (5 node) và 5-6-7 (3 node). Jordan center: 2 và 6.
G = nx.disjoint_union(nx.path_graph(5), nx.path_graph(3))
M = shortest_path(nx.to_scipy_sparse_array(G), unweighted=True)
c1, c2 = B.kcenter_seq(M, 1)[0], B.kcenter_seq(M, 2)[0]
print("(2) đứt mảnh: m=1 ->", c1, "(kỳ vọng [2]); m=2 ->", c2, "(kỳ vọng [2, 6]); bản cũ m=2 ->", old(M, 2))
assert c1 == [2] and c2 == [2, 6]
print("ĐẠT")
