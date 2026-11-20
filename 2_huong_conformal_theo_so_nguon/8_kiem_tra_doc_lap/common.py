import sys, os, types
if os.name == "nt":  # Windows: chạy lại bằng .venv chung của dự án (có đủ thư viện)
    import _venv; _venv.ensure()
else:
    sys.modules['_venv'] = types.SimpleNamespace(ensure=lambda: None)
B = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
for p in ("2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK1_phu_theo_k", "1_huong_cong_dong/5_E0_ho_so_cong_dong_da_thang", "2_huong_conformal_theo_so_nguon/1_tap_du_doan_so_nguon/PK2_lech_mo_hinh", "2_huong_conformal_theo_so_nguon/0_tai_lap_Jian2026/cnsd", "2_huong_conformal_theo_so_nguon/2_chan_doan_phu_theo_k/JK11_do_thi_lon"):
    sys.path.append(os.path.join(B, p))
import math
import numpy as np
def qconf(v, a):
    """Phân vị conformal chuẩn (viết lại độc lập): phần tử thứ ceil((1-a)(n+1)) của v đã sắp; +inf nếu vượt n."""
    v = np.sort(np.asarray(v, float)); r = math.ceil((1 - a) * (len(v) + 1) - 1e-12)
    return np.inf if (len(v) == 0 or r > len(v)) else float(v[r - 1])
def wcp_vec(calv, calk, W, alpha):
    """WCP (Wang et al., Alg. 1) viết lại độc lập: với mỗi hàng w của W, q nhỏ nhất thỏa sum_c w_c m_c(q)/(n_c+1) >= 1-alpha."""
    qs = np.unique(calv); F = np.zeros((15, len(qs)))
    for c in range(1, 16):
        s = calv[calk == c]
        if len(s):
            F[c - 1] = np.array([np.count_nonzero(s <= q) for q in qs]) / (len(s) + 1) if len(qs) < 300 else np.searchsorted(np.sort(s), qs, side="right") / (len(s) + 1)
    T = W @ F; ok = T >= 1 - alpha
    return np.where(ok.any(1), qs[np.argmax(ok, 1)], np.inf)
