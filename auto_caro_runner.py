# auto_caro_runner.py — YOLO(bàn + quân) -> chỉ xuất (row,col); robot đi bằng grid_actions
# Phím:
#   s - Start nhận diện
#   p - Freeze + nhập (row,col) qua console → pick_from_reserve → place → về REF → resume
#   r - Reset board-state
#   q - Quit

import os
import time
import cv2
import numpy as np
from ultralytics import YOLO

# ====== ĐƯỜNG DẪN / MODEL ======
BOARD_MODEL_PATH = "D:/doancaro/modelbc1/last.pt"   # YOLO model bàn cờ
PIECE_MODEL_PATH = "D:/doancaro/modelco/last.pt"   # YOLO model quân cờ
SAVE_DIR = "D:/doancaro/runs"
os.makedirs(SAVE_DIR, exist_ok=True)

# ====== LƯỚI ======
GRID_SIZE = 13
SHRINK_FACTOR = 0.98     # co bớt bbox YOLO-bàn để bỏ viền giấy
CONF_PIECE = 0.45         # ngưỡng YOLO-quân

# ====== ROBOT / GRID-ACTIONS ======
from grid_actions import GridRobot
REF_POSE = dict(X=214.2, Y=-6.0, Z=439.9, A=-178.1, B=0.7, C=-180.0)

def goto_ref(gr, vel=150.0):
    """Về REF_POSE bằng controller bên trong RobotClient."""
    rb = gr.rb.rb  # CRIController instance
    ok = rb.move_cartesian(
        X=REF_POSE["X"], Y=REF_POSE["Y"], Z=REF_POSE["Z"],
        A=REF_POSE["A"], B=REF_POSE["B"], C=REF_POSE["C"],
        E1=0.0, E2=0.0, E3=0.0,
        velocity=float(vel), frame="#base",
        wait_move_finished=True, move_finished_timeout=120.0
    )
    time.sleep(0.3)
    return ok

# ====== TIỆN ÍCH ======
def clamp_idx(v, lo=0, hi=12):
    return int(max(lo, min(hi, int(round(v)))))

def draw_grid_from_roi(img, x1, y1, x2, y2, color=(0,0,255)):
    """Vẽ lưới 13x13 nội suy theo ROI."""
    step_x = (x2 - x1) / (GRID_SIZE - 1)
    step_y = (y2 - y1) / (GRID_SIZE - 1)
    # nút giao (xanh lá)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            u = int(round(x1 + c * step_x))
            v = int(round(y1 + r * step_y))
            cv2.circle(img, (u, v), 2, (0,255,0), -1)
    # đường lưới (đỏ)
    for c in range(GRID_SIZE):
        u = int(round(x1 + c * step_x))
        cv2.line(img, (u, y1), (u, y2), color, 1)
    for r in range(GRID_SIZE):
        v = int(round(y1 + r * step_y))
        cv2.line(img, (x1, v), (x2, v), color, 1)

def find_board_roi(frame_bgr, board_model, last_roi=None):
    """
    Dùng YOLO-bàn để tìm ROI. Nếu không thấy, trả về last_roi (nếu có).
    Trả về (x1,y1,x2,y2) hoặc None.
    """
    res = board_model(frame_bgr, verbose=False)[0]
    if res.boxes is not None and len(res.boxes) > 0:
        bb = res.boxes.xyxy.cpu().numpy()
        x1,y1,x2,y2 = map(int, max(bb, key=lambda a:(a[2]-a[0])*(a[3]-a[1])))
        # co bớt viền
        w, h = x2 - x1, y2 - y1
        dx, dy = int(w*(1-SHRINK_FACTOR)/2), int(h*(1-SHRINK_FACTOR)/2)
        x1 += dx; y1 += dy; x2 -= dx; y2 -= dy
        # clip vào khung ảnh
        H, W = frame_bgr.shape[:2]
        x1 = max(0, min(W-1, x1)); x2 = max(1, min(W-1, x2))
        y1 = max(0, min(H-1, y1)); y2 = max(1, min(H-1, y2))
        if x2 - x1 > 40 and y2 - y1 > 40:
            return (x1, y1, x2, y2)
    return last_roi

