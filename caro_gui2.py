# caro_gui.py — PyQt5 GUI cho hệ Caro tự động (YOLO + grid_actions + iRC robot)
# Đã sửa: Board State phóng to, header 0–12
# -------------------------------------------------------------------
# Phím: Connect Robot, Start/Stop Detect, Place, Go REF, Calibration, Models, Safety, Logs
# -------------------------------------------------------------------

import sys, os, time, threading
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import cv2
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QAction, QMessageBox, QToolBar, QStatusBar, QDialog,
    QFormLayout, QSpinBox, QDialogButtonBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)

# ====== Đường dẫn & model ======
BASE_DIR = Path(__file__).resolve().parent
BOARD_MODEL_PATH = BASE_DIR / "lastbc.pt"
PIECE_MODEL_PATH = BASE_DIR / "last.pt"
RUNS_DIR = BASE_DIR / "runs"
os.makedirs(RUNS_DIR, exist_ok=True)

GRID_SIZE = 13
SHRINK_FACTOR = 0.99
CONF_PIECE = 0.45

# ====== Robot ======
from grid_actions import GridRobot
REF_POSE = dict(X=214.2, Y=-6.0, Z=439.9, A=-178.1, B=0.7, C=-180.0)

def robot_goto_ref(gr, vel=150.0):
    rb = gr.rb.rb
    ok = rb.move_cartesian(
        X=REF_POSE["X"], Y=REF_POSE["Y"], Z=REF_POSE["Z"],
        A=REF_POSE["A"], B=REF_POSE["B"], C=REF_POSE["C"],
        E1=0.0, E2=0.0, E3=0.0,
        velocity=float(vel), frame="#base",
        wait_move_finished=True, move_finished_timeout=120.0
    )
    time.sleep(0.3)
    return ok

# ====== YOLO ======
try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except Exception:
    _YOLO_AVAILABLE = False

@dataclass
class BoardROI:
    x1: int; y1: int; x2: int; y2: int

@dataclass
class DetectionItem:
    row: int; col: int; cls_id: int; u: int; v: int

# ======================= Camera Thread =======================
class CameraWorker(QThread):
    newFrame = pyqtSignal(np.ndarray)
    opened = pyqtSignal(bool)
    def __init__(self, cam_index=6, parent=None):
        super().__init__(parent)
        self.cam_index = cam_index
        self._stop = threading.Event()
        self.cap = None
    def run(self):
        self.cap = cv2.VideoCapture(self.cam_index)
        ok = self.cap.isOpened()
        self.opened.emit(ok)
        if not ok: return
        while not self._stop.is_set():
            ret, frame = self.cap.read()
            if ret: self.newFrame.emit(frame)
            else: time.sleep(0.01)
        if self.cap: self.cap.release()
    def stop(self): self._stop.set()

