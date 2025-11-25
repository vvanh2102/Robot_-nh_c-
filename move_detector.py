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
        self._last_map.clear()

    def detect_new_move(self, detection_items: List) -> MoveDetectionResult:
        #+ Compare current detections with previous and find new move
        current_map, invalid_found = self._build_map(detection_items)
        if invalid_found:
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.INVALID)
        new_positions = [coord for coord in current_map if coord not in self._last_map]

        if len(new_positions) == 0:
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.NO_CHANGE)

        if len(new_positions) > 1:
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.MULTIPLE_NEW)

        (row, col) = new_positions[0]
        cls_id = current_map[(row, col)]
        # Validate coordinates
        if not self._is_valid_coord(row, col) or cls_id <= 0:
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.INVALID)

        self._last_map = current_map
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