def detect_board_state(frame_bgr, roi, piece_model, conf=0.45):
    """
    Tạo board_state 13x13 chỉ bằng (row,col) trong ROI YOLO-bàn.
    Không quy đổi mm, chỉ (0..12,0..12).
    """
    final = frame_bgr.copy()
    board_state = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8)

    if roi is None:
        cv2.putText(final, "No board ROI", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
        return final, board_state

    x1,y1,x2,y2 = roi
    step_x = (x2 - x1) / (GRID_SIZE - 1)
    step_y = (y2 - y1) / (GRID_SIZE - 1)

    # Vẽ lưới tham chiếu
    draw_grid_from_roi(final, x1, y1, x2, y2)

    # Cắt ROI để YOLO-quân bền vững hơn
    roi_img = frame_bgr[y1:y2, x1:x2]
    pres = piece_model(roi_img, conf=conf, verbose=False)[0]
    if pres.boxes is None or len(pres.boxes) == 0:
        cv2.rectangle(final, (x1,y1), (x2,y2), (255,0,0), 2)
        return final, board_state

    xyxy = pres.boxes.xyxy.cpu().numpy()
    cls  = pres.boxes.cls.cpu().numpy().astype(int)

    for k, (bx1, by1, bx2, by2) in enumerate(xyxy):
        cx = (bx1 + bx2) / 2.0
        cy = (by1 + by2) / 2.0

        # Toạ độ "toàn cục" trên ảnh
        u = x1 + cx
        v = y1 + cy

        # Quy đổi sang (row,col) bằng chuẩn hoá theo ROI
        col = clamp_idx((u - x1) / step_x)  # 0..12
        row = clamp_idx((v - y1) / step_y)  # 0..12

        val = 1 if cls[k] == 0 else 2  # 0: đen, 1: vàng (đổi nếu model khác)
        board_state[row, col] = val

        color = (0,255,0) if val == 1 else (0,255,255)
        cv2.circle(final, (int(u), int(v)), 6, color, -1)
        cv2.putText(final, f"{row},{col}", (int(u)+6, int(v)-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)

    # Khung ROI để quan sát
    cv2.rectangle(final, (x1,y1), (x2,y2), (255,0,0), 2)
    return final, board_state

def main():
    print("[INIT] Load YOLO models & robot …")
    board_model = YOLO(BOARD_MODEL_PATH)
    piece_model = YOLO(PIECE_MODEL_PATH)

    # Robot qua GridRobot (Z_TABLE bạn chỉnh theo thực tế)
    gr = GridRobot(Z_TABLE=130.0)

    # Về REF khi khởi động
    print("[INIT] Move to REF_POSE …")
    goto_ref(gr, vel=150.0)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Không mở được camera 0.")
    print("\n[READY] Phím: s=Start  p=Place  r=Reset  q=Quit\n")

    running = False
    frozen  = False
    last_board_state = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8)
    last_roi = None
    frame0 = None

    while True:
        if not frozen:
            ok, frame = cap.read()
            if not ok: break
            frame0 = frame

            # tìm ROI bàn (ưu tiên YOLO; fallback dùng last_roi)
            roi = find_board_roi(frame, board_model, last_roi)
            if roi is not None: last_roi = roi

            if running:
                final, board_state = detect_board_state(frame, last_roi, piece_model, conf=CONF_PIECE)
            else:
                final, board_state = frame.copy(), last_board_state

            # Ô trạng thái nhỏ
            disp = np.ones((GRID_SIZE*22, GRID_SIZE*22, 3), np.uint8) * 255
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    if board_state[r, c] != 0:
                        colr = (0,0,255)
                        cv2.putText(disp, str(board_state[r, c]),
                                    (c*22+6, r*22+16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colr, 1)

            cv2.putText(final, "[s] Start  [p] Place  [r] Reset  [q] Quit",
                        (16, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 30, 30), 2)
            cv2.imshow("AUTO CARO RUNNER (YOLO grid only)", final)
            cv2.imshow("Board State", disp)

            # In console (tối giản): toạ độ đang thấy
            # (Bạn có thể comment nếu spam)
            # coords = np.argwhere(board_state > 0)
            # if coords.size > 0:
            #     print("Detected (row,col):", [tuple(map(int, x)) for x in coords])

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        elif key == ord('s'):
            running = True
            print("[STATE] RUNNING")

        elif key == ord('r'):
            last_board_state = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8)
            print("[STATE] Reset board_state.")

        elif key == ord('p'):
            # Freeze + lưu trạng thái trước
            frozen = True
            print("[STATE] FROZEN. Chuẩn bị đặt quân…")

            # chụp lại + detect trước khi move
            before_final, before_board = detect_board_state(frame0 if frame0 is not None else frame,
                                                            last_roi, piece_model, conf=CONF_PIECE)
            ts = int(time.time())
            before_img = os.path.join(SAVE_DIR, f"before_{ts}.jpg")
            before_npy = os.path.join(SAVE_DIR, f"before_{ts}.npy")
            cv2.imwrite(before_img, before_final);  np.save(before_npy, before_board)
            print(f"[SAVE] Trước khi đặt: {before_img}, {before_npy}")

            try:
                raw = input("Nhập toạ độ (row,col) [0..12], ví dụ 6,6: ").strip()
                parts = raw.replace(" ", "").split(",")
                if len(parts) != 2: raise ValueError("Sai định dạng, cần 'row,col'.")
                row = int(parts[0]); col = int(parts[1])
                if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
                    raise ValueError("row/col ngoài phạm vi 0..12.")
                print(f"[CMD] place at cell ({row},{col})")

                # 1) Lấy quân từ khay
                gr.pick_from_reserve()

                # 2) Đặt vào ô (grid_actions lo toạ độ chính xác)
                gr.place_cell(row, col)

                # 3) Về REF
                goto_ref(gr, vel=150.0)

                # 4) Resume + lưu sau
                frozen = False
                ok, frame = cap.read()
                if ok:
                    after_final, after_board = detect_board_state(frame, last_roi, piece_model, conf=CONF_PIECE)
                    after_img = os.path.join(SAVE_DIR, f"after_{ts}.jpg")
                    after_npy = os.path.join(SAVE_DIR, f"after_{ts}.npy")
                    cv2.imwrite(after_img, after_final);  np.save(after_npy, after_board)
                    print(f"[SAVE] Sau khi đặt: {after_img}, {after_npy}")
                    last_board_state = after_board.copy()
                else:
                    print("[WARN] Không đọc được frame sau khi đặt.")
            except Exception as e:
                print("[ERROR] Đặt quân thất bại:", e)
                try: goto_ref(gr, vel=150.0)
                except Exception: pass
                frozen = False

    # cleanup
    try: cap.release()
    except: pass
    cv2.destroyAllWindows()
    try: gr.close()
    except: pass
    print("[CLOSE] Bye.")

if __name__ == "__main__":
    main()
