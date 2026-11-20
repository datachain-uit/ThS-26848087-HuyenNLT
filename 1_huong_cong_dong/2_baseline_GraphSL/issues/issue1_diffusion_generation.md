**Title:** `diffusion_generation`: initial infected set is the 0/1 seed vector instead of node IDs, so every cascade starts from nodes 0 and 1

**Environment**
GraphSL 0.15 (PyPI), ndlib 6.0.1, networkx 3.7, Python 3.13 (CPU) and Google Colab (Python 3.13, Tesla T4). The line is unchanged on `main` (checked at commit `242751f`).

**Description**
In `GraphSL/utils.py`, `diffusion_generation` builds `seed_vector` with `generate_seed_vector`, which returns a 0/1 indicator list over `G.nodes()`. That list is then passed directly to ndlib:

```python
# GraphSL/utils.py, line 196
config.add_model_initial_configuration("Infected", seed_vector)
```

`ndlib.models.ModelConfig.Configuration.add_model_initial_configuration` expects a list of **node IDs**. Given a 0/1 vector, ndlib reads its values as node IDs, so the initial infected set is always `{0, 1}`, whatever seeds were sampled. The sampled `seed_vector` is still stored as the label, so the label and the simulated diffusion are unrelated.

This affects every diffusion type (IC, LT, SI, SIS, SIR), because the call is shared.

**Minimal reproduction** (no spreading, so the infected set equals the initial set)

```python
import networkx as nx, numpy as np, scipy.sparse as sp
from GraphSL.utils import diffusion_generation

G = nx.karate_club_graph()
graph = {"adj_mat": sp.csr_matrix(nx.to_scipy_sparse_array(G))}
out = diffusion_generation(graph, sim_num=3, diff_type="IC", time_step=1, repeat_step=1,
                           seed_ratio=0.2, threshold=0.0)
D = out["diff_mat"]
for i in range(3):
    print("seeds:", np.flatnonzero(D[i, :, 0].numpy()).tolist(),
          "| infected:", np.flatnonzero(D[i, :, 1].numpy()).tolist())
```

Output:

```
seeds: [0, 2, 3, 31, 32, 33] | infected: [0, 1]
seeds: [0, 1, 3, 31, 32, 33] | infected: [0, 1]
seeds: [0, 1, 2, 3, 31, 33] | infected: [0, 1]
```

**Effect on the benchmark datasets** (default IC settings, 5 simulations each)
With the current code, the infection vectors of different simulations are identical on Karate, Jazz and NetScience. On NetScience the mean infected fraction is 0.002 and the AUC of the infection vector against the true seeds is 0.498, i.e. at chance level. After the fix below, the vectors differ across simulations and the NetScience AUC is 0.958. Learned models can still score well on the original data because the seeds are drawn from the top-degree nodes, so a model that only learns "high degree = source" does well without using the diffusion at all.

**Suggested fix**

```python
init = [v for v, s in zip(G.nodes(), seed_vector) if s == 1]
config.add_model_initial_configuration("Infected", init)
```

Since the bug changes the generated data, results produced with `diffusion_generation` in 0.15 and earlier may need to be regenerated.
