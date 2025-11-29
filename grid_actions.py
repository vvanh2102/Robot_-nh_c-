#+ Grid Actions API - Coordinate Transformation Module
#+
#+ This module provides coordinate transformation functions and robot control
#+ interface for a 13x13 grid game board. It handles conversion between grid
#+ coordinates (row, col) and robot base coordinates (X, Y) using calibration
#+ matrix transformation.
#+
#+ Features:
#+   - Grid to board coordinate conversion
#+   - Board to robot base coordinate transformation
#+   - Robot control interface for picking and placing pieces
#+   - Configurable axis flipping and swapping
#+
#+ @code
#+ from grid_actions import GridRobot
#+ robot = GridRobot(Z_TABLE=128.0)
#+ robot.place_cell(6, 6)  # Place piece at center
#+ @endcode
#+
#+ @author Automated Gomoku System
#+ @version 2.0
#+ @date 2024

# ============================================================================
# IMPORTS
# ============================================================================

import os
from typing import Tuple, Optional
import numpy as np
from robot_client import RobotClient

# ============================================================================
# CONSTANTS
# ============================================================================

# Grid configuration
CELL_MM: float = 23.5  # Cell size in millimeters
GRID_SIZE: int = 13    # Grid dimensions (13x13)
BOARD_LENGTH_MM: float = (GRID_SIZE - 1) * CELL_MM  # Total board length: 282 mm
# Offset to align with grid intersections (center of each cell)
CENTER_OFFSET_MM: float = CELL_MM / 2.0

# Coordinate transformation flags
# Enable if your board system has axis inversion when converting row/col
AXIS_SWAP: bool = True   # True: swap row<->col in grid_to_board_mm()
FLIP_ROW: bool = True    # Flip row: r -> (GRID_SIZE - 1) - r
FLIP_COL: bool = True    # Flip column: c -> (GRID_SIZE - 1) - c

# Calibration file path
CALIBRATION_FILE_PATH = (
    "/home/ubuntu/FInal_gomoku_project_AI/Image_processing/Robot_-nh_c-/calibration/board2base.npz"
)

# ============================================================================
# CALIBRATION MATRIX LOADING
# ============================================================================

#+ Load calibration transformation matrix
#+
#+ Loads the transformation matrix from calibration file that maps board
#+ coordinates to robot base coordinates. The matrix is obtained by teaching
#+ 3 points on the board.
#+
#+ @raise FileNotFoundError If calibration file does not exist
if not os.path.exists(CALIBRATION_FILE_PATH):
    raise FileNotFoundError(
        f"Calibration file not found: {CALIBRATION_FILE_PATH}\n"
        "Please run calibrate_board_to_robot.py to generate the calibration file."
    )

TRANSFORMATION_MATRIX: np.ndarray = np.load(CALIBRATION_FILE_PATH)["T"]

# ============================================================================
# COORDINATE TRANSFORMATION FUNCTIONS
# ============================================================================

def grid_to_board_mm(row: int, col: int) -> Tuple[float, float]:
    #+ Convert grid coordinates to board coordinates in millimeters
    #+
    #+ Converts grid cell coordinates (row, col) to board coordinate system
    #+ (x_b, y_b) in millimeters. Applies axis flipping and swapping based
    #+ on configuration flags.
    #+
    #+ Coordinate system convention:
    #+   - Origin (0,0) at BOTTOM-RIGHT
    #+   - +X axis points LEFT (col increases)
    #+   - +Y axis points UP (row increases)
    #+
    #+ @code
    #+ xb, yb = grid_to_board_mm(6, 6)  # Center cell
    #+ print(f"Board coordinates: ({xb}, {yb}) mm")
    #+ @endcode
    #+
    #+ @param row Grid row index (0-based, 0-12)
    #+ @param col Grid column index (0-based, 0-12)
    #+
    #+ @return Tuple of (x_b, y_b) board coordinates in millimeters
    # Normalize coordinates according to flags
    normalized_row = int(row)
    normalized_col = int(col)
    
    # Apply row flipping if enabled
    if FLIP_ROW:
        normalized_row = (GRID_SIZE - 1) - normalized_row
    
    # Apply column flipping if enabled
    if FLIP_COL:
        normalized_col = (GRID_SIZE - 1) - normalized_col
    
    # Apply axis swap if enabled
    if AXIS_SWAP:
        normalized_row, normalized_col = normalized_col, normalized_row
    
    # Calculate board coordinates in millimeters (centered on intersections)
    x_board = normalized_col * CELL_MM
    y_board = normalized_row * CELL_MM
    
    return float(x_board), float(y_board)

