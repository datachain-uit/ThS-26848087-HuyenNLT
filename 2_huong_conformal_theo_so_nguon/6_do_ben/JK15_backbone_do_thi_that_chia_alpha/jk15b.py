"""J-K15 Phần B — đồ thị thật ngoài LFR (power_grid, cora_ml), giao thức y hệt J-K11. Giao thức: JK15_PLAN.md.
Chạy: python jk15b.py [--smoke]"""
import _venv; _venv.ensure()
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
for p in ("2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK11_do_thi_lon", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k", "1_huong_cong_dong/5_E0_ho_so_cong_dong_da_thang", "2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK2_lech_mo_hinh", "2_huong_conformal_theo_so_nguon/3_KSU_bao_dam_theo_k/JK5_so_sanh_MDCP", "2_huong_conformal_theo_so_nguon/4_gia_cua_bao_dam/JK8_diem_theo_k"):
    sys.path.append(os.path.join(B, p))
import datetime as dt, hashlib, pickle, platform, time
import numpy as np, scipy.sparse as sp
import jk11
os.chdir(HERE)

SMOKE = jk11.SMOKE
GRAPHS = ("power_grid", "cora_ml")
SETTINGS = [(g, m, t) for g in GRAPHS for t in (50, 200) for m in ("SI", "IC", "SIR")]
MAX_TRY = 400_000
OUT = os.path.join(HERE, "results", "JK15B_raw.pkl")
SCEN = ("S1", "S2", "S3", "S4")


def load(gid):
    g = pickle.load(open(os.path.join(B, "1_huong_cong_dong/2_baseline_GraphSL", "data", gid), "rb"))
    A = sp.csr_matrix(g["adj_mat"], dtype=float); A = ((A + A.T) > 0).astype(float); A.setdiag(0); A.eliminate_zeros()
    return A.shape[0], sp.csr_matrix(A)


class TooHard(Exception):
    pass


def simulate(A, n, sim, rng, target):
    out, tries = [], 0
    while len(out) < jk11.NS:
        tries += 1
        if tries > MAX_TRY:
            raise TooHard(f"chỉ được {len(out)}/{jk11.NS} mẫu sau {MAX_TRY} lần thử")
        k = int(rng.integers(1, 16)); src = rng.choice(n, k, replace=False)
        inf = sim(A, src, rng, target)
        if inf is None or len(inf) != target:
            continue
        out.append((np.asarray(inf, int), np.asarray(src, int)))
    return out


jk11.load = load
jk11.simulate = simulate


def main():
    cache = {}
    if SMOKE:
        r = jk11.run(0, "power_grid", "IC", 50, cache)
        open(os.path.join(HERE, "results", "JK15B_smoke.txt"), "w", encoding="utf-8").write(f"smoke ok; n={cache['power_grid'][0]}\n")
        print("smoke ok", flush=True); return
    t0 = time.time(); R = pickle.load(open(OUT, "rb")) if os.path.exists(OUT) else {}
    for si, s in enumerate(SETTINGS):
        if s in R:
            continue
        print(f"[{dt.datetime.now():%H:%M}] {s}", flush=True)
        try:
            R[s] = jk11.run(200 + si, *s, cache)
        except TooHard as e:
            R[s] = {"skip": str(e)}; print("  bỏ:", e, flush=True)
        pickle.dump(R, open(OUT, "wb"))
    report(R, time.time() - t0)


def report(R, secs):
    sha = {p: hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest()[:16] for p in ("JK15_PLAN.md", "jk15b.py")}
    ok = [s for s in SETTINGS if "skip" not in R[s]]
    b1 = sum(R[s]["G"]["kmin"] < 0.85 for s in ok); b2 = sum(R[s]["KSU*"]["kmin"] >= 0.88 for s in ok)
    B1, B2 = b1 >= len(ok) / 2, b2 == len(ok)
    v = "TỔNG QUÁT HÓA" if B1 and B2 else ("MỘT PHẦN" if B2 else "CẦN XEM LẠI")
    L = ["# J-K15 Phần B — báo cáo (sinh tự động)", "",
         f"{dt.datetime.now():%d/%m/%Y %H:%M}. {platform.system()}, Python {platform.python_version()}. SHA {sha}. Thời gian {secs/60:.0f} phút.", "",
         f"## Kết luận: **{v}**", "", f"- Mô phỏng được {len(ok)}/{len(SETTINGS)} thiết lập",
         f"- B1 (G < 0,85 ở k xấu nhất): {b1}/{len(ok)} → {'đạt' if B1 else 'trượt'}",
         f"- B2 (KSU* ≥ 0,88): {b2}/{len(ok)} → {'đạt' if B2 else 'trượt'}", "",
         "| Đồ thị | Mô hình | Vùng nhiễm | \\|K̂\\| | G | O | WCP | MDCP | KSU* |", "|---|---|---|---|---|---|---|---|---|"]
    for s in SETTINGS:
        r = R[s]
        if "skip" in r:
            L.append(f"| {s[0]} | {s[1]} | {s[2]} | — | không mô phỏng được: {r['skip']} |||||"); continue
        cell = lambda m: f"{r[m]['kmin']:.2f} [{r[m]['kmin_lo']:.2f}] (k={r[m]['kargmin']}) / {r[m]['size']:.1f} ± {r[m]['size_hw']:.1f}"
        L.append(f"| {s[0]} | {s[1]} | {s[2]} | {r['_kset']:.1f} | " + " | ".join(cell(m) for m in ("G", "O", "WCP", "MD", "KSU*")) + " |")
    L += ["", "Mỗi ô: phủ ở k xấu nhất [cận Wilson] (k) / kích thước ± nửa KTC 95%.", "",
          "### Lệch prior (S1 / S2 / S3 / S4)", "", "| Đồ thị | Mô hình | Vùng nhiễm | G | WCP | KSU* |", "|---|---|---|---|---|---|"]
    for s in ok:
        r = R[s]
        L.append(f"| {s[0]} | {s[1]} | {s[2]} | " + " | ".join(" / ".join(f"{r[m][x]:.2f}" for x in SCEN) for m in ("G", "WCP", "KSU*")) + " |")
    open(os.path.join(HERE, "results", "JK15B_REPORT.md"), "w", encoding="utf-8").write("\n".join(L))
    print("\n".join(L[:10]), flush=True)


if __name__ == "__main__":
    main()
