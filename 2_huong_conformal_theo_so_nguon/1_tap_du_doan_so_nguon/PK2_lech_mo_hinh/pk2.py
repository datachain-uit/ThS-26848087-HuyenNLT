"""P-K2 — tập dự đoán conformal cho k khi mô hình lan truyền bị lệch. Giao thức: PK2_PLAN.md.
Chạy: python pk2.py                 (mặc định hạn 07:30 sáng hôm sau gần nhất; ngừng nhận seed mới khi không kịp)
      python pk2.py --smoke         (kiểm tra nhanh, results_smoke/)
      python pk2.py --analyze-only  (chỉ dựng báo cáo từ chunk đã có)"""
import _venv; _venv.ensure()
import argparse
import csv
import datetime as dt
import glob
import hashlib
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED

import numpy as np
from scipy.sparse.csgraph import shortest_path, connected_components

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "..", "..", "..", "1_huong_cong_dong", "5_E0_ho_so_cong_dong_da_thang"))
import e0  # load_graph, si_fixed (β = 0,3), kcenter_seq, sub_seed
from sklearn.ensemble import RandomForestClassifier

SEED0 = 20261118
GRAPHS = e0.GRAPHS
FS = [0.02, 0.05, 0.10, 0.25]
KS = list(range(1, 11))
MODELS = {"SI": 60, "IC": 30, "SIR": 30}
P_IC, BETA_SIR, GAMMA_SIR = 0.2, 0.3, 0.3
RHOS, KMAX = e0.RHOS, 15
F_N = ["comp"] + [f"rho_{r}" for r in RHOS]
F_G = ["diam", "rad", "dq25", "dq50", "dq75", "dq90", "bnd", "degG_mean", "degG_max", "degI_mean", "leaf", "ecc_min"]
FEATS = F_N + F_G
TR, CAL, TE = range(0, 4), range(4, 7), range(7, 10)
N_SEEDS, ALPHA = 10, 0.1
MAX_TRIES = 5000


def ic_fixed(A, src, rng, target):
    ip, ix = A.indptr, A.indices
    act = np.zeros(A.shape[0], bool); act[src] = True
    front = np.asarray(src)
    while act.sum() < target:
        if front.size == 0:
            return None
        new = set()
        for u in front:
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[~act[nb]]
            if nb.size:
                new.update(nb[rng.random(nb.size) < P_IC].tolist())
        new = np.array(sorted(new), dtype=int)
        need = int(target - act.sum())
        if new.size > need:
            new = rng.choice(new, need, replace=False)
        act[new] = True
        front = new
    return np.flatnonzero(act)


def sir_fixed(A, src, rng, target):
    ip, ix = A.indptr, A.indices
    n = A.shape[0]
    ever = np.zeros(n, bool); ever[src] = True
    inf = np.zeros(n, bool); inf[src] = True
    while ever.sum() < target:
        I = np.flatnonzero(inf)
        if I.size == 0:
            return None
        new = set()
        for u in I:
            nb = ix[ip[u]:ip[u + 1]]; nb = nb[~ever[nb]]
            if nb.size:
                new.update(nb[rng.random(nb.size) < BETA_SIR].tolist())
        inf[I[rng.random(I.size) < GAMMA_SIR]] = False
        new = np.array(sorted(new), dtype=int)
        need = int(target - ever.sum())
        if new.size > need:
            new = rng.choice(new, need, replace=False)
        ever[new] = True; inf[new] = True
    return np.flatnonzero(ever)


