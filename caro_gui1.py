"""
PyQt6 GUI Application for Automated Gomoku Game System

This application provides a graphical interface for controlling an automated
Gomoku (Caro) game system that uses YOLO object detection, robot control,
and real-time camera feed processing.

Features:
- Real-time camera feed display
- YOLO-based board and piece detection
- Robot control for piece placement
- Board state visualization
- Vacuum control for piece handling


@author Automated Gomoku System
@version 2.0 (PyQt6)
@date 2024

Example:
    python3 caro_gui1.py
"""

import sys
import os
import time
import threading
from dataclasses import dataclass
from typing import Optional, Tuple, List
import numpy as np
import cv2
os.environ['QT_QPA_PLATFORM'] = 'xcb'  
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QImage, QPixmap, QColor, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QMessageBox, QToolBar, QStatusBar, QDialog,
    QFormLayout, QSpinBox, QDialogButtonBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QCheckBox
)
from grid_actions import GridRobot, cell_to_robot_xy
from gomoku_game_state import (
    GomokuGameState,
    HUMAN_PLAYER,
    AI_PLAYER,
    EMPTY,
    STATUS_PLAYING,
    STATUS_HUMAN_WON,
    STATUS_AI_WON,
    STATUS_DRAW,
)
from gomoku_ai_strategy import GomokuAIStrategy
from move_detector import MoveDetector, MoveStatus
try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except Exception as e:
    _YOLO_AVAILABLE = False
    print(f"Ultralytics import error: {e}")

# ============================================================================
# CONSTANTS
# ============================================================================
BOARD_MODEL_PATH = "/home/ubuntu/FInal_gomoku_project_AI/Image_processing/Robot_-nh_c-/lastbc.pt"
PIECE_MODEL_PATH = "/home/ubuntu/FInal_gomoku_project_AI/Image_processing/Robot_-nh_c-/last.pt"
RUNS_DIR = "/home/ubuntu/FInal_gomoku_project_AI/Image_processing/Robot_-nh_c-/runs"
os.makedirs(RUNS_DIR, exist_ok=True)
CAMERA_INDEX : int = 6
CELL_SIZE : int = 60
GRID_SIZE = 13
SHRINK_FACTOR = 0.99
CONF_PIECE = 0.35  
DETECTION_STABILITY_FRAMES = 5

# Referece pose
REF_POSE = {
    'X': 214.2,
    'Y': -6.0,
    'Z': 439.9,
    'A': -178.1,
    'B': 0.7,
    'C': -180.0
}

@dataclass
class BoardROI:
    """
    init board roi
    """
    x1: int
    y1: int
    x2: int
    y2: int

@dataclass
class DetectionItem:
    """
    Docstring for DetectionItem
    """
    row: int
    col: int
    cls_id: int
    u: int
    v: int

def robot_goto_ref(grid_robot: GridRobot, velocity: float = 150.0) -> bool:
    """
    The robot go to ref
    """
    robot = grid_robot.rb.rb
    success = robot.move_cartesian(
        X=REF_POSE['X'],
        Y=REF_POSE['Y'],
        Z=REF_POSE['Z'],
        A=REF_POSE['A'],
        B=REF_POSE['B'],
        C=REF_POSE['C'],
        E1=0.0,
        E2=0.0,
        E3=0.0,
        velocity=float(velocity),
        frame="#base",
        wait_move_finished=True,
        move_finished_timeout=120.0
    )
    time.sleep(0.3)
    return success
