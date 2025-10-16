# ============================================================
#  recalib_H_auto.py  — về ref pose -> chụp -> YOLO (A4) -> lọc lưới -> H
#  Giữ cấu trúc bản đầu tiên, chỉ thay tọa độ ref + thêm refine lưới.
# ============================================================
import cv2, numpy as np, time, os
from ultralytics import YOLO
from cri_lib import CRIController

# ===== ĐƯỜNG DẪN =====
MODEL_PATH = "D:/doancaro/modelbc1/last.pt"                # YOLO phát hiện "bàn" (giấy A4)
SAVE_PATH  = "D:/doancaro/calibration/perspective.npz"     # nơi lưu H
BOARD_SIZE_MM = 282.0                                      # 12 ô x 23.5mm

# ===== REF POSE (bạn xác nhận) =====
REF_POSE = dict(X=214.2, Y=-6, Z=439.9, A=-179.7, B=0.7, C=-180)

# ====== Tùy chọn ======
SHRINK_FACTOR = 0.98     # co bớt bbox YOLO trước khi lọc lưới
SHOW_DEBUG    = True     # hiện các cửa sổ kiểm tra

# ---------- util: tìm hình chữ nhật "lưới trong" bằng Hough ----------
def find_inner_grid_rect(roi_bgr):
    """
    Trả về (gx1, gy1, gx2, gy2) trong toạ độ ROI (pixel) là biên lưới trong cùng.
    Nếu thất bại -> None.
    """
    h, w = roi_bgr.shape[:2]
    gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3,3), 0)

    # nhấn mạnh biên
    edges = cv2.Canny(gray, 60, 180)
    # Hough line
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80,
                            minLineLength=min(w,h)//4, maxLineGap=40)

    if SHOW_DEBUG:
        dbg = roi_bgr.copy()
        if lines is not None:
            for l in lines[:,0,:]:
                x1,y1,x2,y2 = l
                cv2.line(dbg, (x1,y1), (x2,y2), (0,255,255), 1)
        cv2.imshow("ROI edges/Hough", dbg)
        cv2.waitKey(1)

    if lines is None or len(lines) < 6:
        return None

    vx, vy = [], []
    for x1,y1,x2,y2 in lines[:,0,:]:
        dx, dy = x2 - x1, y2 - y1
        if abs(dx) < abs(dy)*0.3:        # gần như dọc
            vx += [x1, x2]
        elif abs(dy) < abs(dx)*0.3:      # gần như ngang
            vy += [y1, y2]

    if len(vx) < 4 or len(vy) < 4:
        return None

    # lấy biên trong cùng theo percentile để tránh outlier
    x_min = np.clip(int(np.percentile(vx, 5)),  0, w-1)
    x_max = np.clip(int(np.percentile(vx, 95)), 0, w-1)
    y_min = np.clip(int(np.percentile(vy, 5)),  0, h-1)
    y_max = np.clip(int(np.percentile(vy, 95)), 0, h-1)

    # nới nhẹ 1–2 px
    pad = 2
    x_min = max(0, x_min - pad); y_min = max(0, y_min - pad)
    x_max = min(w-1, x_max + pad); y_max = min(h-1, y_max + pad)

    # phải là hình có diện tích đáng kể
    if (x_max - x_min) < w*0.4 or (y_max - y_min) < h*0.4:
        return None
    return (x_min, y_min, x_max, y_max)

# ---------- robot về ref pose (bản đơn giản như bản đầu) ----------
def move_to_ref(robot):
    print(f"[MOVE] Về ref pose: {REF_POSE}")
    ok = robot.move_cartesian(
        X=REF_POSE["X"], Y=REF_POSE["Y"], Z=REF_POSE["Z"],
        A=REF_POSE["A"], B=REF_POSE["B"], C=REF_POSE["C"],
        E1=0.0, E2=0.0, E3=0.0,
        velocity=100, frame="#base", wait_move_finished=True
    )
    time.sleep(0.4)
    return ok

# ---------- pipeline recalib ----------
def recalib_H():
    board_model = YOLO(MODEL_PATH)

    # 1) Kết nối robot & về ref
    rb = CRIController()
    assert rb.connect("192.168.3.11", 3920), "Không kết nối được robot!"
    rb.set_active_control(True); rb.enable(); rb.set_override(40.0)
    try:
        from cri_lib.cri_controller import MotionType
        rb.set_motion_type(MotionType.CartBase)
    except Exception:
        pass
    move_to_ref(rb)

    # 2) Chụp 1 ảnh
    cap = cv2.VideoCapture(0); time.sleep(0.4)
    ok, frame = cap.read(); cap.release()
    if not ok:
        print("[ERROR] Không đọc được ảnh từ camera.")
        rb.disable(); rb.close(); return
    if SHOW_DEBUG:
        cv2.imshow("Captured @Ref", frame); cv2.waitKey(1)

    # 3) YOLO tìm "giấy A4"
    res = board_model(frame, verbose=False)[0]
    if res.boxes is None or len(res.boxes)==0:
        print("[ERROR] Không phát hiện được bàn/giấy.")
        rb.disable(); rb.close(); return
    x1,y1,x2,y2 = map(int, max(res.boxes.xyxy.cpu().numpy(),
                               key=lambda a:(a[2]-a[0])*(a[3]-a[1])))

    # co bớt bbox để loại mép giấy
    w,h = x2-x1, y2-y1
    dx,dy = int(w*(1-SHRINK_FACTOR)/2), int(h*(1-SHRINK_FACTOR)/2)
    x1+=dx; y1+=dy; x2-=dx; y2-=dy

    roi = frame[y1:y2, x1:x2].copy()

    # 4) Lọc Hough để lấy "lưới trong"
    inner = find_inner_grid_rect(roi)
    if inner is None:
        print("[WARN] Không tách được lưới bằng Hough — dùng bbox đã co.")
        gx1,gy1,gx2,gy2 = 0,0,roi.shape[1]-1, roi.shape[0]-1
    else:
        gx1,gy1,gx2,gy2 = inner

    # 5) 4 góc pixel của LƯỚI (toạ độ ảnh gốc)
    tl = (x1 + gx1, y1 + gy1)
    tr = (x1 + gx2, y1 + gy1)
    bl = (x1 + gx1, y1 + gy2)
    br = (x1 + gx2, y1 + gy2)

    if SHOW_DEBUG:
        dbg = frame.copy()
        cv2.rectangle(dbg, (x1,y1),(x2,y2),(300,0,0),2)             # bbox YOLO (đã co)
        cv2.rectangle(dbg, tl, br, (0,300,0), 2)                    # lưới trong
        cv2.imshow("Board Detected", dbg); cv2.waitKey(300)

    # 6) Homography pixel->mm (giữ gốc O ở PHẢI-DƯỚI, +X trái, +Y lên)
    pts_px = np.array([tl, tr, bl, br], np.float32)
    L = float(BOARD_SIZE_MM)
    pts_mm = np.array([[L,L], [0,L], [L,0], [0,0]], np.float32)  # mapping theo quy ước
    H, _ = cv2.findHomography(pts_px, pts_mm)
    if H is None:
        print("[ERROR] Không tính được H.")
        rb.disable(); rb.close(); return

    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    np.savez(SAVE_PATH, H=H)
    print(f"[DONE] Lưu H tại: {SAVE_PATH}\nH=\n{H}")

    rb.disable(); rb.close()
    if SHOW_DEBUG:
        cv2.destroyAllWindows()
    return H

if __name__ == "__main__":
    H = recalib_H()
    print("[OK] perspective.npz đã cập nhật." if H is not None else "[FAIL] Recalib không thành công.")