def feats(A, inf):
    A_I = A[inf][:, inf].tocsr()
    ncomp, _ = connected_components(A_I, directed=False)
    DI = shortest_path(A_I, method="D", unweighted=True)
    _, radii = e0.kcenter_seq(DI, KMAX)
    f = {"comp": int(ncomp)}
    for r in RHOS:
        ok = [i + 1 for i, x in enumerate(radii) if x <= r]
        f[f"rho_{r}"] = ok[0] if ok else KMAX
    m = len(inf)
    ecc = np.where(np.isfinite(DI), DI, -1).max(axis=1)
    dv = DI[np.triu_indices(m, 1)]; dv = dv[np.isfinite(dv)]
    q = np.percentile(dv, [25, 50, 75, 90]) if dv.size else np.zeros(4)
    degG = np.asarray(A[inf].sum(axis=1)).ravel()
    degI = np.asarray(A_I.sum(axis=1)).ravel()
    ip, ix = A_I.indptr, A_I.indices
    emin = sum(1 for i in range(m) if ip[i] == ip[i + 1] or ecc[i] < ecc[ix[ip[i]:ip[i + 1]]].min())
    f.update(diam=float(ecc.max()), rad=float(ecc.min()), dq25=float(q[0]), dq50=float(q[1]), dq75=float(q[2]),
             dq90=float(q[3]), bnd=float(degG.sum() - degI.sum()), degG_mean=float(degG.mean()),
             degG_max=float(degG.max()), degI_mean=float(degI.mean()), leaf=float((degI == 1).mean()), ecc_min=emin)
    return f


SIM = {"SI": e0.si_fixed, "IC": ic_fixed, "SIR": sir_fixed}