# ======================= Detection Thread =======================
class DetectionWorker(QThread):
    result = pyqtSignal(np.ndarray, object, list)
    ready = pyqtSignal(bool, str)
    def __init__(self, conf_piece=CONF_PIECE, shrink=SHRINK_FACTOR, parent=None):
        super().__init__(parent)
        self.conf_piece = conf_piece; self.shrink = shrink
        self._stop = threading.Event(); self._lock = threading.Lock()
        self._last_frame = None; self._running = False
        self.board_model = None; self.piece_model = None
    def set_running(self, s): self._running = s
    def update_frame(self, f):
        with self._lock: self._last_frame = f
    def _ensure_models(self):
        if not _YOLO_AVAILABLE:
            self.ready.emit(False, "Ultralytics YOLO chưa cài đặt.")
            return False
        if self.board_model is None: self.board_model = YOLO(BOARD_MODEL_PATH)
        if self.piece_model is None: self.piece_model = YOLO(PIECE_MODEL_PATH)
        self.ready.emit(True, "YOLO models ready.")
        return True
    def run(self):
        if not self._ensure_models(): return
        while not self._stop.is_set():
            if not self._running:
                time.sleep(0.02); continue
            with self._lock:
                if self._last_frame is None:
                    time.sleep(0.005); continue
                frame = self._last_frame.copy()
            annotated, roi, items = self._detect_frame(frame)
            self.result.emit(annotated, roi, items)
    def stop(self): self._stop.set()
    def _find_board_roi(self, frame):
        res = self.board_model(frame, verbose=False)[0]
        if res.boxes is None or len(res.boxes)==0: return None
        bb = res.boxes.xyxy.cpu().numpy()
        x1,y1,x2,y2 = map(int, max(bb,key=lambda a:(a[2]-a[0])*(a[3]-a[1])))
        w,h=x2-x1,y2-y1; dx,dy=int(w*(1-self.shrink)/2),int(h*(1-self.shrink)/2)
        x1+=dx; y1+=dy; x2-=dx; y2-=dy
        H,W=frame.shape[:2]
        x1=max(0,min(W-1,x1));x2=max(1,min(W-1,x2))
        y1=max(0,min(H-1,y1));y2=max(1,min(H-1,y2))
        if x2-x1>40 and y2-y1>40: return BoardROI(x1,y1,x2,y2)
        return None
    def _draw_grid(self,img,roi):
        step_x=(roi.x2-roi.x1)/(GRID_SIZE-1); step_y=(roi.y2-roi.y1)/(GRID_SIZE-1)
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                u=int(round(roi.x1+c*step_x)); v=int(round(roi.y1+r*step_y))
                cv2.circle(img,(u,v),2,(0,255,0),-1)
        for c in range(GRID_SIZE):
            u=int(round(roi.x1+c*step_x))
            cv2.line(img,(u,roi.y1),(u,roi.y2),(0,0,255),1)
        for r in range(GRID_SIZE):
            v=int(round(roi.y1+r*step_y))
            cv2.line(img,(roi.x1,v),(roi.x2,v),(0,0,255),1)
    def _detect_frame(self, frame):
        annotated=frame.copy(); roi=self._find_board_roi(frame); items=[]
        if roi is None:
            cv2.putText(annotated,"No board ROI",(20,40),cv2.FONT_HERSHEY_SIMPLEX,0.9,(0,0,255),2)
            return annotated,None,items
        self._draw_grid(annotated,roi)
        cv2.rectangle(annotated,(roi.x1,roi.y1),(roi.x2,roi.y2),(255,0,0),2)
        crop=frame[roi.y1:roi.y2,roi.x1:roi.x2]
        pres=self.piece_model(crop,conf=self.conf_piece,verbose=False)[0]
        if pres.boxes is None or len(pres.boxes)==0: return annotated,roi,items
        step_x=(roi.x2-roi.x1)/(GRID_SIZE-1); step_y=(roi.y2-roi.y1)/(GRID_SIZE-1)
        xyxy=pres.boxes.xyxy.cpu().numpy(); cls=pres.boxes.cls.cpu().numpy().astype(int)
        clamp=lambda v: int(max(0,min(GRID_SIZE-1,int(round(v)))))
        for k,(bx1,by1,bx2,by2) in enumerate(xyxy):
            cx=(bx1+bx2)/2; cy=(by1+by2)/2
            u=int(roi.x1+cx); v=int(roi.y1+cy)
            col=clamp((u-roi.x1)/step_x); row=clamp((v-roi.y1)/step_y)
            val=1 if cls[k]==0 else 2
            items.append(DetectionItem(row,col,val,u,v))
            color=(0,255,0) if val==1 else (0,255,255)
            cv2.circle(annotated,(u,v),6,color,-1)
            cv2.putText(annotated,f"{row},{col}",(u+6,v-6),cv2.FONT_HERSHEY_SIMPLEX,0.55,color,1)
        return annotated,roi,items

# ======================= Dialog nhỏ =======================
class PlaceDialog(QDialog):
    def __init__(self,parent=None,prefill=None):
        super().__init__(parent)
        self.setWindowTitle("Place a piece"); self.setModal(True)
        self.row=QSpinBox();self.row.setRange(0,GRID_SIZE-1)
        self.col=QSpinBox();self.col.setRange(0,GRID_SIZE-1)
        if prefill: self.row.setValue(prefill[0]);self.col.setValue(prefill[1])
        frm=QFormLayout(); frm.addRow("Row (0-12):",self.row); frm.addRow("Col (0-12):",self.col)
        btns=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept);btns.rejected.connect(self.reject)
        lay=QVBoxLayout();lay.addLayout(frm);lay.addWidget(btns);self.setLayout(lay)
    def get_values(self): return self.row.value(),self.col.value()

