# calibrate_board_to_robot.py
import numpy as np, os, math

L = 282.0  # mm, cạnh bàn

print("Nhập X,Y (mm, base robot) mà bạn đọc trên iRC cho 3 điểm:")
X0 = float(input("O  (0,0)  -> X = "));  Y0 = float(input("                Y = "))
Xx = float(input("OX (L,0)  -> X = "));  Yx = float(input("                Y = "))
Xy = float(input("OY (0,L)  -> X = "));  Yy = float(input("                Y = "))

P0 = np.array([X0, Y0], dtype=float)   # robot base tại# O
P1 = np.array([Xx, Yx], dtype=float)   # robot base tại OX
P2 = np.array([Xy, Yy], dtype=float)   # robot base tại OY

# Ma trận 2x2 và tịnh tiến:
# S*[x_b, y_b]^T + t = [X_r, Y_r]^T
col_x = (P1 - P0) / L     # cột 1 ứng với trục +X_b
col_y = (P2 - P0) / L     # cột 2 ứng với trục +Y_b
S = np.column_stack([col_x, col_y])
t = P0

# 3x3 cho tiện dùng dạng đồng nhất
T = np.array([[S[0,0], S[0,1], t[0]],
              [S[1,0], S[1,1], t[1]],
              [0.0,    0.0,    1.0]], dtype=float)

os.makedirs("D:/doancaro/calibration", exist_ok=True)
np.savez("D:/doancaro/calibration/board2base.npz", T=T, L=L)

# Thống kê kiểm tra
sx = np.linalg.norm(col_x); sy = np.linalg.norm(col_y)
theta = math.degrees(math.atan2(col_x[1], col_x[0]))  # góc trục +X_b so với +X_base
print("\n[OK] Lưu T tại D:/doancaro/calibration/board2base.npz")
print("T =\n", T)
print(f"scale_x~{sx:.4f}, scale_y~{sy:.4f} (gần 1.0 là đúng),  góc~{theta:.2f}°")
