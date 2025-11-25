#!/usr/bin/env python3
#+ Teach reserve point for pick_from_reserve()
#+
#+ Usage:
#+   1. Jog robot (bằng pendant hoặc giao diện iRC) tới đúng vị trí khay quân,
#+      đặt đầu hút cách mặt khay khoảng 1 mm (trạng thái hút TẮT).
#+   2. Chạy:  python3 teach_reserve_point.py
#+      Script sẽ kết nối robot, đọc toạ độ hiện tại và lưu vào
#+      calibration/reserve_point.npz
#+
#+ Sau khi reserve_point.npz được tạo, GridRobot.pick_from_reserve() sẽ sử dụng
#+ toạ độ này để lấy quân tự động.

import numpy as np
from pathlib import Path
from robot_client import RobotClient


def main() -> None:
    reserve_path = Path(__file__).resolve().parent / "calibration" / "reserve_point.npz"
    reserve_path.parent.mkdir(parents=True, exist_ok=True)

    print("=== Teach reserve point ===")
    print("• Đảm bảo robot đã được đưa tới vị trí khay và dừng lại")
    input("Nhấn Enter để ghi nhận toạ độ hiện tại...")

    client = RobotClient()
    pose = client.rb.robot_state.position_robot

    np.savez(
        reserve_path,
        X=float(pose.X),
        Y=float(pose.Y),
        Z=float(pose.Z),
        A=float(pose.A),
        B=float(pose.B),
        C=float(pose.C),
    )
    client.close()

    print(f"[DONE] Đã lưu reserve_point vào: {reserve_path}")


if __name__ == "__main__":
    main()