def board_to_robot_xy(x_board: float, y_board: float) -> Tuple[float, float]:
    #+ Convert board coordinates to robot base coordinates
    #+
    #+ Transforms board coordinate system (x_b, y_b) to robot base coordinate
    #+ system (X_r, Y_r) using the calibration transformation matrix.
    #+
    #+ @code
    #+ xr, yr = board_to_robot_xy(141.0, 141.0)  # Center of board
    #+ print(f"Robot coordinates: ({xr}, {yr}) mm")
    #+ @endcode
    #+
    #+ @param x_board X coordinate in board system (millimeters)
    #+ @param y_board Y coordinate in board system (millimeters)
    #+
    #+ @return Tuple of (X_r, Y_r) robot base coordinates in millimeters
    # Create homogeneous coordinate vector
    board_point = np.array([x_board, y_board, 1.0], dtype=float)
    
    # Apply transformation matrix
    robot_point = TRANSFORMATION_MATRIX @ board_point
    
    # Extract X and Y coordinates (ignore Z if present)
    x_robot = float(robot_point[0])
    y_robot = float(robot_point[1])
    
    return x_robot, y_robot

def cell_to_robot_xy(row: int, col: int) -> Tuple[float, float]:
    #+ Convert grid cell coordinates directly to robot base coordinates
    #+
    #+ Convenience function that combines grid_to_board_mm() and
    #+ board_to_robot_xy() to directly convert from grid cell to robot
    #+ base coordinates.
    #+
    #+ @code
    #+ xr, yr = cell_to_robot_xy(0, 0)  # Bottom-right corner
    #+ robot.move_to(xr, yr)
    #+ @endcode
    #+
    #+ @param row Grid row index (0-based, 0-12)
    #+ @param col Grid column index (0-based, 0-12)
    #+
    #+ @return Tuple of (X_r, Y_r) robot base coordinates in millimeters
    x_board, y_board = grid_to_board_mm(row, col)
    return board_to_robot_xy(x_board, y_board)

# ============================================================================
# ROBOT CONTROL CLASS
# ============================================================================