# ======================= MainWindow =======================
class MainWindow(QMainWindow):
    sigFreeze=pyqtSignal(bool)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giao Dien Tu Dong")
        self.resize(1280,820)
        self.gr=None; self.robot_connected=False
        self.camThread=CameraWorker(); self.detThread=DetectionWorker()
        self.running_detect=False; self.frozen=False
        self.last_frame=None; self.prefill_cell=None
        self._build_ui(); self._connect_signals()
        self.camThread.start()
    # ---------- UI ----------
    def _build_ui(self):
        tb=QToolBar("Main"); tb.setIconSize(QSize(18,18)); self.addToolBar(tb)
        def addAct(name,slot): a=QAction(name,self);a.triggered.connect(slot);tb.addAction(a)
        addAct("Connect Robot",self.on_connect_robot)
        addAct("Start Detect",self.on_start_detect)
        addAct("Stop Detect",self.on_stop_detect)
        addAct("Place…",self.on_place)
        addAct("Go REF",self.on_go_ref)

        self.lblView=QLabel("Camera…"); self.lblView.setMinimumSize(800,600)
        self.lblView.setAlignment(Qt.AlignCenter)
        self.lblView.setStyleSheet("background:#111;color:#ccc;border:1px solid #333;")

        # ==== Board State table (phóng to + header 0–12) ====
        # ==== Board State table (phóng to, header 0–12, không cần scroll) ====
        self.tblBoard = QTableWidget(GRID_SIZE, GRID_SIZE)

        # mỗi ô to hơn
        cell_size = 50
        for r in range(GRID_SIZE):
            self.tblBoard.setRowHeight(r, cell_size)
        for c in range(GRID_SIZE):
            self.tblBoard.setColumnWidth(c, cell_size)

        # đặt header 0–12
        self.tblBoard.setHorizontalHeaderLabels([str(c) for c in range(GRID_SIZE)])
        self.tblBoard.setVerticalHeaderLabels([str(r) for r in range(GRID_SIZE)])
        self.tblBoard.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.tblBoard.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

        # tắt thanh cuộn
        self.tblBoard.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tblBoard.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # tính kích thước thật: cell + header + frame
        vh = self.tblBoard.verticalHeader().sizeHint().width()
        hh = self.tblBoard.horizontalHeader().sizeHint().height()
        fw = int(self.tblBoard.frameWidth()) * 2
        total_w = GRID_SIZE * cell_size + vh + fw + 8  # +8 dư để tránh scrollbar
        total_h = GRID_SIZE * cell_size + hh + fw + 8
        self.tblBoard.setFixedWidth(total_w)
        self.tblBoard.setFixedHeight(total_h)

        # cài đặt cơ bản
        self.tblBoard.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tblBoard.setSelectionMode(QTableWidget.SingleSelection)
        self.tblBoard.cellClicked.connect(self.on_board_cell_clicked)

        # khởi tạo bảng trắng
        self._refresh_board(np.zeros((GRID_SIZE, GRID_SIZE), np.int8))

        # Vac buttons
        self.btnVacOn=QPushButton("Vac ON"); self.btnVacOff=QPushButton("Vac OFF")
        self.btnVacOn.clicked.connect(self.on_vac_on)
        self.btnVacOff.clicked.connect(self.on_vac_off)
        self.btnVacOn.setEnabled(False); self.btnVacOff.setEnabled(False)

        sideBox=QVBoxLayout()
        sideBox.addWidget(QLabel("Board State"))
        sideBox.addWidget(self.tblBoard)
        sideBox.addSpacing(10)
        sideBox.addWidget(self.btnVacOn); sideBox.addWidget(self.btnVacOff); sideBox.addStretch(1)
        wrap=QWidget(); wrap.setLayout(sideBox)

        mainBox=QHBoxLayout()
        mainBox.addWidget(self.lblView,1)
        mainBox.addWidget(wrap,0)
        central=QWidget(); central.setLayout(mainBox)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar()); self.statusBar().showMessage("Ready.")
    # ---------- signals ----------
    def _connect_signals(self):
        self.camThread.opened.connect(self.on_cam_opened)
        self.camThread.newFrame.connect(self.on_new_frame)
        self.detThread.result.connect(self.on_det_result)
        self.sigFreeze.connect(self._apply_freeze)
    # ---------- helper ----------
    def _np2pix(self,img):
        rgb=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
        h,w,ch=rgb.shape; q=QImage(rgb.data,w,h,ch*w,QImage.Format_RGB888)
        return QPixmap.fromImage(q).scaled(self.lblView.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation)
    def _refresh_board(self,b):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                val=b[r,c]; it=QTableWidgetItem(str(val) if val>0 else "")
                it.setTextAlignment(Qt.AlignCenter)
                if val==1: it.setBackground(QColor(210,240,210))
                elif val==2: it.setBackground(QColor(240,240,180))
                else: it.setBackground(QColor(255,255,255))
                self.tblBoard.setItem(r,c,it)
    # ---------- slots ----------
    def on_cam_opened(self,ok): self.statusBar().showMessage("Camera ok." if ok else "Camera fail.")
    def on_new_frame(self,f):
        self.last_frame=f
        if self.running_detect and not self.frozen: self.detThread.update_frame(f)
        if not self.running_detect: self.lblView.setPixmap(self._np2pix(f))
    def on_det_result(self,ann,roi,items):
        b=np.zeros((GRID_SIZE,GRID_SIZE),np.int8)
        for it in items: b[it.row,it.col]=it.cls_id
        self._refresh_board(b)
        if items: self.prefill_cell=(items[-1].row,items[-1].col)
        cv2.putText(ann,"Press Place to command robot",(16,28),cv2.FONT_HERSHEY_SIMPLEX,0.7,(30,30,30),2)
        self.lblView.setPixmap(self._np2pix(ann))
    def on_connect_robot(self):
        if self.robot_connected: return
        try:
            self.gr=GridRobot(Z_TABLE=130.0)
            self.robot_connected=True
            self.btnVacOn.setEnabled(True); self.btnVacOff.setEnabled(True)
            self.statusBar().showMessage("Robot connected.")
        except Exception as e: QMessageBox.critical(self,"Robot",f"Connect fail: {e}")
    def on_start_detect(self):
        if not _YOLO_AVAILABLE:
            QMessageBox.critical(self,"YOLO","Chưa cài ultralytics."); return
        if not self.detThread.isRunning(): self.detThread.start()
        self.detThread.set_running(True); self.running_detect=True
        self.statusBar().showMessage("Detection started.")
    def on_stop_detect(self):
        self.detThread.set_running(False); self.running_detect=False
        self.statusBar().showMessage("Detection stopped.")
    def on_place(self):
        if not self.robot_connected: QMessageBox.warning(self,"Robot","Chưa kết nối."); return
        dlg=PlaceDialog(self,prefill=self.prefill_cell)
        if dlg.exec_()!=QDialog.Accepted: return
        row,col=dlg.get_values(); self.sigFreeze.emit(True)
        ts=int(time.time())
        if self.last_frame is not None:
            cv2.imwrite(os.path.join(RUNS_DIR,f"before_{ts}.jpg"),self.last_frame)
        try:
            self.gr.pick_from_reserve()
            self.gr.place_cell(row,col)
            robot_goto_ref(self.gr)
            self.statusBar().showMessage(f"Placed at ({row},{col}).")
        except Exception as e:
            QMessageBox.critical(self,"Place",f"Failed: {e}")
        self.sigFreeze.emit(False)
    def on_go_ref(self):
        if not self.robot_connected: QMessageBox.warning(self,"Robot","Chưa kết nối."); return
        try: robot_goto_ref(self.gr); self.statusBar().showMessage("Moved to REF.")
        except Exception as e: QMessageBox.critical(self,"Go REF",str(e))
    def _apply_freeze(self,f): self.frozen=f; self.detThread.set_running(self.running_detect and not f)
    def on_board_cell_clicked(self,r,c): self.prefill_cell=(r,c)
    def on_vac_on(self):
        if not self.robot_connected: QMessageBox.warning(self,"Vacuum","Chưa kết nối.");

    def on_go_ref(self):
        """Đưa robot về REF_POSE an toàn."""
        if not self.robot_connected or self.gr is None:
            QMessageBox.warning(self, "Robot", "Robot chưa kết nối.")
            return
        try:
            robot_goto_ref(self.gr, vel=150.0)
            self.statusBar().showMessage("Moved to REF.")
        except Exception as e:
            QMessageBox.critical(self, "Go REF", f"Failed: {e}")

    def _apply_freeze(self, freeze: bool):
        self.frozen = freeze
        self.detThread.set_running(self.running_detect and (not self.frozen))
        self.statusBar().showMessage("FROZEN." if freeze else "RUNNING.")

    def on_vac_on(self):
        """Bật hút chân không."""
        if not self.robot_connected or self.gr is None:
            QMessageBox.warning(self, "Vacuum", "Robot chưa kết nối.")
            return
        try:
            self.gr.rb.vacuum_on()
            self.statusBar().showMessage("VAC ON")
        except Exception as e:
            QMessageBox.critical(self, "Vacuum", f"Lỗi bật hút: {e}")

    def on_vac_off(self):
        """Tắt hút chân không."""
        if not self.robot_connected or self.gr is None:
            QMessageBox.warning(self, "Vacuum", "Robot chưa kết nối.")
            return
        try:
            self.gr.rb.vacuum_off()
            self.statusBar().showMessage("VAC OFF")
        except Exception as e:
            QMessageBox.critical(self, "Vacuum", f"Lỗi tắt hút: {e}")

    def on_calib(self):
        CalibWizardStub(self).exec_()

    def on_models(self):
        dlg = ModelsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            conf, shrink = dlg.get_params()
            self.detThread.conf_piece = float(conf)
            self.detThread.shrink = float(shrink)
            self.statusBar().showMessage(f"Updated: conf={conf:.2f}, shrink={shrink:.3f}")

    def on_safety(self):
        SafetyDialog(self, gr=self.gr).exec_()

    def on_logs(self):
        QMessageBox.information(self, "Runs folder", f"Saved images in:\n{RUNS_DIR}")

    def on_board_cell_clicked(self, r, c):
        self.prefill_cell = (r, c)
        self.statusBar().showMessage(f"Selected cell ({r},{c})")


# ======================= Entry =======================
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Caro GUI")
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
