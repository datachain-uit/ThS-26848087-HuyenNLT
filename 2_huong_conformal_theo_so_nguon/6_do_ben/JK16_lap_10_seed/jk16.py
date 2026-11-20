"""J-K16 — 10 seed cho J-K12 (A: dữ liệu tác giả; B: C3 mô phỏng). Giao thức: JK16_PLAN.md. Chạy: python jk16.py [--smoke]"""
import _venv; _venv.ensure()
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for p in ("2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK12_gia_theo_K", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK11_do_thi_lon", "2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK7_KNCP", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k"):
    sys.path.append(os.path.join(HERE, "..", p))
import datetime as dt, hashlib, pickle, platform, time
import numpy as np
from scipy.stats import spearmanr
import jk12, jk11
from jk5 import CONFIGS
os.chdir(HERE)
SMOKE = "--smoke" in sys.argv
SEEDS = [0] if SMOKE else list(range(10))
OUT = os.path.join(HERE, "results", "JK16_smoke.pkl" if SMOKE else "JK16_raw.pkl")
METH = ("G", "O", "WCP", "MD", "KSU*")


def perm_p(x, y, rng, B=10000):
    r0 = spearmanr(x, y)[0]; c = 1
    for _ in range(B):
        c += spearmanr(x, rng.permutation(y))[0] >= r0
    return r0, c / (B + 1)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    R = pickle.load(open(OUT, "rb")) if os.path.exists(OUT) else {}
    t0 = time.time(); cache = {}
    if SMOKE:
        R[("A", 0)] = {CONFIGS[-1]: jk12.part_b(*CONFIGS[-1], reps=2, seed=20261118)}
        R[("B", 0)] = {jk12.SET_A[0]: jk11.run(100, *jk12.SET_A[0], cache)}
        pickle.dump(R, open(OUT, "wb")); print("smoke ok", flush=True); return
    for s in SEEDS:
        key = ("A", s)
        if key not in R:
            R[key] = {}
        for c in CONFIGS:
            if c in R[key]:
                continue
            print(f"[{dt.datetime.now():%H:%M}] A seed {s} {c}", flush=True)
            R[key][c] = jk12.part_b(*c, reps=50, seed=20261118 + 1000 * s)
            pickle.dump(R, open(OUT, "wb"))
    for s in SEEDS:
        key = ("B", s)
        if key not in R:
            R[key] = {}
        for i, st in enumerate(jk12.SET_A):
            if st in R[key]:
                continue
            print(f"[{dt.datetime.now():%H:%M}] B seed {s} {st}", flush=True)
            R[key][st] = jk11.run(100 + i + 1000 * s, *st, cache)
            pickle.dump(R, open(OUT, "wb"))
    report(R, time.time() - t0)


