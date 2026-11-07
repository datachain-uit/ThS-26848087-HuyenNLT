"""Chạy 5 baseline của GraphSL trên Karate, Jazz, NetScience (Review 30/10 Mục 7.4, hạn 10/11).

Giao thức đánh giá giữ đúng mặc định của GraphSL (README, v0.15):
  diffusion_generation(infect_prob=0.3, diff_type='IC', sim_num=100, seed_ratio=0.2) -> split_dataset
  Metric: acc, pr, re, f1, auc (phân loại node nguồn / không nguồn) do GraphSL trả về.
Mục đích: kiểm môi trường và so cùng cỡ với bài GraphSL (arXiv 2405.03724), KHÔNG phải thí nghiệm của P6.

  python run_baselines.py                       # mặc định: 3 đồ thị x 5 phương pháp x seed 0
  python run_baselines.py --seeds 0 1 2         # nhiều seed
  python run_baselines.py --methods GCNSI       # chỉ một phương pháp
"""
import _venv; _venv.ensure()
import argparse
import csv
import datetime as dt
import os
import platform
import random
import sys
import time
import traceback

import numpy as np

DATASETS = ["karate", "jazz", "netscience"]
METHODS = ["LPSI", "NetSleuth", "GCNSI", "IVGD", "SLVAE"]
DIFF = dict(infect_prob=0.3, diff_type="IC", sim_num=100, seed_ratio=0.2)   # mặc định README GraphSL
FIELDS = ["time", "dataset", "n_nodes", "method", "seed", "acc", "pr", "re", "f1", "auc",
          "train_s", "test_s", "status"]

os.makedirs("logs", exist_ok=True)
os.makedirs("results", exist_ok=True)
LOG = os.path.join("logs", "run.log")


def log(msg):
    line = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def set_seed(s):
    random.seed(s)
    np.random.seed(s)
    try:
        import torch
        torch.manual_seed(s)
    except ImportError:
        pass


def run_method(name, adj, train, test):
    from GraphSL.Prescribed import LPSI, NetSleuth
    from GraphSL.GNN.GCNSI.main import GCNSI
    from GraphSL.GNN.IVGD.main import IVGD
    from GraphSL.GNN.SLVAE.main import SLVAE
    t0 = time.time()
    if name == "LPSI":
        m = LPSI(); alpha, thres, *_ = m.train(adj, train); t1 = time.time()
        res = m.test(adj, test, alpha, thres)
    elif name == "NetSleuth":
        m = NetSleuth(); k, *_ = m.train(adj, train); t1 = time.time()
        res = m.test(adj, test, k)
    elif name == "GCNSI":
        m = GCNSI(); model, thres, *_ = m.train(adj, train); t1 = time.time()
        res = m.test(adj, test, model, thres)
    elif name == "IVGD":
        m = IVGD(); diff = m.train_diffusion(adj, train)
        model, thres, *_ = m.train(adj, train, diff); t1 = time.time()
        res = m.test(adj, test, diff, model, thres)
    elif name == "SLVAE":
        m = SLVAE(); model, seed_train, thres, *_ = m.train(adj, train); t1 = time.time()
        res = m.infer(test, model, seed_train, thres)
    else:
        raise ValueError(name)
    t2 = time.time()
    return res, t1 - t0, t2 - t1


def main():
    log("run_baselines.py bắt đầu")
    ap = argparse.ArgumentParser()
    ap.add_argument("--datasets", nargs="+", default=DATASETS)
    ap.add_argument("--methods", nargs="+", default=METHODS)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0])
    a = ap.parse_args()
    try:
        from GraphSL.utils import load_dataset, diffusion_generation, split_dataset, download_dataset
        import GraphSL
    except Exception as e:
        log(f"LỖI khi import GraphSL: {type(e).__name__}: {e}")
        with open(LOG, "a", encoding="utf-8") as lf:
            lf.write(traceback.format_exc() + "\n")
        raise
    log(f"Bắt đầu | python {sys.version.split()[0]} | {platform.platform()} | GraphSL {getattr(GraphSL, '__version__', '?')}")
    log(f"Giao thức sinh dữ liệu (mặc định GraphSL): {DIFF}")
    data_dir = os.getcwd()
    if not os.path.exists(os.path.join(data_dir, "data")):
        log("Tải bộ dữ liệu của GraphSL...")
        download_dataset(data_dir)
    out = os.path.join("results", "baselines.csv")
    new = not os.path.exists(out)
    with open(out, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for ds in a.datasets:
            for s in a.seeds:
                set_seed(s)
                graph = load_dataset(ds, data_dir=data_dir)
                dataset = diffusion_generation(graph=graph, **DIFF)
                adj, train, test = split_dataset(dataset)
                n = adj.shape[0]
                log(f"== {ds} (n={n}) seed={s}: {len(train)} train / {len(test)} test cascade")
                for mth in a.methods:
                    set_seed(s)
                    row = dict(time=dt.datetime.now().isoformat(timespec="seconds"), dataset=ds,
                               n_nodes=n, method=mth, seed=s)
                    try:
                        log(f"   {mth}: đang huấn luyện...")
                        res, tr, te = run_method(mth, adj, train, test)
                        row.update(acc=res.acc, pr=res.pr, re=res.re, f1=res.f1, auc=res.auc,
                                   train_s=round(tr, 1), test_s=round(te, 1), status="ok")
                        log(f"   {mth}: acc={res.acc:.3f} pr={res.pr:.3f} re={res.re:.3f} "
                            f"f1={res.f1:.3f} auc={res.auc:.3f} | train {tr:.0f}s, test {te:.0f}s")
                    except Exception as e:
                        row.update(status=f"error: {type(e).__name__}: {e}")
                        log(f"   {mth}: LỖI {type(e).__name__}: {e}")
                        with open(LOG, "a", encoding="utf-8") as lf:
                            lf.write(traceback.format_exc() + "\n")
                    w.writerow(row); f.flush()
    log(f"XONG. Kết quả: {out}")


if __name__ == "__main__":
    main()
