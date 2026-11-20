# Bug 1: diffusion_generation passes a 0/1 seed vector where ndlib expects a list of node IDs
import networkx as nx, numpy as np, scipy.sparse as sp
from GraphSL.utils import diffusion_generation

G = nx.karate_club_graph()                  # 34 nodes
graph = {"adj_mat": sp.csr_matrix(nx.to_scipy_sparse_array(G))}
out = diffusion_generation(graph, sim_num=3, diff_type="IC", time_step=1, repeat_step=1,
                           seed_ratio=0.2, threshold=0.0)   # threshold=0 -> no spread, infected set == initial set
D = out["diff_mat"]                          # shape: (sim_num, n, 2) -> [:, :, 0] seeds, [:, :, 1] infected
for i in range(3):
    seeds = np.flatnonzero(D[i, :, 0].numpy())
    infected = np.flatnonzero(D[i, :, 1].numpy())
    print(f"simulation {i}: sampled seeds = {seeds.tolist()}, infected nodes = {infected.tolist()}")
