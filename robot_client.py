# robot_client.py — lớp điều khiển robot an toàn cho pick/place theo XY (base)
import time, os, numpy as np
from pathlib import Path
from cri_lib import CRIController

# Một số bản có MotionType; nếu không có thì bỏ qua
try:
    from cri_lib.cri_controller import MotionType
except Exception:
    MotionType = None

class RobotClient:
    def __init__(self, ip="192.168.3.11", port=3920,
                 Z_TABLE=130.0,          # cao độ mặt bàn (mm) bạn đã đo
                 approach_up=30.0,       # z cố định +30mm
                 touch=1.5,              # chạm hút: Z_TABLE + touch
                 a=180.0, b=0.0, c=-180.0,
                 v_approach=150.0, v_touch=50.0,
                 override=60.0):
        self.Z_TABLE = float(Z_TABLE)
        self.Z_APPROACH = self.Z_TABLE + float(approach_up)
        self.Z_PICK = self.Z_TABLE + float(touch)
        self.a, self.b, self.c = float(a), float(b), float(c)
        self.v_approach, self.v_touch = float(v_approach), float(v_touch)

        self.rb = CRIController()
        ok = self.rb.connect(ip, port)
        if not ok:
            raise RuntimeError("Không kết nối được iRC")
        self.rb.set_active_control(True)
        self.rb.enable()
        try:
            self.rb.wait_for_kinematics_ready(10)
        except Exception:
            pass
        self.rb.set_override(float(override))
        if MotionType is not None:
            try:
                self.rb.set_motion_type(MotionType.CartBase)
            except Exception:
                pass
        print(f"[READY] Z_TABLE={self.Z_TABLE:.2f}  APPROACH={self.Z_APPROACH:.2f}  PICK={self.Z_PICK:.2f}")

    # ====== IO hút ======
    def vacuum_on(self):
        self.rb.set_dout(22, True);  print("[VAC] ON")

    def vacuum_off(self):
        self.rb.set_dout(22, False); print("[VAC] OFF")

    # ====== Move helpers (luôn truyền E1,E2,E3) ======
    def move_above(self, X, Y, vel=None):
        v = self.v_approach if vel is None else float(vel)
        return self.rb.move_cartesian(
            X=float(X), Y=float(Y), Z=self.Z_APPROACH,
            A=self.a, B=self.b, C=self.c,
            E1=0.0, E2=0.0, E3=0.0,
            velocity=v, frame="#base",
            wait_move_finished=True, move_finished_timeout=100.0
        )

    def touch_down(self, X, Y, vel=None):
        v = self.v_touch if vel is None else float(vel)
        return self.rb.move_cartesian(
            X=float(X), Y=float(Y), Z=self.Z_PICK,
            A=self.a, B=self.b, C=self.c,
            E1=0.0, E2=0.0, E3=0.0,
            velocity=v, frame="#base",
            wait_move_finished=True, move_finished_timeout=100.0
        )

    def lift_up(self, X, Y, vel=None):
        return self.move_above(X, Y, vel=vel)

    # ====== Pick / Place theo toạ độ base (mm) ======
    def pick_at(self, X, Y, dwell=1):
        # Di chuyển đến vị trí, chạm xuống, BẬT VACUUM để hút quân, nhấc lên
        # Vacuum sẽ ON sau khi hoàn thành
        print(f"[PICK@] ({X:.1f},{Y:.1f})")
        self.move_above(X, Y)
        self.touch_down(X, Y)
        self.vacuum_on()  # Bật vacuum để hút quân
        time.sleep(float(dwell))
        self.lift_up(X, Y)  # Nhấc lên (vacuum vẫn ON)

    def place_at(self, X, Y, dwell=1, release_delay=2.0):
        # Di chuyển đến vị trí, chạm xuống, TẮT VACUUM để thả quân, chờ thả hoàn toàn, nhấc lên
        # Vacuum sẽ OFF sau khi hoàn thành
        # @param dwell Thời gian chờ sau khi chạm xuống (giây)
        # @param release_delay Thời gian chờ sau khi tắt vacuum để quân cờ thả ra hoàn toàn (giây)
        print(f"[PLACE@] ({X:.1f},{Y:.1f})")
        self.move_above(X, Y)
        self.touch_down(X, Y)
        time.sleep(float(dwell))  # Chờ ổn định sau khi chạm xuống
        self.vacuum_off()  # Tắt vacuum để thả quân
        time.sleep(float(release_delay))  # Chờ quân cờ thả ra hoàn toàn trước khi nhấc lên
        self.lift_up(X, Y)  # Nhấc lên (vacuum đã OFF, quân cờ đã được thả)

    # ====== Lấy quân từ khay dự trữ (reserve_point.npz) ======
    def pick_from_reserve(self, dwell=1):
        # Di chuyển đến khay dự trữ, chạm xuống, BẬT VACUUM để hút quân, nhấc lên
        # Vacuum sẽ ON sau khi hoàn thành (quân cờ được giữ)
        p = Path(__file__).resolve().parent / "calibration" / "reserve_point.npz"
        if not p.exists():
            raise FileNotFoundError("Chưa có reserve_point.npz — hãy teach vị trí khay trước.")
        d = np.load(str(p))
        Xr, Yr, Zr = float(d["X"]), float(d["Y"]), float(d["Z"])
        Ar, Br, Cr = float(d["A"]), float(d["B"]), float(d["C"])
        Z_APP = Zr + 30.0  # Độ cao tiếp cận
        Z_PK  = Zr + 1.0   # Độ cao hút

        print(f"[RESERVE] ({Xr:.1f},{Yr:.1f},{Zr:.1f})")
        # Di chuyển đến vị trí tiếp cận
        self.rb.move_cartesian(X=Xr, Y=Yr, Z=Z_APP, A=Ar, B=Br, C=Cr,
                               E1=0.0, E2=0.0, E3=0.0,
                               velocity=self.v_approach, frame="#base",
                               wait_move_finished=True)
        # Hạ xuống để hút
        self.rb.move_cartesian(X=Xr, Y=Yr, Z=Z_PK, A=Ar, B=Br, C=Cr,
                               E1=0.0, E2=0.0, E3=0.0,
                               velocity=self.v_touch, frame="#base",
                               wait_move_finished=True)
        # Bật vacuum và chờ
        self.vacuum_on()
        time.sleep(dwell)
        # Nhấc lên (vacuum vẫn ON, quân cờ được giữ)
        self.rb.move_cartesian(X=Xr, Y=Yr, Z=Z_APP, A=Ar, B=Br, C=Cr,
                               E1=0.0, E2=0.0, E3=0.0,
                               velocity=self.v_approach, frame="#base",
                               wait_move_finished=True)

    def close(self):
        # Đóng kết nối và tắt vacuum để an toàn
        try: self.vacuum_off()
        except: pass
        try: self.rb.disable()
        except: pass
        try: self.rb.close()
        except: pass
        print("[CLOSE] Controller closed.")

