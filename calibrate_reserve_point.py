# calibrate_reserve_point.py
import numpy as np, os

# nhập giá trị bạn đo từ robot UI
RESERVE_POSE = dict(
    X=214.2,
    Y=-161.4,
    Z=135.9,
    A=-179.7,
    B=0.7,
    C=-178
)

os.makedirs("D:/doancaro/calibration", exist_ok=True)
np.savez("D:/doancaro/calibration/reserve_point.npz", **RESERVE_POSE)
print("[OK] Lưu reserve_point.npz:", RESERVE_POSE)
