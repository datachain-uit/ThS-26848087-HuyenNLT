"""Tham số H0. Khớp H0_PROTOCOL.md Mục 4-8. Không sửa sau khi khóa giao thức."""
import numpy as np

MASTER_SEED = 2026          # seed gốc cho lượt chạy chính
SMOKE_SEED = 9999           # seed riêng cho chạy thử, để không nhìn trước dữ liệu chính

# --- Đồ thị (Mục 4) ---
LFR_N = 1000
LFR_MUS = [0.1, 0.3, 0.5]
LFR_PER_MU = 5
LFR_PARAMS = dict(tau1=3, tau2=1.5, average_degree=10, max_degree=50,
                  min_community=20, max_community=100)
LFR_MAX_TRIES = 50
USE_EMAIL_EU = True
EMAIL_EDGES_URL = "https://snap.stanford.edu/data/email-Eu-core.txt.gz"
EMAIL_LABELS_URL = "https://snap.stanford.edu/data/email-Eu-core-department-labels.txt.gz"

# --- Phân hoạch (Mục 5) ---
GAMMAS = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 5.0]
PART_SEEDS = [0, 1, 2, 3, 4]
DEFAULT_PART = (1.0, 0)     # (gamma, seed) mặc định
N_RANDOM_PARTS = 5          # mức sàn, không dùng cho H-a

# --- Cascade (Mục 6) ---
KS = [1, 3, 5]
N_VAL = 50
N_TEST = 200
TARGET_FRAC = 0.15
FRAC_RANGE = (0.10, 0.20)
P_GRID = np.unique(np.concatenate([np.geomspace(0.01, 0.6, 40), np.linspace(0.6, 0.99, 14)]))
N_CALIB = 100
MAX_REJECT = 200           # số lần thử tối đa cho mỗi cascade giữ lại

# --- Bộ định vị (Mục 7) ---
RHOS = [1, 2, 3, 4, 5, 6]
RHO_CRITERION = "ed"     # chọn rho trên val theo ED (metric chính của cô)
LPSI_ALPHA = 0.5

# --- Chấm điểm (Mục 8) ---
F1_HOPS = [0, 1, 2]

# --- Quy tắc quyết định H-a (Mục 1) ---
HA_DELTA_ABS = 0.3
HA_DELTA_REL = 0.10
HA_ETA2 = 0.20
HA_K_PASS = 2               # đồ thị đạt khi >= 2/3 giá trị k đạt
HA_GRAPH_FRAC = 2 / 3       # GO khi >= 2/3 số đồ thị đạt
HB_RHO = 0.5

# --- Chạy thử (smoke) ---
SMOKE = dict(mus=[0.3], per_mu=1, email=False, gammas=[0.3, 0.7, 1.0, 2.0, 5.0],
             part_seeds=[0, 1], ks=[1, 3], n_val=20, n_test=20, n_calib=30)