def run_task(si, gid, frac, scale, out):
    ck = os.path.join(out, "chunks", f"s{si:03d}_{gid}_f{frac}.csv")
    if os.path.exists(ck):
        return si, gid, frac, 0.0, True
    t0 = time.time()
    G, A = e0.load_graph(gid)
    n = A.shape[0]
    target = int(round(frac * n))
    rows = []
    for model, n_c in MODELS.items():
        n_c = max(2, int(round(n_c * scale)))
        for k in KS:
            rng = np.random.default_rng(e0.sub_seed(SEED0, si, gid, frac, model, k))
            c = tries = 0
            while c < n_c and tries < MAX_TRIES:
                tries += 1
                src = rng.choice(n, k, replace=False)
                inf = SIM[model](A, src, rng, target)
                if inf is None:
                    continue
                rows.append(dict(seed=si, graph=gid, f=frac, model=model, k=k, casc=c, **feats(A, inf)))
                c += 1
    cols = ["seed", "graph", "f", "model", "k", "casc"] + FEATS
    os.makedirs(os.path.dirname(ck), exist_ok=True)
    with open(ck + ".tmp", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
    os.replace(ck + ".tmp", ck)
    return si, gid, frac, time.time() - t0, False


# ------------------------------------------------------------------ phân tích
def load_rows(out):
    rows = []
    for p in sorted(glob.glob(os.path.join(out, "chunks", "s*_f*.csv"))):
        with open(p, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                rows.append(dict(seed=int(r["seed"]), graph=r["graph"], f=float(r["f"]), model=r["model"], k=int(r["k"]),
                                 x=[float(r[c]) for c in FEATS]))
    return rows


def qhat(scores, alpha):
    n = len(scores)
    return float(np.quantile(scores, min(1.0, np.ceil((n + 1) * (1 - alpha)) / n), method="higher"))


def fit(R):
    return RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=0, n_jobs=-1).fit(
        np.array([r["x"] for r in R]), np.array([r["k"] for r in R]))


def proba(m, R):
    P = m.predict_proba(np.array([r["x"] for r in R]))
    full = np.zeros((len(R), len(KS)))
    for j, c in enumerate(m.classes_):
        full[:, KS.index(c)] = P[:, j]
    return full


def cp_q(m, R):
    P = proba(m, R)
    y = np.array([KS.index(r["k"]) for r in R])
    return qhat(1 - P[np.arange(len(R)), y], ALPHA)


def evaluate(S, R):
    y = np.array([KS.index(r["k"]) for r in R])
    hit = S[np.arange(len(R)), y]
    return float(hit.mean()), float(S.sum(1).mean())


def analyze(rows, tr_s, ca_s, te_s):
    out = {}
    for g in GRAPHS:
        for f in FS:
            C = [r for r in rows if r["graph"] == g and r["f"] == f]
            part = lambda S, models: [r for r in C if r["seed"] in S and r["model"] in models]
            tr_si, tr_mx = part(tr_s, {"SI"}), part(tr_s, set(MODELS))
            m_si, m_mx = fit(tr_si), fit(tr_mx)
            q_si, q_mx = cp_q(m_si, part(ca_s, {"SI"})), cp_q(m_mx, part(ca_s, set(MODELS)))
            # quy tắc k-center chọn trên train SI
            ytr = np.array([r["k"] for r in tr_si])
            best = min(RHOS, key=lambda rr: np.abs(np.clip([r["x"][F_N.index(f"rho_{rr}")] for r in tr_si], 1, 10) - ytr).mean())
            res = {}
            for model in MODELS:
                T = part(te_s, {model})
                y = np.array([r["k"] for r in T])
                P_si, P_mx = proba(m_si, T), proba(m_mx, T)
                S_si, S_mx = P_si >= 1 - q_si, P_mx >= 1 - q_mx
                top = P_si.argmax(1)
                pm1 = np.abs(np.arange(len(KS))[None, :] - top[:, None]) <= 1
                kc = np.clip([r["x"][F_N.index(f"rho_{best}")] for r in T], 1, 10)
                yi = np.array([KS.index(v) for v in y])
                res[model] = dict(cp_si=evaluate(S_si, T), cp_mx=evaluate(S_mx, T), pm1=evaluate(pm1, T),
                                  mae_pt=float(np.abs(np.array(KS)[top] - y).mean()), mae_kc=float(np.abs(kc - y).mean()),
                                  cov_k_si={k: float(S_si[y == k, KS.index(k)].mean()) for k in (1, 5, 10)},
                                  n=len(T))
            out[(g, f)] = dict(res=res, rho=best)
    return out


def report(out, n_seeds, path, smoke, secs, sha):
    V = sum(0.85 <= o["res"]["SI"]["cp_si"][0] <= 0.95 for o in out.values())
    U2 = sum(o["res"]["SI"]["cp_si"][1] <= 3.0 for (g, f), o in out.items() if f <= 0.05)
    R = sum(o["res"][m]["cp_si"][0] >= 0.80 for o in out.values() for m in ("IC", "SIR"))
    RM = sum(o["res"][m]["cp_mx"][0] >= 0.85 for o in out.values() for m in MODELS)
    okV, okU, okR, okRM = V >= 14, U2 >= 6, R >= 24, RM >= 42
    if not okV:
        verdict = "KIỂM TRA CÀI ĐẶT (V trượt) — không diễn giải"
    elif okU and (okR or okRM):
        verdict = "GO (" + ("nhờ R" if okR else "chỉ nhờ RM, hiệu chỉnh hỗn hợp") + ")"
    else:
        verdict = "NO-GO"
    L = [f"# P-K2 — báo cáo {'SMOKE (không dùng)' if smoke else ''} (sinh tự động)\n",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. Seed gốc {SEED0}; {n_seeds} seed. {platform.system()}, Python {platform.python_version()}. "
         f"Thời gian tính: {secs / 60:.1f} phút. SHA: {sha}. Giao thức: `PK2_PLAN.md`.\n",
         f"## Kết luận: **{verdict}**\n",
         f"- V (độ phủ CP-SI trên SI trong [0,85; 0,95]): {V}/16\n- U2 (kích thước CP-SI ≤ 3 ở f ≤ 5%): {U2}/8\n"
         f"- R (CP-SI phủ ≥ 0,80 trên IC và SIR): {R}/32\n- RM (CP-MIX phủ ≥ 0,85 trên SI, IC, SIR): {RM}/48\n",
         "## Độ phủ / kích thước tập (test, seed 7–9), α = 0,1, k ∈ 1..10\n",
         "| Đồ thị | f | mô hình | CP-SI | CP-MIX | pm1 | MAE pt | MAE k-center (ρ) | CP-SI phủ k=1 / 5 / 10 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for (g, f), o in out.items():
        for m, r in o["res"].items():
            ck = r["cov_k_si"]
            L.append(f"| {g} | {f:.0%} | {m} | {r['cp_si'][0]:.2f} / {r['cp_si'][1]:.2f} | {r['cp_mx'][0]:.2f} / {r['cp_mx'][1]:.2f} | "
                     f"{r['pm1'][0]:.2f} / {r['pm1'][1]:.2f} | {r['mae_pt']:.2f} | {r['mae_kc']:.2f} (ρ={o['rho']}) | "
                     f"{ck[1]:.2f} / {ck[5]:.2f} / {ck[10]:.2f} |")
    L.append("\n## Giới hạn\n\n- Một bản đồ thị mỗi mức μ; một bộ tham số mỗi mô hình; lệch mô hình nằm trong họ đã có trong hỗn hợp. Chưa có baseline BP và NetSleuth.\n")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    return verdict


def parse_deadline(s):
    h, m = map(int, s.split(":"))
    now = dt.datetime.now()
    d = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return d if d > now else d + dt.timedelta(days=1)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--analyze-only", action="store_true")
    ap.add_argument("--deadline", default="07:30")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    a = ap.parse_args()
    out = os.path.join(HERE, "results_smoke" if a.smoke else "results")
    os.makedirs(os.path.join(out, "chunks"), exist_ok=True); os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    scale = 0.1 if a.smoke else 1.0
    base = 900 if a.smoke else 0
    seeds = [base + s for s in range(N_SEEDS)]
    deadline = parse_deadline(a.deadline)
    logf = open(os.path.join(HERE, "logs", "pk2_smoke.log" if a.smoke else "pk2.log"), "a", encoding="utf-8")

    def log(msg):
        s = f"[{dt.datetime.now():%H:%M:%S}] {msg}"
        print(s, flush=True); logf.write(s + "\n"); logf.flush()

    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("PK2_PLAN.md", "pk2.py")}
    log(f"Bắt đầu P-K2 {'(smoke)' if a.smoke else ''}: {len(GRAPHS)} đồ thị x {len(FS)} f x 3 mô hình x k 1..10; "
        f"{N_SEEDS} seed; {a.workers} tiến trình; hạn {deadline:%d/%m %H:%M}. SHA {sha}")
    t_all = time.time(); secs = 0.0
    if not a.analyze_only:
        tasks = [(s, g, f) for s in seeds for g, f in sorted(((g, f) for g in GRAPHS for f in FS), key=lambda x: (-x[1], x[0] != "email_eu"))]
        pending, it, done_new, stop = {}, iter(tasks), 0, False
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            while True:
                while not stop and len(pending) < 2 * a.workers:
                    t = next(it, None)
                    if t is None:
                        stop = True; break
                    if done_new and dt.datetime.now() + dt.timedelta(seconds=(time.time() - t_all) / done_new * (len(pending) + 1)) > deadline:
                        log("Dừng nhận phần mới: dự báo không kịp hạn."); stop = True; break
                    pending[ex.submit(run_task, *t, scale, out)] = t
                if not pending:
                    break
                dn, _ = wait(list(pending), return_when=FIRST_COMPLETED)
                for fu in dn:
                    s, g, f = pending.pop(fu)
                    _, _, _, sec, skipped = fu.result()
                    if not skipped:
                        done_new += 1; secs += sec
                    if not any(v[0] == s for v in pending.values()) and not any(t[0] == s for t in []):
                        pass
                if done_new and done_new % 16 == 0:
                    log(f"{done_new} phần mới xong ({(time.time() - t_all) / 60:.1f} phút).")
    rows = load_rows(out)
    have = {}
    for r in rows:
        have.setdefault(r["seed"], set()).add((r["graph"], r["f"]))
    full = sorted(s for s, c in have.items() if len(c) == len(GRAPHS) * len(FS))
    if len(full) < N_SEEDS:
        log(f"Mới đủ {len(full)}/{N_SEEDS} seed; chạy lại cùng lệnh để chạy tiếp. Chưa phân tích.")
        return
    log("Phân tích ...")
    tr, ca, te = [set(base + s for s in rg) for rg in (TR, CAL, TE)]
    res = analyze(rows, tr, ca, te)
    v = report(res, len(full), os.path.join(out, "PK2_REPORT.md"), a.smoke, secs, sha)
    log(f"Kết thúc. Kết luận: {v}. Báo cáo: {os.path.join(out, 'PK2_REPORT.md')}")


if __name__ == "__main__":
    main()
