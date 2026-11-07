"""Mốc so sánh "đoán theo bậc": điểm mỗi node = bậc / bậc lớn nhất (giống nhau ở mọi cascade, KHÔNG dùng lan truyền).
Chạy trên cùng dữ liệu với run_baselines_va.py (gốc GraphSL lỗi và bản vá), cùng cách chia train/test.
Hai cách chọn tập nguồn: top-k với k thật; ngưỡng chọn trên train theo F1 (như GraphSL).
Kết quả: results/degree_baseline.csv, log: logs/degree_baseline.log."""
import _venv; _venv.ensure()
import csv, os, datetime as dt
import numpy as np
import run_baselines_va as R   # dùng chung hàm sinh dữ liệu và chấm điểm

LOG = os.path.join("logs", "degree_baseline.log")
def log(m):
    line = f"[{dt.datetime.now():%H:%M:%S}] {m}"; print(line, flush=True); open(LOG, "a", encoding="utf-8").write(line + "\n")

out = os.path.join("results", "degree_baseline.csv"); rows = []
log("degree_baseline.py bắt đầu")
for data in ["goc", "va"]:
    for ds in ["karate", "jazz", "netscience"]:
        R.set_seed(0)
        adj, train, test = R.split_dataset(R.diffusion_generation_v(R.load_dataset(ds, data_dir=R.WORK), fixed=(data == "va")))
        deg = np.asarray(adj.sum(1)).ravel().astype(float); score = deg / deg.max()
        Ptr = [score] * len(train); Pte = [score] * len(test)
        thr = R.best_thres(train, Ptr)
        for mode, rule in [("topk_k_that", R.topk), ("nguong_train", lambda p, y: (p >= thr).astype(int))]:
            m = R.evaluate(test, Pte, rule)
            rows.append(dict(data=data, dataset=ds, n_nodes=adj.shape[0], method="Degree", mode=mode,
                             acc=m[0], pr=m[1], re=m[2], f1=m[3], auc=m[4]))
            log(f"[{data}] {ds:10s} Degree {mode:12s} acc={m[0]:.3f} pr={m[1]:.3f} re={m[2]:.3f} f1={m[3]:.3f} auc={m[4]:.3f}")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
log(f"XONG. Kết quả: {out}")
