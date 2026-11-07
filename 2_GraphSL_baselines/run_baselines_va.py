"""Chạy lại 5 baseline GraphSL trên DỮ LIỆU ĐÃ VÁ (truyền danh sách mã node nguồn cho ndlib) — trên máy.
Cùng code với colab/GraphSL_va_loi_colab.ipynb. Kết quả: results/baselines_va.csv, log: logs/run_va.log.
Thứ tự: Karate (5 pp) -> Jazz (4 pp, trừ IVGD) -> NetScience (4 pp, trừ IVGD) -> GCNSI 3 chế độ trên 3 đồ thị -> IVGD Jazz.
IVGD NetScience KHÔNG chạy trên máy (ước tính 4–5 ngày CPU) — để Colab.
Chạy lại được: phần đã có "ok" trong CSV sẽ bỏ qua."""
import _venv; _venv.ensure()
import os, sys
for _st in (sys.stdout, sys.stderr):
    try: _st.reconfigure(encoding="utf-8")
    except Exception: pass
import warnings; warnings.filterwarnings("ignore")
# Ô 4: hàm sinh dữ liệu — bản sao GraphSL 0.15 utils.diffusion_generation, chỉ IC, có cờ fixed
import random, numpy as np, networkx as nx, torch
import ndlib.models.ModelConfig as mc, ndlib.models.epidemics as ep
from GraphSL.utils import generate_seed_vector

def diffusion_generation_v(graph, sim_num=100, time_step=10, repeat_step=10, seed_ratio=0.2,
                           threshold=0.5, random_seed=0, fixed=True):
    """fixed=False: y hệt GraphSL 0.15 (lỗi: ndlib nhận vector 0/1 -> nhiễm node 0 và 1).
       fixed=True : truyền danh sách mã node nguồn (bản vá, sửa đúng 1 chỗ)."""
    adj_mat = graph['adj_mat']
    G = nx.from_scipy_sparse_array(adj_mat)
    node_num = len(G.nodes()); seed_num = int(seed_ratio * node_num)
    degree_list = sorted(G.degree(), key=lambda x: x[1], reverse=True)
    num_more_node = int(len(degree_list) * 0.05)
    top_nodes = [x[0] for x in degree_list[:num_more_node + seed_num]]
    simulation = []
    for i in range(sim_num):
        seed_vector = generate_seed_vector(top_nodes, seed_num, G, random_seed + i)
        init = [v for v, s in zip(G.nodes(), seed_vector) if s == 1] if fixed else seed_vector   # <-- chỗ sửa duy nhất
        inf_vec_all = torch.zeros(node_num)
        config = mc.Configuration()
        for k in range(repeat_step):
            model = ep.IndependentCascadesModel(G, random_seed + k)
            for e in G.edges():
                config.add_edge_configuration("threshold", e, threshold)
            config.add_model_initial_configuration("Infected", init)
            model.set_initial_status(config)
            iterations = model.iteration_bunch(time_step)
            node_status = iterations[0]['status']
            for j in range(1, len(iterations)):
                node_status.update(iterations[j]['status'])
            inf_vec = np.array(list(node_status.values())); inf_vec[inf_vec == 2] = 1
            inf_vec_all += inf_vec
        inf_vec_all = inf_vec_all / repeat_step
        simulation.append([seed_vector, inf_vec_all])
    simulation = torch.Tensor(np.array([[np.asarray(s, dtype=float), v.numpy()] for s, v in simulation])).permute(0, 2, 1)
    return {'adj_mat': adj_mat, 'diff_mat': simulation}
import datetime as dt
from sklearn.metrics import roc_auc_score
from GraphSL.utils import load_dataset, split_dataset, download_dataset
WORK = os.getcwd()
OUT = os.path.join(WORK, "results"); os.makedirs(OUT, exist_ok=True); os.makedirs("logs", exist_ok=True)
if not os.path.exists("data"): download_dataset(WORK)
LOG = os.path.join("logs", "run_va.log")
def log(m):
    line = f"[{dt.datetime.now():%H:%M:%S}] {m}"; print(line, flush=True); open(LOG, "a", encoding="utf-8").write(line + "\n")