def report(R, secs):
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK16_PLAN.md", "jk16.py")}
    L = ["# J-K16 — 10 seed (sinh tự động)", "",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Thời gian lượt này {secs/60:.0f} phút.", ""]
    A = {s: R[("A", s)] for s in SEEDS}
    a1 = sum(A[s][c]["recall"]["G"]["kmin"] < 0.85 for s in SEEDS for c in CONFIGS)
    ks = [A[s][c][sc]["KSU*"]["kmin"] for s in SEEDS for c in CONFIGS for sc in ("recall", "prec", "min")]
    a2 = sum(v >= 0.88 for v in ks) >= 0.95 * len(ks) and min(ks) >= 0.86
    Bd = {s: R[("B", s)] for s in SEEDS}
    kb = [Bd[s][st]["KSU*"]["kmin"] for s in SEEDS for st in jk12.SET_A]
    gb = [Bd[s][st]["G"]["kmin"] for s in SEEDS for st in jk12.SET_A]
    b1 = sum(v >= 0.88 for v in kb) >= 0.95 * len(kb) and min(kb) >= 0.86 and sum(v < 0.85 for v in gb) >= 0.75 * len(gb)
    rng = np.random.default_rng(7); rho = {}
    for s in SEEDS:
        x = [Bd[s][st]["_kset"] for st in jk12.SET_A]; y = [Bd[s][st]["KSU*"]["size"] / Bd[s][st]["WCP"]["size"] for st in jk12.SET_A]
        rho[s] = perm_p(x, y, rng)
    b2 = np.median([r for r, _ in rho.values()]) >= 0.7 and sum(p < 0.05 for _, p in rho.values()) >= 8
    L += ["## Kết luận theo tiêu chí khóa trước", "",
          f"- A1 (G < 0,85, recall): {a1}/90 → {'đạt' if a1 >= 85 else 'trượt'}",
          f"- A2 (KSU* ≥ 0,88 ở ≥ 95% của 270, min ≥ 0,86): {sum(v >= 0.88 for v in ks)}/270, min {min(ks):.3f} → {'đạt' if a2 else 'trượt'}",
          f"- B1 (mô phỏng: KSU* ≥ 0,88 ở ≥ 95% của 180, min ≥ 0,86; G < 0,85 ở ≥ 75%): KSU* {sum(v >= 0.88 for v in kb)}/180, min {min(kb):.3f}; G {sum(v < 0.85 for v in gb)}/180 → {'đạt' if b1 else 'trượt'}",
          f"- B2 (C3): ρ theo seed {', '.join(f'{r:.2f}' for r, _ in rho.values())}; trung vị {np.median([r for r, _ in rho.values()]):.2f}; p<0,05 ở {sum(p < 0.05 for _, p in rho.values())}/10 → {'đạt' if b2 else 'trượt'}", "",
          f"Kiểm tính đúng seed 0: ρ = {rho[0][0]:.3f} (J-K12A: 0,89)", "",
          "## Phần A — trung bình ± độ lệch chuẩn qua 10 seed (phủ k xấu nhất / kích thước)", ""]
    for sc in ("recall", "prec", "min"):
        L += [f"### {sc}", "", "| Đồ thị | R0 | " + " | ".join(METH) + " |", "|---|---|" + "---|" * len(METH)]
        for c in CONFIGS:
            cells = []
            for m in METH:
                km = np.array([A[s][c][sc][m]["kmin"] for s in SEEDS]); sz = np.array([A[s][c][sc][m]["size"] for s in SEEDS])
                cells.append(f"{km.mean():.2f} ± {km.std(ddof=1):.2f} (min {km.min():.2f}) / {sz.mean():.1f} ± {sz.std(ddof=1):.1f}")
            L.append(f"| {c[0]} | {c[1]} | " + " | ".join(cells) + " |")
        L.append("")
    L += ["## Phần B — 18 thiết lập C3, trung bình ± độ lệch chuẩn qua 10 seed", "",
          "| Thiết lập | \\|K̂\\| | G phủ k xấu nhất | KSU* phủ k xấu nhất | KSU*/WCP |", "|---|---|---|---|---|"]
    for st in jk12.SET_A:
        kk = np.array([Bd[s][st]["_kset"] for s in SEEDS]); g = np.array([Bd[s][st]["G"]["kmin"] for s in SEEDS])
        k_ = np.array([Bd[s][st]["KSU*"]["kmin"] for s in SEEDS]); r = np.array([Bd[s][st]["KSU*"]["size"] / Bd[s][st]["WCP"]["size"] for s in SEEDS])
        L.append(f"| {st[0]} {st[1]} {st[2]} | {kk.mean():.2f} ± {kk.std(ddof=1):.2f} | {g.mean():.2f} ± {g.std(ddof=1):.2f} | {k_.mean():.2f} ± {k_.std(ddof=1):.2f} (min {k_.min():.2f}) | {r.mean():.2f} ± {r.std(ddof=1):.2f} |")
    open(os.path.join(HERE, "results", "JK16_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:14]), flush=True)


if __name__ == "__main__":
    main()
