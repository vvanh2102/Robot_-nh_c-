# grid_actions.py — API ô lưới 13x13 -> robot base
import os, numpy as np
from robot_client import RobotClient

CELL_MM   = 23.5
GRID_SIZE = 13
L = (GRID_SIZE - 1) * CELL_MM  # 282 mm

# bật nếu hệ bàn của bạn đang bị đảo trục khi quy đổi row/col
AXIS_SWAP = False     # True: hoán row<->col trong grid_to_board_mm() False
FLIP_ROW  = True       # lật theo hàng: r -> 12 - r
FLIP_COL  = True       # lật theo cột:  c -> 12 - c
# ma trận board->base (teach 3 điểm)
T_PATH = "D:/doancaro/calibration/board2base.npz"
if not os.path.exists(T_PATH):
    raise FileNotFoundError("Thiếu board2base.npz — hãy chạy calibrate_board_to_robot.py")
T = np.load(T_PATH)["T"]

def grid_to_board_mm(row, col):
    """
    (row,col) -> (x_b,y_b) mm trong hệ BÀN.
    Quy ước: O ở PHẢI-DƯỚI; +X sang TRÁI (col tăng); +Y lên TRÊN (row tăng).
    """
    # chuẩn hoá theo cờ
    r, c = int(row), int(col)
    if FLIP_ROW:  r = (GRID_SIZE - 1) - r
    if FLIP_COL:  c = (GRID_SIZE - 1) - c
    if AXIS_SWAP: r, c = c, r

    xb = c * CELL_MM
    yb = r * CELL_MM
    return float(xb), float(yb)
    #if AXIS_SWAP:
     #   row, col = col, row
    #xb = col * CELL_MM
    #yb = row * CELL_MM
    #return float(xb), float(yb)

def board_to_robot_xy(xb, yb):
    """(x_b,y_b) -> (X_r,Y_r) trong hệ BASE ROBOT."""
    xr, yr, _ = T @ np.array([xb, yb, 1.0], float)
    return float(xr), float(yr)

def cell_to_robot_xy(row, col):
    xb, yb = grid_to_board_mm(row, col)
    return board_to_robot_xy(xb, yb)

class GridRobot:
    def __init__(self, Z_TABLE=128.0):
        self.rb = RobotClient(Z_TABLE=Z_TABLE, approach_up=30.0, touch=1.5)

    def pick_cell(self, row, col):
        Xr, Yr = cell_to_robot_xy(row, col)
        print(f"[PICK_CELL] ({row},{col}) -> base({Xr:.1f},{Yr:.1f})")
        self.rb.pick_at(Xr, Yr)

    def place_cell(self, row, col):
        Xr, Yr = cell_to_robot_xy(row, col)
        print(f"[PLACE_CELL] ({row},{col}) -> base({Xr:.1f},{Yr:.1f})")
        self.rb.place_at(Xr, Yr)

    def pick_from_reserve(self):
        self.rb.pick_from_reserve()

    def close(self):
        self.rb.close()

# test nhanh khi chạy file này trực tiếp
#if __name__ == "__main__":
#    print("Kiểm tra mapping (4 góc & tâm):")
#    for r, c in [(0,0),(0,12),(12,0),(12,12),(6,6)]:
#        Xr, Yr = cell_to_robot_xy(r, c)
#        print(f"  cell({r:02d},{c:02d}) -> base({Xr:.1f},{Yr:.1f})")
