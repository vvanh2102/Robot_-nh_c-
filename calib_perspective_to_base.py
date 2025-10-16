# calib_perspective_to_base.py
import cv2, numpy as np, os

CAL_DIR = "D:/co_caro_project/calibration"
INTR = os.path.join(CAL_DIR, "intrinsics.npz")
OUT  = os.path.join(CAL_DIR, "perspective.npz")
os.makedirs(CAL_DIR, exist_ok=True)

# --- Quy ước O phải-dưới, +X trái, +Y lên ---
L = 282.0  # mm  (12 ô × 23,5mm)
base_mm = np.array([[0,0],[L,0],[0,L],[L,L]], np.float32)

pts_px = []
def on_mouse(e, x, y, *_):
    if e == cv2.EVENT_LBUTTONDOWN and len(pts_px) < 4:
        pts_px.append([x,y]); print("  +", (x,y))

cap = cv2.VideoCapture(0)
with np.load(INTR) as d:
    K, dist = d["K"], d["dist"]

print("[INFO] Click theo thứ tự: O(phải-dưới) → OX(trái-dưới) → OY(phải-trên) → đối(diagonal); ENTER để lưu.")
while True:
    ok, img = cap.read();  assert ok
    img = cv2.undistort(img, K, dist)
    disp = img.copy()
    for p in pts_px: cv2.circle(disp, tuple(p), 6, (0,255,0), -1)
    cv2.imshow("click_corners", disp)
    cv2.setMouseCallback("click_corners", on_mouse)
    k = cv2.waitKey(1) & 0xFF
    if k == 13 and len(pts_px) == 4:  # Enter
        break

cap.release(); cv2.destroyAllWindows()
pts_px = np.array(pts_px, np.float32)
H, _ = cv2.findHomography(pts_px, base_mm, method=cv2.RANSAC)
np.savez(OUT, H=H, pts_px=pts_px, base_mm=base_mm)
print("[DONE] Lưu:", OUT)