# Ô 6: hàm chạy 5 baseline + GCNSI các chế độ chọn tập nguồn (top-k với k thật; ngưỡng chọn trên val)
import csv, time, traceback
from GraphSL.Prescribed import LPSI, NetSleuth
from GraphSL.GNN.GCNSI.main import GCNSI
from GraphSL.GNN.IVGD.main import IVGD
from GraphSL.GNN.SLVAE.main import SLVAE
from scipy.sparse import csgraph, coo_matrix
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
CSV = os.path.join(OUT, 'baselines_va.csv')
FIELDS = ['time','data','dataset','n_nodes','method','seed','acc','pr','re','f1','auc','train_s','test_s','status']
DEV = torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'

def done(data, ds, mth):
    if not os.path.exists(CSV): return False
    return any(r['data']==data and r['dataset']==ds and r['method']==mth and r['status'].startswith('ok') for r in csv.DictReader(open(CSV, encoding='utf-8')))

def write(row):
    new = not os.path.exists(CSV)
    with open(CSV, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore'); new and w.writeheader(); w.writerow(row)

def set_seed(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)

def run_method(name, adj, train, test):
    t0 = time.time()
    if name == 'LPSI':
        m = LPSI(); alpha, thres, *_ = m.train(adj, train); t1 = time.time(); r = m.test(adj, test, alpha, thres)
    elif name == 'NetSleuth':
        m = NetSleuth(); k, *_ = m.train(adj, train); t1 = time.time(); r = m.test(adj, test, k)
    elif name == 'GCNSI':
        m = GCNSI(); model, thres, *_ = m.train(adj, train); t1 = time.time(); r = m.test(adj, test, model, thres)
    elif name == 'IVGD':
        m = IVGD(); diff = m.train_diffusion(adj, train); model, thres, *_ = m.train(adj, train, diff)
        t1 = time.time(); r = m.test(adj, test, diff, model, thres)
    elif name == 'SLVAE':
        m = SLVAE(); model, seed_train, thres, *_ = m.train(adj, train); t1 = time.time(); r = m.infer(test, model, seed_train, thres)
    return [r.acc, r.pr, r.re, r.f1, r.auc], t1 - t0, time.time() - t1

# --- GCNSI: đánh giá lại với đầu vào đúng từng cascade (GraphSL.test dùng nhầm lpsi_input[i] cố định) ---
def gcnsi_feats(adj, dataset, alpha=0.01):
    S = torch.tensor(coo_matrix.todense(csgraph.laplacian(adj, normed=True)), dtype=torch.float)
    n = adj.shape[0]; M = (1 - alpha) * torch.linalg.inv(torch.eye(n) - alpha * S)
    out = []
    for im in dataset:
        d = im[:, -1].float(); V3 = d.clone(); V4 = d.clone(); V3[d < 0.5] = 0.5; V4[d >= 0.5] = 0.5
        out.append(torch.cat([d.unsqueeze(1)] + [(M @ v).unsqueeze(1) for v in (d, V3, V4)], dim=1))
    return out

def gcnsi_scores(model, adj, dataset):
    coo = adj.tocoo(); ei = torch.stack([torch.from_numpy(coo.row.astype(np.int64)), torch.from_numpy(coo.col.astype(np.int64))])
    model = model.cpu().eval()
    with torch.no_grad():
        return [torch.softmax(model(x, ei), dim=1)[:, 1].numpy() for x in gcnsi_feats(adj, dataset)]

def evaluate(dataset, preds, rule):
    m = np.zeros(5)
    for im, p in zip(dataset, preds):
        y = im[:, 0].numpy().astype(int); yh = rule(p, y)
        m += [accuracy_score(y, yh), precision_score(y, yh, zero_division=1), recall_score(y, yh, zero_division=1), f1_score(y, yh, zero_division=1), roc_auc_score(y, p)]
    return list(m / len(preds))

def topk(p, y):
    yh = np.zeros_like(y); yh[np.argsort(-p)[:int(y.sum())]] = 1; return yh

def best_thres(dataset, preds, num=10):
    a = np.concatenate(preds); best = (-1, None)
    for t in np.linspace(a.min(), a.max(), num + 2)[1:-1]:
        f = np.mean([f1_score(im[:, 0].numpy().astype(int), p >= t) for im, p in zip(dataset, preds)])
        if f > best[0]: best = (f, float(t))
    return best[1]

def gcnsi_modes(adj, train, test):
    set_seed(0); g = GCNSI(); model, thres, *_ = g.train(adj, train)
    P = gcnsi_scores(model, adj, test)
    res = {'GCNSI_sua_nguong_train': evaluate(test, P, lambda p, y: (p >= thres).astype(int)),
           'GCNSI_topk_k_that': evaluate(test, P, topk)}
    idx = np.random.default_rng(0).permutation(len(train)); cut = int(0.75 * len(train))
    tr = torch.utils.data.Subset(train, idx[:cut].tolist()); va = torch.utils.data.Subset(train, idx[cut:].tolist())
    set_seed(0); mv, *_ = GCNSI().train(adj, tr); tv = best_thres(va, gcnsi_scores(mv, adj, va))
    res['GCNSI_nguong_val'] = evaluate(test, gcnsi_scores(mv, adj, test), lambda p, y: (p >= tv).astype(int))
    return res

def run_all(data, datasets, methods, modes=True):
    for ds in datasets:
        set_seed(0)
        adj, train, test = split_dataset(diffusion_generation_v(load_dataset(ds, data_dir=WORK), fixed=(data == 'va')))
        log(f"== [{data}] {ds} (n={adj.shape[0]}): {len(train)} train / {len(test)} test")
        for mth in methods:
            if done(data, ds, mth): log(f"   {mth}: đã có, bỏ qua"); continue
            set_seed(0); row = dict(time=dt.datetime.now().isoformat(timespec='seconds'), data=data, dataset=ds,
                                    n_nodes=adj.shape[0], method=mth, seed=0)
            try:
                log(f"   {mth}: đang huấn luyện..."); m, tr_s, te_s = run_method(mth, adj, train, test)
                row.update(dict(zip(['acc','pr','re','f1','auc'], m)), train_s=round(tr_s,1), test_s=round(te_s,1), status=f'ok ({DEV})')
                log(f"   {mth}: acc={m[0]:.3f} pr={m[1]:.3f} re={m[2]:.3f} f1={m[3]:.3f} auc={m[4]:.3f} | train {tr_s:.0f}s, test {te_s:.0f}s")
            except Exception as e:
                row.update(status=f'error: {type(e).__name__}: {e}'); log(f"   {mth}: LỖI {type(e).__name__}: {e}")
                open(LOG, 'a', encoding='utf-8').write(traceback.format_exc() + "\n")
            write(row)
        if modes and not done(data, ds, 'GCNSI_topk_k_that'):
            try:
                t0 = time.time(); log("   GCNSI các chế độ: đang chạy...")
                for mode, m in gcnsi_modes(adj, train, test).items():
                    write(dict(time=dt.datetime.now().isoformat(timespec='seconds'), data=data, dataset=ds, n_nodes=adj.shape[0],
                               method=mode, seed=0, acc=m[0], pr=m[1], re=m[2], f1=m[3], auc=m[4], status=f'ok ({DEV})'))
                    log(f"   {mode}: acc={m[0]:.3f} pr={m[1]:.3f} re={m[2]:.3f} f1={m[3]:.3f} auc={m[4]:.3f}")
                log(f"   GCNSI các chế độ: xong {time.time()-t0:.0f}s")
            except Exception as e:
                log(f"   GCNSI các chế độ: LỖI {type(e).__name__}: {e}"); open(LOG, 'a', encoding='utf-8').write(traceback.format_exc() + "\n")

def sanity():
    for ds in ["karate", "jazz", "netscience"]:
        g = load_dataset(ds, data_dir=WORK)
        for fixed in (False, True):
            D = diffusion_generation_v(g, sim_num=5, fixed=fixed)["diff_mat"]
            s, d = D[:, :, 0].numpy(), D[:, :, 1].numpy()
            same = all(np.allclose(d[0], d[i]) for i in range(1, 5))
            log(f"KIỂM TRA {ds:10s} {'vá ' if fixed else 'gốc'}: tỉ lệ nhiễm TB={d.mean():.3f} | vector nhiễm giống hệt giữa cascade: {same}")

if __name__ == "__main__":
    log("run_baselines_va.py bắt đầu (dữ liệu đã vá)")
    sanity()
    run_all("va", ["karate"], ["LPSI", "NetSleuth", "GCNSI", "IVGD", "SLVAE"], modes=True)
    run_all("va", ["jazz", "netscience"], ["LPSI", "NetSleuth", "GCNSI", "SLVAE"], modes=True)
    run_all("va", ["jazz"], ["IVGD"], modes=False)
    log("XONG. Kết quả: results/baselines_va.csv (IVGD-NetScience chạy trên Colab)")