# ============================================================================
# CAMERA WORKER THREAD
# ============================================================================
class CameraWorker(QThread):
    """
    Thread for CameraWorker
    """    
    newFrame = pyqtSignal(np.ndarray)
    opened = pyqtSignal(bool)
    
    def __init__(self, cam_index: int = CAMERA_INDEX, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.cam_index = cam_index
        self.__stop = threading.Event()
        self.cap: Optional[cv2.VideoCapture] = None

    def run(self) -> None:
        """
        Run the camera worker and capture frames
        """
        try:
            if not self._initialize_camera():
                return
            self._capture_loop()
        except Exception as e:
            print(f"Camera worker error: {e}")
            self.opened.emit(False)
        finally:
            self._cleanup_camera()

    def _initialize_camera(self) -> bool:
        """
        Initialize camera and emit status. 
        
        Returns True if successful.
        """
        self.cap = cv2.VideoCapture(self.cam_index)
        is_opened = self.cap.isOpened()
        self.opened.emit(is_opened)
        return is_opened

    def _capture_loop(self) -> None:
        """
        Main loop for capturing and emitting frames
        """
        while not self.__stop.is_set():
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                self._emit_frame(frame)
            else:
                time.sleep(0.01)

    def _emit_frame(self, frame: np.ndarray) -> None:
        """
        Safely emit a frame copy to listeners
        """
        try:
            frame_copy = frame.copy()
            self.newFrame.emit(frame_copy)
        except Exception as e:
            print(f"Error emitting frame: {e}")
            time.sleep(0.1)

    def _cleanup_camera(self) -> None:
        """
        Release camera resources
        """
        if self.cap is not None:
            self.cap.release()

    # def run(self) -> None:
    #     """
    #     run the camera worker and capture frames
    #     """
    #     try:
    #         self.cap = cv2.VideoCapture(self.cam_index)
    #         if self.cap is None:
    #             self.opened.emit(False)
    #             return
            
    #         is_opened = self.cap.isOpened()
    #         self.opened.emit(is_opened)
            
    #         if not is_opened:
    #             if self.cap:
    #                 self.cap.release()
    #             return
            
    #         while not self.__stop.is_set():
    #             ret, frame = self.cap.read()
    #             if ret and frame is not None:
    #                 try:
    #                     frame_copy = frame.copy()
    #                     self.newFrame.emit(frame_copy)
    #                 except Exception as e:
    #                     print(f"Error emitting frame: {e}")
    #                     time.sleep(0.1)
    #             else:
    #                 time.sleep(0.01)
    #     except Exception as e:
    #         print(f"Camera worker error: {e}")
    #         self.opened.emit(False)
    #     finally:
    #         if self.cap:
    #             self.cap.release()
    
    def stop(self) -> None:
        """
        Stop the camera worker
        """
        self.__stop.set()

# ============================================================================
# DETECTION WORKER THREAD
# ============================================================================

class DetectionWorker(QThread):
    """
    Thread for performing YOLO-based detection on camera frames
    """     
    result = pyqtSignal(np.ndarray, object, list)  # list contains DetectionItem objects
    ready = pyqtSignal(bool, str)
    
    def __init__(self,conf_piece: float = CONF_PIECE,shrink: float = SHRINK_FACTOR,parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.conf_piece = conf_piece
        self.shrink = shrink
        self.__stop = threading.Event()
        self.__lock = threading.Lock()
        self.__last_frame: Optional[np.ndarray] = None
        self.__running = False
        self.board_model: Optional[YOLO] = None
        self.piece_model: Optional[YOLO] = None
        self.__detection_history: List[List[Tuple[int, int, int]]] = [] 
        self.__max_history_len = DETECTION_STABILITY_FRAMES
    
    def set_running(self, running: bool) -> None:
        """
        set running game and clear detection history after starting detection
        """
        self.__running = running
        if running:
            self.__detection_history.clear()
    
    def update_frame(self, frame: np.ndarray) -> None:
        """
        Update the last frame with a new frame
        """
        with self.__lock:
            self.__last_frame = frame
    
    def __ensure_models(self) -> bool:
        """
        Ensure YOLO models are loaded
        """
        if not _YOLO_AVAILABLE:
            self.ready.emit(False, "Ultralytics YOLO not available.")
            return False
        
        if self.board_model is None:
            self.board_model = YOLO(BOARD_MODEL_PATH)
        
        if self.piece_model is None:
            self.piece_model = YOLO(PIECE_MODEL_PATH)
        
        self.ready.emit(True, "YOLO models ready.")
        return True
    
    def run(self) -> None:
        """
        Main detection loop
        
        Continuously processes frames when running is enabled.
        Detects board ROI and pieces, then emits results.
        """
        
        if not self.__ensure_models():
            return
        
        while not self.__stop.is_set():
            if not self.__running:
                time.sleep(0.02)
                continue
            
            with self.__lock:
                if self.__last_frame is None:
                    time.sleep(0.005)
                    continue
                frame = self.__last_frame.copy()
            
            annotated, roi, items = self.__detect_frame(frame)
            self.result.emit(annotated, roi, items)
    
    def stop(self) -> None:
        """
        Stop detection worker

        Signals the thread to stop processing.
        """
        self.__stop.set()
    
    def __find_board_roi(self, frame: np.ndarray) -> Optional[BoardROI]:
        """
        Find board region of interest

        Uses board detection model to locate the game board in the frame
        and returns the ROI coordinates with shrink factor applied.

        Example:
            roi = self.__find_board_roi(frame)
            if roi:
                print(f"Board found at ({roi.x1}, {roi.y1}) to ({roi.x2}, {roi.y2})")

        Args:
            frame: Input camera frame

        Returns:
            BoardROI if board detected, None otherwise
        """
        if self.board_model is None:
            return None
        
        result = self.board_model(frame, verbose=False)[0]
        
        if result.boxes is None or len(result.boxes) == 0:
            return None
        
        boxes = result.boxes.xyxy.cpu().numpy()
        largest_box = max(boxes, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        x1, y1, x2, y2 = map(int, largest_box)
        
        width = x2 - x1
        height = y2 - y1
        dx = int(width * (1 - self.shrink) / 2)
        dy = int(height * (1 - self.shrink) / 2)
        
        x1 += dx
        y1 += dy
        x2 -= dx
        y2 -= dy
    
        frame_height, frame_width = frame.shape[:2]
        x1 = max(0, min(frame_width - 1, x1))
        x2 = max(1, min(frame_width - 1, x2))
        y1 = max(0, min(frame_height - 1, y1))
        y2 = max(1, min(frame_height - 1, y2))
        
        if (x2 - x1 > 40) and (y2 - y1 > 40):
            return BoardROI(x1, y1, x2, y2)
        
        return None
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #+ Note to review : Bug maybe in __filter_stable_detections
    #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def __filter_stable_detections(self, current_detections: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
        """
        Filter detections to only keep stable ones across multiple frames
        
        Implements temporal filtering by tracking detections across consecutive
        frames and only returning pieces that appear consistently.
        
        
        Args:
            current_detections List of (row, col, cls_id) tuples from current frame
        
        Returns:
            List of stable detections (row, col, cls_id)
        """

        self.__detection_history.append(current_detections)
        detection_counts = {}

        if len(self.__detection_history) > self.__max_history_len:
            self.__detection_history.pop(0)
        if len(self.__detection_history) < self.__max_history_len:
            return current_detections
        
        for frame_detections in self.__detection_history:
            seen_in_frame = set()
            for row, col, cls_id in frame_detections:
                key = (row, col, cls_id)
                seen_in_frame.add(key)
            for key in seen_in_frame:
                detection_counts[key] = detection_counts.get(key, 0) + 1
        
        stable_detections = [key for key, count in detection_counts.items() if count >= self.__max_history_len]
        return stable_detections

    def __draw_grid(self, img: np.ndarray, roi: BoardROI) -> None:
        """
        Draw grid overlay on image
        
        Draws the game grid lines and intersection points on the image
        based on the board ROI and grid size.
        
        Args:
            img Image to draw on (modified in-place)
            roi Board region of interest
        """
        step_x = (roi.x2 - roi.x1) / (GRID_SIZE - 1)
        step_y = (roi.y2 - roi.y1) / (GRID_SIZE - 1)
        
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                u = int(round(roi.x1 + col * step_x))
                v = int(round(roi.y1 + row * step_y))
                cv2.circle(img, (u, v), 2, (0, 255, 0), -1)
        for col in range(GRID_SIZE):
            u = int(round(roi.x1 + col * step_x))
            cv2.line(img, (u, roi.y1), (u, roi.y2), (0, 0, 255), 1)
        for row in range(GRID_SIZE):
            v = int(round(roi.y1 + row * step_y))
            cv2.line(img, (roi.x1, v), (roi.x2, v), (0, 0, 255), 1)
    
    def __detect_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[BoardROI], List[DetectionItem]]:
        """
        Detect board and pieces in frame
        
        Main detection method that finds the board ROI, detects pieces,
        and returns annotated frame with detection results.
        
        Example:
            annotated, roi, items = self.__detect_frame(frame)
            for item in items:
            print(f"Piece at ({item.row}, {item.col})")
        
        Args:
            frame Input camera frame
        
        Returns:
            Tuple of (annotated_frame, roi, detection_items)
        """
        annotated = frame.copy()
        roi = self.__find_board_roi(frame)
        items: List[DetectionItem] = []
        
        if roi is None:
            cv2.putText(annotated,"No board ROI",(20, 40),cv2.FONT_HERSHEY_SIMPLEX,0.9,(0, 0, 255),2)
            return annotated, None, items
        
        self.__draw_grid(annotated, roi)
        cv2.rectangle(annotated, (roi.x1, roi.y1), (roi.x2, roi.y2), (255, 0, 0), 2)
        board_crop = frame[roi.y1:roi.y2, roi.x1:roi.x2]
        
        if self.piece_model is None:
            return annotated, roi, items
        
        piece_result = self.piece_model(board_crop, conf=self.conf_piece, verbose=False)[0]
        if piece_result.boxes is None or len(piece_result.boxes) == 0:
            return annotated, roi, items
        
        step_x = (roi.x2 - roi.x1) / (GRID_SIZE - 1)
        step_y = (roi.y2 - roi.y1) / (GRID_SIZE - 1)
        boxes_xyxy = piece_result.boxes.xyxy.cpu().numpy()
        classes = piece_result.boxes.cls.cpu().numpy().astype(int)

        def clamp_to_grid(value: float) -> int:
            """
            Clamp value to valid grid index range.
            """
            return int(max(0, min(GRID_SIZE - 1, int(round(value)))))

        raw_detections = [] 

        for idx, (bx1, by1, bx2, by2) in enumerate(boxes_xyxy):
            center_x = (bx1 + bx2) / 2
            center_y = (by1 + by2) / 2
            abs_u = int(roi.x1 + center_x)
            abs_v = int(roi.y1 + center_y)
            col = clamp_to_grid((abs_u - roi.x1) / step_x)
            row = clamp_to_grid((abs_v - roi.y1) / step_y)
            class_id = 1 if classes[idx] == 0 else 2
            raw_detections.append((row, col, class_id, abs_u, abs_v))
        current_frame_detections = [(r, c, cls) for r, c, cls, _, _ in raw_detections]
        stable_detections = self.__filter_stable_detections(current_frame_detections)
        stable_set = set(stable_detections)

        for row, col, class_id, abs_u, abs_v in raw_detections:
            if (row, col, class_id) in stable_set:
                items.append(DetectionItem(row, col, class_id, abs_u, abs_v))
                color = (0, 255, 0) if class_id == 1 else (0, 255, 255)
                cv2.circle(annotated, (abs_u, abs_v), 6, color, -1)
                cv2.putText(annotated,f"{row},{col}",(abs_u + 6, abs_v - 6),cv2.FONT_HERSHEY_SIMPLEX,0.55,color,1)
            else:
                cv2.circle(annotated, (abs_u, abs_v), 4, (128, 128, 128), 1)
        return annotated, roi, items

# ============================================================================
# DIALOG CLASSES
# ============================================================================

class PlaceDialog(QDialog):
    """
    Dialog for selecting piece placement position
    
    Provides a simple dialog with spin boxes for selecting row and
    column coordinates for piece placement.
    """
    
    def __init__(self, parent: Optional[QWidget] = None, prefill: Optional[Tuple[int, int]] = None):
        super().__init__(parent)
        self.setWindowTitle("Place a piece")
        self.setModal(True)
        self.row_spinbox = QSpinBox()
        self.row_spinbox.setRange(0, GRID_SIZE - 1)
        self.col_spinbox = QSpinBox()
        self.col_spinbox.setRange(0, GRID_SIZE - 1)
        
        if prefill:
            self.row_spinbox.setValue(prefill[0])
            self.col_spinbox.setValue(prefill[1])
        
        form_layout = QFormLayout()
        form_layout.addRow("Row (0-12):", self.row_spinbox)
        form_layout.addRow("Col (0-12):", self.col_spinbox)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
    
    def get_values(self) -> Tuple[int, int]:
        """
        Get selected row and column values
        
        Returns:
            Tuple of (row, col) as integers
        """
        return self.row_spinbox.value(), self.col_spinbox.value()


class VirtualGameDialog(QDialog):
    """
    Virtual Gomoku game dialog for testing AI engines
    
    Provides an interactive 2D board where a human can play against
    the currently selected AI model (minimax or AlphaZero) without
    requiring camera input or robot hardware. This is intended for
    validating AI integration in a purely virtual environment.
    """
    def __init__(self, parent: Optional[QWidget], grid_size: int, ai_mode: str, ai_depth: int):
        super().__init__(parent)
        self.setWindowTitle("Virtual Gomoku vs AI")
        self.resize(800, 800)
        self.grid_size = grid_size
        self.ai_mode = ai_mode
        self.ai_depth = ai_depth
        self.game_state = GomokuGameState(grid_size=self.grid_size)
        self.ai_strategy = GomokuAIStrategy(board_size=self.grid_size, max_depth=self.ai_depth, strategy_type="alphazero" if self.ai_mode == "alphazero" else "minimax")
        self.tbl_board = QTableWidget(self.grid_size, self.grid_size)
        for row in range(self.grid_size):
            self.tbl_board.setRowHeight(row, CELL_SIZE)
        for col in range(self.grid_size):
            self.tbl_board.setColumnWidth(col, CELL_SIZE)

        header_labels = [str(c) for c in range(self.grid_size)]
        self.tbl_board.setHorizontalHeaderLabels(header_labels)
        self.tbl_board.setVerticalHeaderLabels(header_labels)
        self.tbl_board.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_board.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tbl_board.cellClicked.connect(self.on_cell_clicked)
        self.lbl_status = QLabel("Your turn (X).")
        self.btn_restart = QPushButton("Restart")
        self.btn_restart.clicked.connect(self.on_restart)

        layout = QVBoxLayout()
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.tbl_board)
        layout.addWidget(self.btn_restart)
        self.setLayout(layout)
        self.__refresh_board()

    def __refresh_board(self) -> None:
        """
        Refresh virtual board display from game_state
        """
        board = self.game_state.get_board_state()
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                value = board[row, col]
                text = "X" if value == HUMAN_PLAYER else ("O" if value == AI_PLAYER else "")
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl_board.setItem(row, col, item)

    def on_cell_clicked(self, row: int, col: int) -> None:
        """
        Handle human click on virtual board
        """
        if self.game_state.get_game_status() != STATUS_PLAYING:
            return

        if not self.game_state.validate_move(row, col, HUMAN_PLAYER):
            self.lbl_status.setText(f"Invalid move at ({row},{col}).")
            return

        # Human move
        self.game_state.make_move(row, col, HUMAN_PLAYER)
        self.__refresh_board()
        status = self.game_state.check_win()
        if status == STATUS_HUMAN_WON:
            self.lbl_status.setText("You win!")
            return
        if status == STATUS_DRAW:
            self.lbl_status.setText("Draw.")
            return

        # AI move
        board_state = self.game_state.get_board_state()
        ai_row, ai_col = self.ai_strategy.get_best_move(board_state, player=AI_PLAYER)
        if ai_row < 0 or ai_col < 0:
            self.lbl_status.setText("AI has no valid moves (check AlphaZero setup).")
            return

        if self.game_state.validate_move(ai_row, ai_col, AI_PLAYER):
            self.game_state.make_move(ai_row, ai_col, AI_PLAYER)
        self.__refresh_board()
        status = self.game_state.check_win()
        if status == STATUS_AI_WON:
            self.lbl_status.setText("AI wins.")
        elif status == STATUS_DRAW:
            self.lbl_status.setText("Draw.")
        else:
            self.lbl_status.setText("Your turn (X).")

    def on_restart(self) -> None:
        """
        Restart virtual game
        """
        self.game_state.reset()
        self.__refresh_board()
        self.lbl_status.setText("Your turn (X).")

# ============================================================================
# MAIN WINDOW CLASS
# ============================================================================

class MainWindow(QMainWindow):
    """
    Main application window
    
    Provides the main GUI interface for the automated Gomoku system.
    Manages camera feed, detection, robot control, and board visualization.
    """
    
    sigFreeze = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Giao Dien Tu Dong")
        self.resize(1280, 820)
        self.grid_robot: Optional[GridRobot] = None
        self.robot_connected = False
        self.running_detect = False
        self.frozen = False
        self.last_frame: Optional[np.ndarray] = None
        self.prefill_cell: Optional[Tuple[int, int]] = None
        self.game_state = GomokuGameState(grid_size=GRID_SIZE)
        self.move_detector = MoveDetector(grid_size=GRID_SIZE)
        self.ai_strategy: Optional[GomokuAIStrategy] = None
        self.current_ai_depth = 1
        self.current_ai_mode = "alphazero"  
        self.auto_play_mode = True  
        self.game_active = True
        self.chk_auto_play: Optional[QCheckBox] = None
        self.cmb_ai_engine: Optional[QComboBox] = None
        self.cmb_ai_strength: Optional[QComboBox] = None
        self.btn_start_game: Optional[QPushButton] = None
        self.btn_stop_game: Optional[QPushButton] = None
        self.btn_reset_board: Optional[QPushButton] = None
        self.cam_thread = CameraWorker()
        self.det_thread = DetectionWorker()
        self.__build_ui()
        self.__connect_signals()
        self.__configure_ai_strategy(depth=self.current_ai_depth)
        self.__reset_game_state()
        QThread.msleep(100) 
        self.cam_thread.start()
    
    def __build_ui(self) -> None:
        """
        Build user interface
        
        Creates and arranges all UI components including toolbar,
        camera view, board state table, and control buttons.
        """
        toolbar = QToolBar("Main")
        toolbar.setIconSize(QSize(18, 18))
        self.addToolBar(toolbar)
        
        def add_action(name: str, slot):
            """Helper to add toolbar action."""
            action = QAction(name, self)
            action.triggered.connect(slot)
            toolbar.addAction(action)
        
        add_action("Connect Robot", self.on_connect_robot)
        add_action("Start Detect", self.on_start_detect)
        add_action("Stop Detect", self.on__stop_detect)
        add_action("Place…", self.on_place)
        add_action("Go REF", self.on_go_ref)
        add_action("Virtual Play", self.on_virtual_play)
        
        self.lbl_view = QLabel("Camera…")
        self.lbl_view.setMinimumSize(800, 600)
        self.lbl_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_view.setStyleSheet("background:#111;color:#ccc;border:1px solid #333;")
        
        self.tbl_board = self.__create_board_table()
        self.__refresh_board(np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8))
        
        self.btn_vac_on = QPushButton("Vac ON")
        self.btn_vac_off = QPushButton("Vac OFF")
        self.btn_vac_on.clicked.connect(self.on_vac_on)
        self.btn_vac_off.clicked.connect(self.on_vac_off)
        self.btn_vac_on.setEnabled(False)
        self.btn_vac_off.setEnabled(False)
        self.lbl_robot_pos = QLabel("Robot position: (N/A)")

        self.btn_start_game = QPushButton("Start Game")
        self.btn_start_game.clicked.connect(self.on_start_game)
        self.btn_stop_game = QPushButton("Stop Game")
        self.btn_stop_game.clicked.connect(self.on_stop_game)
        self.btn_reset_board = QPushButton("Reset Board")
        self.btn_reset_board.clicked.connect(self.on_reset_board)
        
        self.chk_auto_play = QCheckBox("Auto Play")
        self.chk_auto_play.setChecked(self.auto_play_mode)
        self.chk_auto_play.toggled.connect(self.on_auto_play_toggled)
        
        self.cmb_ai_engine = QComboBox()
        self.cmb_ai_engine.addItems(["Minimax (Heuristic)", "AlphaZero (Neural)",])
        self.cmb_ai_engine.currentIndexChanged.connect(self.on_ai_engine_changed)
        self.cmb_ai_strength = QComboBox()
        self.cmb_ai_strength.addItems(["Depth 1", "Depth 2", "Depth 3",])
        self.cmb_ai_strength.currentIndexChanged.connect(self.on_ai_strength_changed)

        toolbar.addSeparator()
        toolbar.addWidget(self.btn_start_game)
        toolbar.addWidget(self.btn_stop_game)
        toolbar.addWidget(self.btn_reset_board)
        toolbar.addSeparator()
        toolbar.addWidget(self.chk_auto_play)
        toolbar.addSeparator()
        toolbar.addWidget(QLabel("AI:"))
        toolbar.addWidget(self.cmb_ai_engine)
        toolbar.addWidget(QLabel("Strength:"))
        toolbar.addWidget(self.cmb_ai_strength)

        side_layout = QVBoxLayout()
        side_layout.addWidget(QLabel("Board State"))
        side_layout.addWidget(self.tbl_board)
        side_layout.addSpacing(10)
        side_layout.addWidget(self.btn_vac_on)
        side_layout.addWidget(self.btn_vac_off)
        side_layout.addWidget(self.lbl_robot_pos)
        side_layout.addStretch(1)
        
        side_widget = QWidget()
        side_widget.setLayout(side_layout)
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.lbl_view, 1)
        main_layout.addWidget(side_widget, 0)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready.")
    
    def __create_board_table(self) -> QTableWidget:
        """
        Create and configure board state table

        Creates a table widget to display the current game board state
        with proper sizing, headers, and styling. Ensures all 13x13 cells
        (0-12) are visible with proper headers.

        Returns:
            Configured QTableWidget instance
        """
        table = QTableWidget(GRID_SIZE, GRID_SIZE)

        for row in range(GRID_SIZE):
            table.setRowHeight(row, CELL_SIZE)
        for col in range(GRID_SIZE):
            table.setColumnWidth(col, CELL_SIZE)
        
        header_labels = [str(c) for c in range(GRID_SIZE)]
        table.setHorizontalHeaderLabels(header_labels)
        table.setVerticalHeaderLabels(header_labels)
        
        assert table.columnCount() == GRID_SIZE, f"Expected {GRID_SIZE} columns, got {table.columnCount()}"
        assert table.rowCount() == GRID_SIZE, f"Expected {GRID_SIZE} rows, got {table.rowCount()}"
        
        horizontal_header = table.horizontalHeader()
        horizontal_header.setMinimumSectionSize(35)
        horizontal_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        horizontal_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        horizontal_header.setDefaultSectionSize(CELL_SIZE)

        vertical_header = table.verticalHeader()  
        vertical_header.setMinimumSectionSize(35)
        vertical_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        vertical_header.setDefaultSectionSize(CELL_SIZE)

        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.updateGeometry()
        table.setFixedWidth(GRID_SIZE * CELL_SIZE + 40) 
        table.setFixedHeight(GRID_SIZE * CELL_SIZE + 30)  
        table.setShowGrid(True)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.cellClicked.connect(self.on_board_cell_clicked)
        return table
    
    def __connect_signals(self) -> None:
        """
        Connect Qt signals to slots
        
        Establishes connections between worker thread signals and
        window slot methods.
        """
        self.cam_thread.opened.connect(self.on_cam_opened)
        self.cam_thread.newFrame.connect(self.on_new_frame)
        self.det_thread.result.connect(self.on_det_result)
        self.sigFreeze.connect(self._apply_freeze)
    
    def __np2pix(self, img: np.ndarray) -> QPixmap:
        """
        Convert numpy array to QPixmap
        
        Converts an OpenCV BGR image (numpy array) to a Qt pixmap
        suitable for display, with proper color space conversion and scaling.
        
        Example:
            pixmap = self.__np2pix(cv2_frame)
            label.setPixmap(pixmap)
        
        Args:
            img Input image as numpy array (BGR format)
        
        Returns:
            QPixmap scaled to fit label size
        """
        try:
            if img is None or img.size == 0 or len(img.shape) < 2:
                return QPixmap()
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            height, width, channels = rgb.shape
            bytes_per_line = channels * width
            rgb_bytes = rgb.tobytes()
            q_image = QImage(rgb_bytes, width, height, bytes_per_line, QImage.Format.Format_RGB888)
            if q_image.isNull():
                return QPixmap()
            return QPixmap.fromImage(q_image).scaled(self.lbl_view.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        except Exception as e:
            print(f"Error converting image to pixmap: {e}")
            return QPixmap()
    
    def ___refresh_board(self, board_state: np.ndarray) -> None:
        """
        Refresh board state table display
        
        Updates the table widget to reflect the current board state
        with appropriate colors for each player.
        
        Args:
            board_state 2D numpy array with board state (0=empty, 1=player1, 2=player2)
        """
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                value = board_state[row, col]
                item = QTableWidgetItem(str(value) if value > 0 else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if value == 1:
                    item.setBackground(QColor(210, 240, 210))  # Light green
                elif value == 2:
                    item.setBackground(QColor(240, 240, 180))  # Light yellow
                else:
                    item.setBackground(QColor(255, 255, 255))  # White
                self.tbl_board.setItem(row, col, item)
    
    def _apply_freeze(self, freeze: bool) -> None:
        """
        Apply freeze state to detection
        
        Freezes or unfreezes the detection process, typically used
        during robot operations to prevent interference.
        
        Args:
            freeze True to freeze detection, False to resume
        """
        self.frozen = freeze
        self.det_thread.set_running(self.running_detect and (not self.frozen))
        status_msg = "FROZEN." if freeze else "RUNNING."
        self.statusBar().showMessage(status_msg)

    def __reset_game_state(self) -> None:
        """
        Reset internal game state trackers
        
        Clears the game state and move detector so that a new game can start
        without residual detections from prior frames.
        """
        self.game_state.reset()
        self.move_detector.reset()
        self.game_active = True
        self.statusBar().showMessage("Game state reset.")
        self.__refresh_board(np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8))

    def __configure_ai_strategy(self, depth: int, mode: str = "minimax") -> None:
        """
        Configure AI strategy with the specified engine and search depth
        """
        self.current_ai_depth = depth
        self.current_ai_mode = mode
        if mode == "alphazero":
            self.ai_strategy = GomokuAIStrategy(
                board_size=GRID_SIZE,
                max_depth=depth,
                strategy_type="alphazero",
            )
            self.statusBar().showMessage("AI strategy set to AlphaZero (Gomoku).")
        else:
            self.ai_strategy = GomokuAIStrategy(
                board_size=GRID_SIZE,
                max_depth=depth,
                strategy_type="minimax",
            )
            self.statusBar().showMessage(f"AI strategy set to Minimax depth {depth}.")

    def __handle_move_detection(self, result) -> None:
        """
        Handle move detection result
        
        Processes the outcome from MoveDetector and either validates the
        human move or logs warnings for invalid states.
        """
        if result.status == MoveStatus.NO_CHANGE:
            return
        if result.status == MoveStatus.MULTIPLE_NEW:
            self.statusBar().showMessage("Multiple new detections detected; ignoring.")
            return
        if result.status == MoveStatus.INVALID:
            self.statusBar().showMessage("Invalid detection coordinates; ignoring.")
            return
        if result.status == MoveStatus.NEW_MOVE:
            if result.cls_id != HUMAN_PLAYER:
                # Only human moves are validated in this step
                return
            self.__process_human_move(result.row, result.col)

    def __process_human_move(self, row: int, col: int) -> None:
        """
        Validate and register human move
        
        Ensures the detected move obeys turn order and board rules before
        updating the game state.
        """
        if not self.game_active:
            print(f"[HUMAN_MOVE] Game not active, ignoring move at ({row},{col})")
            return

        board_state = self.game_state.get_board_state()
        current_turn = self.game_state.get_current_turn()
        cell_value = board_state[row, col]
        
        print(f"[HUMAN_MOVE] Attempting to register move at ({row},{col})")
        print(f"[HUMAN_MOVE] Current turn: {current_turn} (HUMAN_PLAYER={HUMAN_PLAYER}, AI_PLAYER={AI_PLAYER})")
        print(f"[HUMAN_MOVE] Cell ({row},{col}) current value: {cell_value} (EMPTY={EMPTY})")
        
        if not self.game_state.validate_move(row, col, HUMAN_PLAYER):
            if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
                reason = f"Position out of bounds: ({row},{col})"
            elif cell_value != EMPTY:
                reason = f"Cell already occupied: value={cell_value}"
            elif current_turn != HUMAN_PLAYER:
                reason = f"Not human's turn: current_turn={current_turn}, expected={HUMAN_PLAYER}"
            else:
                reason = "Unknown validation failure"
            print(f"[HUMAN_MOVE] INVALID MOVE: {reason}")
            self.statusBar().showMessage(f"Invalid move detected at ({row},{col}): {reason}")
            return
        print(f"[HUMAN_MOVE] Registering move at ({row},{col}) for HUMAN_PLAYER (cls_id={HUMAN_PLAYER})")

        self.game_state.make_move(row, col, HUMAN_PLAYER)
        self.prefill_cell = (row, col)
        self.__debug_print_board_state("After HUMAN move")
        self.__debug_print_move_history()

        status = self.game_state.check_win()
        if status != STATUS_PLAYING:
            self.__handle_game_end(status)
            return

        self.statusBar().showMessage(f"Registered move ({row},{col}) for human. AI thinking...")
        if self.auto_play_mode:
            self.__ai_turn()

    def __handle_game_end(self, status: str) -> None:
        """
        Handle game end state
        
        Displays a popup dialog announcing the game result (human win, AI win,
        or draw) and offers the option to play again. Stops automatic processing
        when a game result has been reached.
        
        Args:
            status Game status string (STATUS_HUMAN_WON, STATUS_AI_WON, STATUS_DRAW)
        """
        self.game_active = False
        if status == STATUS_HUMAN_WON:
            title = "END GAME"
            message = "Player win"
        elif status == STATUS_AI_WON:
            title = "END GAME"
            message = "AI win"
        elif status == STATUS_DRAW:
            title = "END GAME"
            message = "Draw!"
        else:
            title = "END GAME"
            message = "End game"
        self.statusBar().showMessage(message)
    
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setInformativeText("Do you wanna play again?")
        btn_play_again = msg_box.addButton("Play again", QMessageBox.ButtonRole.YesRole)
        btn_no = msg_box.addButton("No", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(btn_play_again)
        result = msg_box.exec()
    
        if msg_box.clickedButton() == btn_play_again:
            self.__reset_game_state()
            self.auto_play_mode = self.chk_auto_play.isChecked() if self.chk_auto_play else True
            if not self.running_detect:
                self.on_start_detect()
            self.statusBar().showMessage("Start a new game!")
        else:
            self.statusBar().showMessage(f"{message} Stop the game.")

    def __ai_turn(self) -> None:
        """
        Execute AI turn: compute move, command robot, and update game state
        
        This method asks the AI strategy to select the best move based on
        the current board state, then optionally commands the robot to
        place the piece, and finally updates the internal game state.
        """
        if not self.game_active:
            return

        board_state = self.game_state.get_board_state()
        print(f"[AI_TURN] Computing AI move (player=AI_PLAYER, cls_id={AI_PLAYER})")
        self.__debug_print_board_state("Before AI computation")
        
        row, col = self.ai_strategy.get_best_move(board_state, player=AI_PLAYER)
        print(f"[AI_TURN] AI chose move at ({row},{col})")

        if row < 0 or col < 0:
            self.statusBar().showMessage("AI has no valid moves.")
            return

        self.sigFreeze.emit(True)
        if self.robot_connected and self.grid_robot is not None:
            try:
                self.grid_robot.pick_from_reserve()
                self.grid_robot.place_cell(row, col)
                robot_goto_ref(self.grid_robot)
                self._update_robot_position_display(row, col)
                self.statusBar().showMessage(f"AI placed at ({row},{col}).")
            except Exception as e:
                QMessageBox.critical(self, "AI Move", f"Robot failed to place piece: {e}")
        else:
            self._update_robot_position_display(row, col)
            self.statusBar().showMessage(f"AI move ({row},{col}) recorded (no robot).")

        if self.game_state.validate_move(row, col, AI_PLAYER):
            print(f"[AI_MOVE] Registering move at ({row},{col}) for AI_PLAYER (cls_id={AI_PLAYER})")
            self.game_state.make_move(row, col, AI_PLAYER)
            self.__debug_print_board_state("After AI move")
            self.__debug_print_move_history()

        status = self.game_state.check_win()
        if status != STATUS_PLAYING:
            self.__handle_game_end(status)
        self.sigFreeze.emit(False)

    def __debug_print_board_state(self, label: str = "") -> None:
        """
        Debug helper: Print current board state to console
        
        Args:
            label Optional label to prefix the output
        """
        board_state = self.game_state.get_board_state()
        print(f"\n[BOARD_STATE] {label}")
        print("   ", end="")
        for col in range(GRID_SIZE):
            print(f"{col:2d}", end=" ")
        print()
        for row in range(GRID_SIZE):
            print(f"{row:2d} ", end="")
            for col in range(GRID_SIZE):
                value = board_state[row, col]
                if value == EMPTY:
                    print(" .", end=" ")
                elif value == HUMAN_PLAYER:
                    print(" X", end=" ")  
                elif value == AI_PLAYER:
                    print(" O", end=" ")  
                else:
                    print(f"{value:2d}", end=" ")
            print()
        print(f"Current turn: {'HUMAN' if self.game_state.get_current_turn() == HUMAN_PLAYER else 'AI'}")
        print()

    def __debug_print_move_history(self) -> None:
        """
        Debug helper: Print move history to console
        
        """
        history = self.game_state.get_move_history()
        if not history:
            print("[MOVE_HISTORY] No moves yet")
            return
        print(f"[MOVE_HISTORY] Total moves: {len(history)}")
        for idx, (row, col, player) in enumerate(history, 1):
            player_name = "HUMAN" if player == HUMAN_PLAYER else "AI" if player == AI_PLAYER else f"UNKNOWN({player})"
            print(f"  Move {idx}: {player_name} at ({row},{col})")
        print()

    def _update_robot_position_display(self, row: int, col: int) -> None:
        """
        Update UI label showing last robot placement in both grid and base coordinates
        """
        try:
            x_robot, y_robot = cell_to_robot_xy(row, col)
            text = (f"Robot position: cell ({row},{col}) " 
                    f"→ base ({x_robot:.1f}, {y_robot:.1f}) mm")
        except Exception as e:
            text = f"Robot position: cell ({row},{col}) (conversion error: {e})"
        if self.lbl_robot_pos:
            self.lbl_robot_pos.setText(text)

    def on_virtual_play(self) -> None:
        """
        Open virtual Gomoku game dialog to play against current AI model
        
        This allows testing the selected AI engine (Minimax or AlphaZero)
        on a purely virtual board without requiring camera detection or
        robot hardware.
        """
        dialog = VirtualGameDialog(parent=self,grid_size=GRID_SIZE,ai_mode=self.current_ai_mode,ai_depth=self.current_ai_depth,)
        dialog.exec()

    def on_start_game(self) -> None:
        """
        Start a new game and reset state
        """
        self.__reset_game_state()
        self.auto_play_mode = self.chk_auto_play.isChecked() if self.chk_auto_play else True
        if not self.running_detect:
            self.on_start_detect()
            self.statusBar().showMessage("New game started. Detection started.")
        else:
            self.statusBar().showMessage("New game started.")

    def on__stop_game(self) -> None:
        """
        Stop the current game (no further automatic moves)
        """
        self.game_active = False
        self.statusBar().showMessage("Game stopped.")

    def on_reset_board(self) -> None:
        """
        Reset board while keeping current settings
        """
        self.__reset_game_state()

    def on_auto_play_toggled(self, checked: bool) -> None:
        """
        Toggle auto play mode
        """
        self.auto_play_mode = checked
        state = "enabled" if checked else "disabled"
        self.statusBar().showMessage(f"Auto play {state}.")

    def on_ai_engine_changed(self, index: int) -> None:
        """
        Change AI engine (Minimax vs AlphaZero)
        """
        if index == 1:
            self.__configure_ai_strategy(depth=1, mode="alphazero")
            if self.cmb_ai_strength:
                self.cmb_ai_strength.setEnabled(False)
        else:
            if self.cmb_ai_strength:
                self.cmb_ai_strength.setEnabled(True)
                depth_index = self.cmb_ai_strength.currentIndex()
            else:
                depth_index = 0
            depth_map = {0: 1, 1: 2, 2: 3}
            depth = depth_map.get(depth_index, 1)
            self.__configure_ai_strategy(depth=depth, mode="minimax")

    def on_ai_strength_changed(self, index: int) -> None:
        """
        Change Minimax depth (only when Minimax engine is active)
        """
        if self.current_ai_mode != "minimax":
            return
        depth_map = {0: 1, 1: 2, 2: 3}
        depth = depth_map.get(index, 1)
        self.__configure_ai_strategy(depth=depth, mode="minimax")
    
    def on_cam_opened(self, success: bool) -> None:
        """
        Handle camera opened signal
        
        Args:
            success True if camera opened successfully
        """
        message = "Camera ok." if success else "Camera fail."
        self.statusBar().showMessage(message)
    
    def on_new_frame(self, frame: np.ndarray) -> None:
        """
        Handle new camera frame
        
        Processes new frames from camera. If detection is running,
        updates detection worker. Otherwise, displays frame directly.
        
        Args:
            frame New camera frame
        """
        self.last_frame = frame
        
        if self.running_detect and not self.frozen:
            self.det_thread.update_frame(frame)
        
        if not self.running_detect:
            self.lbl_view.setPixmap(self.__np2pix(frame))
    
    def on_det_result(self, annotated: np.ndarray, roi: Optional[BoardROI], items: List[DetectionItem]) -> None:
        """
        Handle detection result
        
        Updates board state display and shows annotated frame with
        detection results.
        
        Args:
            annotated Annotated frame with detections drawn
            roi Board region of interest (may be None)
            items List of detected pieces
        """
        detection_board = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int8)
        for item in items:
            detection_board[item.row, item.col] = item.cls_id
        
        if items:
            debug_msg = f"[DETECTION] Found {len(items)} pieces: "
            for item in items:
                player_name = "HUMAN" if item.cls_id == HUMAN_PLAYER else "AI" if item.cls_id == AI_PLAYER else "UNKNOWN"
                debug_msg += f"({item.row},{item.col})={item.cls_id}({player_name}) "
            print(debug_msg)
        
        game_board_state = self.game_state.get_board_state()
        self.__refresh_board(game_board_state)
        if items:
            last_item = items[-1]
            self.prefill_cell = (last_item.row, last_item.col)

        cv2.putText(annotated,"Press Place to command robot",(16, 28),cv2.FONT_HERSHEY_SIMPLEX,0.7,(30, 30, 30),2)
        self.lbl_view.setPixmap(self.__np2pix(annotated))
        if self.auto_play_mode and self.game_active:
            move_result = self.move_detector.detect_new_move(items)
            self.__handle_move_detection(move_result)
    
    def on_connect_robot(self) -> None:
        """
        Connect to robot
        
        Initializes connection to the robot and enables vacuum controls.
        """
        if self.robot_connected:
            return
        
        try:
            self.grid_robot = GridRobot(Z_TABLE=130.0)
            self.robot_connected = True
            self.btn_vac_on.setEnabled(True)
            self.btn_vac_off.setEnabled(True)
            self.statusBar().showMessage("Robot connected.")
        except Exception as e:
            QMessageBox.critical(self, "Robot", f"Connect fail: {e}")
    
    def on_start_detect(self) -> None:
        """
        Start detection process
        
        Starts the YOLO-based detection worker thread.
        """
        if not _YOLO_AVAILABLE:
            QMessageBox.critical(self, "YOLO", "Chưa cài ultralytics.")
            return
        
        if not self.det_thread.isRunning():
            self.det_thread.start()
        
        self.det_thread.set_running(True)
        self.running_detect = True
        self.statusBar().showMessage("Detection started.")
    
    def on__stop_detect(self) -> None:
        """
        Stop detection process
        
        Stops the detection worker thread.
        """
        self.det_thread.set_running(False)
        self.running_detect = False
        self.statusBar().showMessage("Detection stopped.")
    
    def on_place(self) -> None:
        """
        Place piece at selected position
        
        Opens dialog to select placement position, then commands robot
        to pick and place a piece at that location.
        """
        if not self.robot_connected:
            QMessageBox.warning(self, "Robot", "Not connect.")
            return
        
        dialog = PlaceDialog(self, prefill=self.prefill_cell)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        row, col = dialog.get_values()
        self.sigFreeze.emit(True)
        
        timestamp = int(time.time())
        if self.last_frame is not None:
            frame_path = os.path.join(RUNS_DIR, f"before_{timestamp}.jpg")
            cv2.imwrite(frame_path, self.last_frame)

        try:
            self.grid_robot.pick_from_reserve()
            self.grid_robot.place_cell(row, col)
            robot_goto_ref(self.grid_robot)
            self._update_robot_position_display(row, col)
            self.statusBar().showMessage(f"Placed at ({row},{col}).")
        except Exception as e:
            QMessageBox.critical(self, "Place", f"Failed: {e}")
        finally:
            self.sigFreeze.emit(False)
    
    def on_go_ref(self) -> None:
        """
        Move robot to reference position
        
        Commands robot to move to the safe reference position.
        """
        if not self.robot_connected or self.grid_robot is None:
            QMessageBox.warning(self, "Robot", "Robot is.disabled")
            return
        
        try:
            robot_goto_ref(self.grid_robot, velocity=150.0)
            self.statusBar().showMessage("Moved to REF.")
        except Exception as e:
            QMessageBox.critical(self, "Go REF", f"Failed: {e}")

    def on_vac_on(self) -> None:
        """
        Turn vacuum on
        
        Activates the vacuum system for piece handling.
        """
        if not self.robot_connected or self.grid_robot is None:
            QMessageBox.warning(self, "Vacuum", "Robot is.disabled")
            return
        try:
            self.grid_robot.rb.vacuum_on()
            self.statusBar().showMessage("VAC ON")
        except Exception as e:
            QMessageBox.critical(self, "Vacuum", f"Lỗi bật hút: {e}")

    def on_vac_off(self) -> None:
        """
        Turn vacuum off
        
        Deactivates the vacuum system.
        """
        if not self.robot_connected or self.grid_robot is None:
            QMessageBox.warning(self, "Vacuum", "Robot chưa kết nối.")
            return
        try:
            self.grid_robot.rb.vacuum_off()
            self.statusBar().showMessage("VAC OFF")
        except Exception as e:
            QMessageBox.critical(self, "Vacuum", f"Lỗi tắt hút: {e}")

    def on_board_cell_clicked(self, row: int, col: int) -> None:
        """
        Handle board cell click
        
        Updates prefill cell when user clicks on board table.
        
        Args:
            row Clicked row index
            col Clicked column index
        """
        self.prefill_cell = (row, col)
        self.statusBar().showMessage(f"Selected cell ({row},{col})")
    
    def on_calib(self) -> None:
        """
        Open calibration dialog
        
        Opens calibration wizard (stub - requires CalibWizardStub implementation).
        """
        # CalibWizardStub(self).exec()  # Uncomment when implemented
        QMessageBox.information(self, "Calibration", "Calibration feature not yet implemented.")
    
    def on_models(self) -> None:
        """
        Open model settings dialog
        
        Opens dialog to configure YOLO model parameters (stub - requires ModelsDialog implementation).
        """
        # ModelsDialog(self).exec()  # Uncomment when implemented
        QMessageBox.information(self, "Models", "Model settings feature not yet implemented.")
    
    def on_safety(self) -> None:
        """
        Open safety dialog
        
        Opens safety settings dialog (stub - requires SafetyDialog implementation).
        """
        # SafetyDialog(self, gr=self.grid_robot).exec()  # Uncomment when implemented
        QMessageBox.information(self, "Safety", "Safety settings feature not yet implemented.")
    
    def on_logs(self) -> None:
        """
        Show logs directory
        
        Displays the path to the runs directory where captured images are stored.
        """
        QMessageBox.information(
            self,
            "Runs folder",
            f"Saved images in:\n{RUNS_DIR}"
        )

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main() -> None:
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Caro GUI")
        
        window = MainWindow()
        window.show()
        
        exit_code = app.exec()
        
        # Cleanup threads
        if hasattr(window, 'cam_thread'):
            window.cam_thread.stop()
            window.cam_thread.wait(1000)
        if hasattr(window, 'det_thread'):
            window.det_thread.stop()
            window.det_thread.wait(1000)
        
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()