"""GCNSI với các chế độ chọn tập nguồn (Review 30/10 Mục 7.4: top-k với k thật; ngưỡng chọn trên val - O3).

Dữ liệu sinh y hệt run_baselines.py (mặc định GraphSL 0.15), mô hình GCNSI của GraphSL giữ nguyên.
Chỉ thay phần ĐÁNH GIÁ:
  graphsl_goc     : gọi GCNSI.test của GraphSL như cũ (có lỗi chỉ số, xem dưới) - để đối chiếu
  sua_nguong_train: sửa lỗi chỉ số; ngưỡng chọn trên train (đúng quy tắc của GraphSL)
  topk_k_that     : sửa lỗi chỉ số; lấy k node điểm cao nhất, k = số nguồn thật của cascade
  nguong_val      : huấn luyện trên 75% train, chọn ngưỡng theo F1 trên 25% còn lại (val), đo trên test

Lỗi chỉ số trong GraphSL 0.15 (GNN/GCNSI/main.py, hàm test): vòng lặp đánh giá dùng `lpsi_input[i]`
với `i` còn sót từ vòng lặp trước (= chỉ số cascade test cuối), nên mọi cascade test được dự đoán từ
CÙNG một đầu vào.

  python gcnsi_modes.py                       # Karate, Jazz, NetScience
  python gcnsi_modes.py --datasets karate
"""
import _venv; _venv.ensure()
import argparse
import csv
import datetime as dt
import os
import time

import numpy as np
import torch
from scipy.sparse import csgraph, coo_matrix
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score

DIFF = dict(infect_prob=0.3, diff_type="IC", sim_num=100, seed_ratio=0.2)   # như run_baselines.py
FIELDS = ["time", "dataset", "n_nodes", "mode", "n_train", "thres", "acc", "pr", "re", "f1", "auc", "seconds"]
os.makedirs("logs", exist_ok=True); os.makedirs("results", exist_ok=True)
LOG = os.path.join("logs", "gcnsi_modes.log")


def log(msg):
    line = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def features(adj, dataset, alpha=0.01):
    """Đầu vào GCNSI cho TỪNG cascade (chép đúng cách GraphSL tạo đặc trưng LPSI 4 kênh)."""
    # Giống hệt LPSI.predict của GraphSL: x = (1 - alpha) * inv(I - alpha*S) @ v.
    # Ma trận nghịch đảo không phụ thuộc cascade nên tính MỘT lần (GraphSL tính lại mỗi lần gọi).
    S = csgraph.laplacian(adj, normed=True)
    S = torch.tensor(coo_matrix.todense(S), dtype=torch.float)
    n = adj.shape[0]; out = []
    M = (1 - alpha) * torch.linalg.inv(torch.eye(n) - alpha * S)
    for influ_mat in dataset:
        d = influ_mat[:, -1].float()
        V3 = d.clone(); V4 = d.clone(); V3[d < 0.5] = 0.5; V4[d >= 0.5] = 0.5
        cols = [d.unsqueeze(1)] + [(M @ v).unsqueeze(1) for v in (d, V3, V4)]
        out.append(torch.cat(cols, dim=1))
    return out


def scores(model, adj, dataset):
    coo = adj.tocoo()
    ei = torch.stack([torch.from_numpy(coo.row.astype(np.int64)), torch.from_numpy(coo.col.astype(np.int64))])
    model = model.cpu().eval()
    with torch.no_grad():
        return [torch.softmax(model(x, ei), dim=1)[:, 1].numpy() for x in features(adj, dataset)]


def metric(dataset, preds, rule):
    m = np.zeros(5)
    for influ_mat, p in zip(dataset, preds):
        y = influ_mat[:, 0].numpy().astype(int)
        yhat = rule(p, y)
        m += [accuracy_score(y, yhat), precision_score(y, yhat, zero_division=1), recall_score(y, yhat, zero_division=1),
              f1_score(y, yhat, zero_division=1), roc_auc_score(y, p)]
    return m / len(preds)


def topk(p, y):
    k = int(y.sum()); yhat = np.zeros_like(y); yhat[np.argsort(-p)[:k]] = 1
    return yhat


def best_thres(dataset, preds, num_thres=10):
    allp = np.concatenate(preds)
    best = (-1, None)
    for t in np.linspace(allp.min(), allp.max(), num_thres + 2)[1:-1]:
        f = np.mean([f1_score(im[:, 0].numpy().astype(int), p >= t) for im, p in zip(dataset, preds)])
        if f > best[0]:
            best = (f, float(t))
    return best[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=["karate", "jazz", "netscience"])
    a = ap.parse_args()
    from GraphSL.utils import load_dataset, diffusion_generation, split_dataset
    from GraphSL.GNN.GCNSI.main import GCNSI
    out = os.path.join("results", "gcnsi_modes.csv"); new = not os.path.exists(out)
    log("gcnsi_modes.py bắt đầu")
    with open(out, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for ds in a.datasets:
            torch.manual_seed(0); np.random.seed(0)
            graph = load_dataset(ds, data_dir=os.getcwd())
            adj, train, test = split_dataset(diffusion_generation(graph=graph, **DIFF))
            n = adj.shape[0]
            log(f"== {ds} (n={n}): {len(train)} train / {len(test)} test")

            def emit(mode, ntr, thres, m, t0):
                row = dict(time=dt.datetime.now().isoformat(timespec="seconds"), dataset=ds, n_nodes=n, mode=mode,
                           n_train=ntr, thres=thres, acc=m[0], pr=m[1], re=m[2], f1=m[3], auc=m[4],
                           seconds=round(time.time() - t0, 1))
                w.writerow(row); f.flush()
                log(f"   {mode:17s} acc={m[0]:.3f} pr={m[1]:.3f} re={m[2]:.3f} f1={m[3]:.3f} auc={m[4]:.3f}")

            t0 = time.time()
            g = GCNSI(); model, thres, *_ = g.train(adj, train)
            r = g.test(adj, test, model, thres)
            emit("graphsl_goc", len(train), thres, [r.acc, r.pr, r.re, r.f1, r.auc], t0)
            t1 = time.time(); P = scores(model, adj, test)
            emit("sua_nguong_train", len(train), thres, metric(test, P, lambda p, y: (p >= thres).astype(int)), t1)
            emit("topk_k_that", len(train), "", metric(test, P, topk), t1)
            # ngưỡng chọn trên val: 75% train để huấn luyện, 25% còn lại làm val
            t2 = time.time()
            idx = np.random.default_rng(0).permutation(len(train)); cut = int(0.75 * len(train))
            tr = torch.utils.data.Subset(train, idx[:cut].tolist()); va = torch.utils.data.Subset(train, idx[cut:].tolist())
            torch.manual_seed(0)
            model_v, *_ = GCNSI().train(adj, tr)
            tv = best_thres(va, scores(model_v, adj, va))
            emit("nguong_val", len(tr), tv, metric(test, scores(model_v, adj, test), lambda p, y: (p >= tv).astype(int)), t2)
    log(f"XONG. Kết quả: {out}")


if __name__ == "__main__":
    main()
