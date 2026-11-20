# Bug 2: GCNSI.test passes the same features (lpsi_input[i], i left over from the feature loop)
# to the model for every test cascade. Independent of bug 1: cascades are built by hand and all differ.
import numpy as np, torch, networkx as nx, scipy.sparse as sp
from GraphSL.GNN.GCNSI.main import GCNSI
from GraphSL.utils import split_dataset

G = nx.karate_club_graph(); n = G.number_of_nodes()
rng = np.random.default_rng(0)
sims = []
for _ in range(20):                         # 20 distinct cascades: 3 random seeds, random infected set containing them
    seed = np.zeros(n); seed[rng.choice(n, 3, replace=False)] = 1
    inf = np.maximum(seed, (rng.random(n) < 0.4).astype(float))
    sims.append(np.stack([seed, inf], axis=1))
data = {"adj_mat": sp.csr_matrix(nx.to_scipy_sparse_array(G)), "diff_mat": torch.tensor(np.array(sims), dtype=torch.float)}
adj, train, test = split_dataset(data)

m = GCNSI(); model, thres, *_ = m.train(adj, train, num_epoch=5)
seen = []
orig_forward = model.forward
model.forward = lambda x, edge_index: (seen.append(x.detach().cpu().clone()), orig_forward(x, edge_index))[1]
m.test(adj, test, model, thres)

print("test cascades:", len(test), "| distinct infection vectors in test set:",
      len({t[:, -1].numpy().tobytes() for t in test}))
print("distinct feature tensors passed to the model in GCNSI.test:", len({t.numpy().tobytes() for t in seen}))
