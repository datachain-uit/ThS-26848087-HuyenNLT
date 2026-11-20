**Title:** `GCNSI.test` uses `lpsi_input[i]` with a stale `i`, so every test cascade is scored with the features of the last one

**Environment**
GraphSL 0.15 (PyPI), Python 3.13, CPU. The code is unchanged on `main` (checked at commit `242751f`).

**Description**
In `GraphSL/GNN/GCNSI/main.py`, `GCNSI.test` first fills `lpsi_input[i]` for every test cascade (`for i, influ_mat in enumerate(test_dataset)`, line 196). The evaluation loop then iterates without an index:

```python
# GraphSL/GNN/GCNSI/main.py, lines 221-224
for influ_mat in test_dataset:
    seed_vec = influ_mat[:, 0].numpy()
    diff_vec = influ_mat[:, -1].to(self.device)
    pred = gcnsi_model(lpsi_input[i], edge_index)
```

`i` is left over from the earlier loop and equals `len(test_dataset) - 1`, so the model receives the same features for every cascade, while `seed_vec` changes. The reported metrics therefore compare one fixed prediction against every cascade's seeds. The training loops (lines 109, 125, 136) use `enumerate` and are not affected.

**Minimal reproduction** (hand-built cascades, so it does not depend on `diffusion_generation`)

```python
import numpy as np, torch, networkx as nx, scipy.sparse as sp
from GraphSL.GNN.GCNSI.main import GCNSI
from GraphSL.utils import split_dataset

G = nx.karate_club_graph(); n = G.number_of_nodes()
rng = np.random.default_rng(0)
sims = []
for _ in range(20):
    seed = np.zeros(n); seed[rng.choice(n, 3, replace=False)] = 1
    inf = np.maximum(seed, (rng.random(n) < 0.4).astype(float))
    sims.append(np.stack([seed, inf], axis=1))
data = {"adj_mat": sp.csr_matrix(nx.to_scipy_sparse_array(G)),
        "diff_mat": torch.tensor(np.array(sims), dtype=torch.float)}
adj, train, test = split_dataset(data)

m = GCNSI(); model, thres, *_ = m.train(adj, train, num_epoch=5)
seen = []
fwd = model.forward
model.forward = lambda x, ei: (seen.append(x.detach().cpu().clone()), fwd(x, ei))[1]
m.test(adj, test, model, thres)

print("test cascades:", len(test), "| distinct infection vectors:",
      len({t[:, -1].numpy().tobytes() for t in test}))
print("distinct feature tensors passed to the model:", len({t.numpy().tobytes() for t in seen}))
```

Output:

```
test cascades: 8 | distinct infection vectors: 8
distinct feature tensors passed to the model: 1
```

**Suggested fix**

```python
for i, influ_mat in enumerate(test_dataset):
    seed_vec = influ_mat[:, 0].numpy()
    pred = gcnsi_model(lpsi_input[i], edge_index)
```
