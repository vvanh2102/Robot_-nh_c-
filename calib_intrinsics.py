# calib_intrinsics.py  (checkerboard 7x5)
import cv2, numpy as np, os

SAVE = "D:/co_caro_project/calibration/intrinsics.npz"
os.makedirs(os.path.dirname(SAVE), exist_ok=True)

pattern = (7,5)  # 7 cột x 5 hàng (số góc trong)
criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-3)

objp = np.zeros((pattern[0]*pattern[1],3), np.float32)
objp[:,:2] = np.mgrid[0:pattern[0],0:pattern[1]].T.reshape(-1,2)

objpoints, imgpoints, imgsz = [], [], None
cap = cv2.VideoCapture(0)

print("[INFO] SPACE: chụp;  Q: tính & lưu …")
while True:
    ok, img = cap.read();  assert ok
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    found, corners = cv2.findChessboardCorners(gray, pattern)
    disp = img.copy()
    if found:
        cv2.cornerSubPix(gray, corners, (11,11), (-1,-1), criteria)
        cv2.drawChessboardCorners(disp, pattern, corners, found)
    cv2.imshow("calib_intrinsics", disp)
    k = cv2.waitKey(1) & 0xFF
    if k == ord(' '):
        if found:
            objpoints.append(objp.copy())
            imgpoints.append(corners)
            imgsz = gray.shape[::-1]
            print(f"  + ảnh {len(imgpoints)} OK")
        else:
            print("  ! chưa thấy đủ góc")
    if k == ord('q'):
        break

cap.release(); cv2.destroyAllWindows()
ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, imgsz, None, None)
np.savez(SAVE, K=K, dist=dist)
print("[DONE] Lưu:", SAVE)