class GridRobot:
    #+ Robot control interface for grid-based operations
    #+
    #+ Provides high-level interface for controlling robot movements on a
    #+ 13x13 grid game board. Handles coordinate transformation and robot
    #+ control operations like picking and placing pieces.
    #+
    #+ @code
    #+ robot = GridRobot(Z_TABLE=128.0)
    #+ robot.pick_from_reserve()
    #+ robot.place_cell(6, 6)
    #+ robot.close()
    #+ @endcode
    
    def __init__(self, Z_TABLE: float = 128.0) -> None:
        #+ Initialize grid robot controller
        #+
        #+ Creates a robot client instance with specified table height.
        #+ The robot client handles low-level robot communication and control.
        #+
        #+ @param Z_TABLE Table height in millimeters (default: 128.0)
        self.robot_client = RobotClient(
            Z_TABLE=Z_TABLE,
            approach_up=30.0,
            touch=1.5
        )
    
    def pick_cell(self, row: int, col: int) -> None:
        #+ Pick a piece from specified grid cell
        #+
        #+ Moves robot to the specified cell position and picks up a piece
        #+ from that location. The robot will approach from above, pick the
        #+ piece, and retract.
        #+
        #+ @code
        #+ robot.pick_cell(6, 6)  # Pick piece from center
        #+ @endcode
        #+
        #+ @param row Grid row index (0-based, 0-12)
        #+ @param col Grid column index (0-based, 0-12)
        x_robot, y_robot = cell_to_robot_xy(row, col)
        print(f"[PICK_CELL] Grid({row},{col}) -> Robot Base({x_robot:.1f},{y_robot:.1f})")
        self.robot_client.pick_at(x_robot, y_robot)
    
    def place_cell(self, row: int, col: int) -> None:
        #+ Place a piece at specified grid cell
        #+
        #+ Moves robot to the specified cell position and places a piece
        #+ at that location. The robot will approach from above, place the
        #+ piece, and retract.
        #+
        #+ Vacuum Flow:
        #+   - Giả định vacuum đã ON (từ pick_from_reserve trước đó)
        #+   - Chạm xuống vị trí đặt quân
        #+   - Tắt vacuum OFF để thả quân
        #+   - Chờ delay để quân cờ thả ra hoàn toàn
        #+   - Nhấc lên (vacuum đã OFF, quân cờ đã được đặt)
        #+
        #+ @code
        #+ robot.pick_from_reserve()  # Vacuum ON
        #+ robot.place_cell(6, 6)     # Vacuum OFF - đặt quân
        #+ @endcode
        #+
        #+ @param row Grid row index (0-based, 0-12)
        #+ @param col Grid column index (0-based, 0-12)
        x_robot, y_robot = cell_to_robot_xy(row, col)
        print(f"[PLACE_CELL] Grid({row},{col}) -> Robot Base({x_robot:.1f},{y_robot:.1f})")
        self.robot_client.place_at(x_robot, y_robot)
    
    def pick_from_reserve(self) -> None:
        #+ Pick a piece from reserve area
        #+
        #+ Moves robot to the reserve area and picks up a piece from there.
        #+ This is typically used before placing a piece on the board.
        #+
        #+ Vacuum Flow:
        #+   - Bật vacuum ON khi hút quân từ khay
        #+   - Vacuum vẫn ON sau khi nhấc lên (quân cờ được giữ)
        #+   - Bước tiếp theo nên gọi place_cell() để tắt vacuum và đặt quân
        #+
        #+ @code
        #+ robot.pick_from_reserve()  # Vacuum ON - hút quân từ khay
        #+ robot.place_cell(6, 6)     # Vacuum OFF - đặt quân xuống bàn
        #+ @endcode
        self.robot_client.pick_from_reserve()
    
    def close(self) -> None:
        #+ Close robot connection and cleanup resources
        #+
        #+ Properly closes the connection to the robot and releases any
        #+ resources. Should be called when done using the robot.
        #+
        #+ @code
        #+ robot.close()  # Cleanup
        #+ @endcode
        self.robot_client.close()
    
    @property
    def rb(self) -> RobotClient:
        #+ Get robot client instance
        #+
        #+ Provides access to the underlying robot client for advanced
        #+ operations that are not covered by high-level methods.
        #+
        #+ @return RobotClient instance
        return self.robot_client

# ============================================================================
# TEST/DEBUG FUNCTIONS
# ============================================================================

def test_coordinate_mapping() -> None:
    #+ Test coordinate transformation for key grid positions
    #+
    #+ Tests the coordinate transformation by checking mapping for
    #+ four corners and center of the grid. Useful for debugging
    #+ calibration and transformation issues.
    #+
    #+ @code
    #+ test_coordinate_mapping()
    #+ @endcode
    print("Testing coordinate mapping (4 corners & center):")
    test_positions = [
        (0, 0),    # Bottom-right
        (0, 12),   # Bottom-left
        (12, 0),   # Top-right
        (12, 12),  # Top-left
        (6, 6)     # Center
    ]
    
    for row, col in test_positions:
        x_robot, y_robot = cell_to_robot_xy(row, col)
        print(f"  Grid({row:02d},{col:02d}) -> Robot Base({x_robot:.1f},{y_robot:.1f})")

# # ============================================================================
# # MAIN ENTRY POINT
# # ============================================================================

# if __name__ == "__main__":
#     #+ Run coordinate mapping test when executed directly
#     test_coordinate_mapping()
