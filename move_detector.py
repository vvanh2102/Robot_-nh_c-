#+ Move Detector Module
#+
#+ This module tracks consecutive detection frames (lists of DetectionItem-like
#+ objects) and identifies the newly placed piece between frames. It is meant
#+ to run on top of the YOLO detection worker output before passing data into
#+ the game state manager.
#+
#+ Features:
#+   - Convert detection lists to coordinate maps
#+   - Detect new piece (row/col/class) while ignoring existing ones
#+   - Handle multiple new pieces, removals, or no change
#+   - Provide status information for downstream logic
#+
#+ @code
#+ detector = MoveDetector(grid_size=13)
#+ move = detector.detect_new_move(detection_items)
#+ if move and move.status == MoveStatus.NEW_MOVE:
#+     row, col, cls = move.row, move.col, move.cls_id
#+ @endcode
#+
#+ @author Automated Gomoku System
#+ @version 1.0
#+ @date 2024

# ============================================================================
# IMPORTS
# ============================================================================

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class DetectionRecord:
    #+ Lightweight detection record
    row: int
    col: int
    cls_id: int

@dataclass
class MoveDetectionResult:
    #+ Result returned by MoveDetector
    status: 'MoveStatus'
    row: Optional[int] = None
    col: Optional[int] = None
    cls_id: Optional[int] = None

class MoveStatus(Enum):
    #+ Possible detection statuses
    NO_CHANGE = auto()
    NEW_MOVE = auto()
    MULTIPLE_NEW = auto()
    INVALID = auto()

# ============================================================================
# MOVE DETECTOR CLASS
# ============================================================================

class MoveDetector:
    #+ Detects new moves between consecutive detection frames

    def __init__(self, grid_size: int = 13) -> None:
        self.grid_size = grid_size
        self._last_map: Dict[Tuple[int, int], int] = {}

    def reset(self) -> None:
        #+ Clear detection history
        #+
        #+ Clears _last_map so that the next frame will treat all pieces as "new".
        #+ This is called when starting a new game.
        print(f"[MOVE_DETECTOR] RESET: Clearing last_map (had {len(self._last_map)} pieces)")
        self._last_map.clear()
    
    def sync_with_board_state(self, board_state) -> None:
        #+ Synchronize detector with current board state
        #+
        #+ Syncs _last_map with the current board_state to avoid mistaking old pieces
        #+ as new pieces when starting a game where the board already has pieces.
        #+
        #+ @param board_state Numpy array with board state (0=empty, 1=human, 2=AI)
        import numpy as np
        self._last_map.clear()
        if board_state is None:
            return
        
        for row in range(board_state.shape[0]):
            for col in range(board_state.shape[1]):
                value = int(board_state[row, col])
                if value > 0:  # Piece exists
                    self._last_map[(row, col)] = value
        
        print(f"[MOVE_DETECTOR] SYNC: Synced with board state ({len(self._last_map)} pieces)")

    def detect_new_move(self, detection_items: List) -> MoveDetectionResult:
        #+ Compare current detections with previous and find new move
        #+
        #+ Flow:
        #+   1. Build current_map from current detection_items
        #+   2. Compare with _last_map (previous frame) to find new pieces
        #+   3. Update _last_map = current_map for the next frame
        #+
        #+ Note: _last_map is stored in RAM (instance variable).
        #+       Each call to detect_new_move() compares with the previous frame.
        current_map, invalid_found = self._build_map(detection_items)
        
        # Debug: Log current and last map for tracing
        print(f"[MOVE_DETECTOR] Current frame: {len(current_map)} pieces, Last frame: {len(self._last_map)} pieces")
        if current_map:
            print(f"[MOVE_DETECTOR] Current pieces: {list(current_map.keys())}")
        if self._last_map:
            print(f"[MOVE_DETECTOR] Last pieces: {list(self._last_map.keys())}")
        
        if invalid_found:
            print(f"[MOVE_DETECTOR] INVALID: Found invalid coordinates in detection")
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.INVALID)
        
        # Find new positions (exist in current_map but NOT in _last_map)
        new_positions = [coord for coord in current_map if coord not in self._last_map]
        print(f"[MOVE_DETECTOR] New positions found: {new_positions}")

        if len(new_positions) == 0:
            # No change: all pieces already existed in previous frame
            print(f"[MOVE_DETECTOR] NO_CHANGE: No new pieces detected")
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.NO_CHANGE)

        if len(new_positions) > 1:
            # More than 1 new piece → possibly due to unstable YOLO detection
            print(f"[MOVE_DETECTOR] MULTIPLE_NEW: Found {len(new_positions)} new pieces: {new_positions}")
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.MULTIPLE_NEW)

        # Exactly 1 new piece → this is a valid move
        (row, col) = new_positions[0]
        cls_id = current_map[(row, col)]
        print(f"[MOVE_DETECTOR] NEW_MOVE candidate: ({row},{col}) cls_id={cls_id}")
        
        # Validate coordinates
        if not self._is_valid_coord(row, col) or cls_id <= 0:
            print(f"[MOVE_DETECTOR] INVALID: Coordinates invalid or cls_id <= 0")
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.INVALID)

        # Update _last_map = current_map so next frame compares with this frame
        self._last_map = current_map
        print(f"[MOVE_DETECTOR] ✓ NEW_MOVE confirmed: ({row},{col}) cls_id={cls_id}")
        return MoveDetectionResult(MoveStatus.NEW_MOVE, row=row, col=col, cls_id=cls_id)

    def _build_map(self, detection_items: List) -> Tuple[Dict[Tuple[int, int], int], bool]:
        #+ Build coordinate map from detection items
        coord_map: Dict[Tuple[int, int], int] = {}
        invalid_found = False
        for item in detection_items:
            if not hasattr(item, 'row') or not hasattr(item, 'col') or not hasattr(item, 'cls_id'):
                continue
            row = int(item.row)
            col = int(item.col)
            cls_id = int(item.cls_id)
            if self._is_valid_coord(row, col):
                coord_map[(row, col)] = cls_id
            else:
                invalid_found = True
        return coord_map, invalid_found

    def _is_valid_coord(self, row: int, col: int) -> bool:
        #+ Validate grid coordinate
        return 0 <= row < self.grid_size and 0 <= col < self.grid_size

