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
    #+
    #+ Implements stability checking to handle unstable YOLO detection:
    #+   - Tracks candidate new pieces across multiple frames
    #+   - Only confirms a new move after it appears in N consecutive frames
    #+   - Cross-references with game_state to avoid false positives

    def __init__(self, grid_size: int = 13, stability_threshold: int = 2, debug: bool = True) -> None:
        #+ Initialize move detector
        #+
        #+ @param grid_size Size of the game board (default: 13)
        #+ @param stability_threshold Number of consecutive frames a new piece must
        #+        appear in before being confirmed as a valid move (default: 2)
        #+ @param debug Enable debug logging (default: True)
        self.grid_size = grid_size
        self.stability_threshold = stability_threshold
        self.debug = debug
        self._last_map: Dict[Tuple[int, int], int] = {}
        # Track candidate new pieces: {(row, col): count}
        # count = number of consecutive frames this position appeared as "new"
        self._candidate_map: Dict[Tuple[int, int], int] = {}
        # Track if sync has been performed (optimization: avoid repeated sync checks)
        self._synced = False

    def reset(self) -> None:
        #+ Clear detection history
        #+
        #+ Clears _last_map and candidate_map so that the next frame will treat
        #+ all pieces as "new". This is called when starting a new game.
        if self.debug:
            print(f"[MOVE_DETECTOR] RESET: Clearing last_map (had {len(self._last_map)} pieces) and candidate_map")
        self._last_map.clear()
        self._candidate_map.clear()
        self._synced = False
    
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
        
        self._synced = True
        if self.debug:
            print(f"[MOVE_DETECTOR] SYNC: Synced with board state ({len(self._last_map)} pieces)")

    def detect_new_move(self, detection_items: List, game_state=None) -> MoveDetectionResult:
        #+ Compare current detections with previous and find new move
        #+
        #+ Flow with stability checking:
        #+   1. Build current_map from current detection_items
        #+   2. Compare with _last_map (previous frame) to find new pieces
        #+   3. Track candidates in _candidate_map (increment count for each frame)
        #+   4. Only confirm NEW_MOVE if candidate appears in N consecutive frames
        #+   5. Cross-reference with game_state to avoid false positives
        #+   6. Update _last_map = current_map for the next frame
        #+
        #+ @param detection_items List of DetectionItem objects from YOLO
        #+ @param game_state Optional game state to cross-reference (numpy array)
        #+
        #+ Note: _last_map is stored in RAM (instance variable).
        #+       Each call to detect_new_move() compares with the previous frame.
        current_map, invalid_found = self._build_map(detection_items)
        
        # Debug: Log current and last map for tracing (only if debug enabled)
        if self.debug:
            print(f"[MOVE_DETECTOR] Current frame: {len(current_map)} pieces, Last frame: {len(self._last_map)} pieces")
            if current_map:
                print(f"[MOVE_DETECTOR] Current pieces: {list(current_map.keys())}")
            if self._last_map:
                print(f"[MOVE_DETECTOR] Last pieces: {list(self._last_map.keys())}")
        
        if invalid_found:
            if self.debug:
                print(f"[MOVE_DETECTOR] INVALID: Found invalid coordinates in detection")
            self._last_map = current_map
            self._candidate_map.clear()  # Clear candidates on invalid detection
            return MoveDetectionResult(MoveStatus.INVALID)
        
        # Find new positions (exist in current_map but NOT in _last_map)
        new_positions = [coord for coord in current_map if coord not in self._last_map]
        if self.debug and new_positions:
            print(f"[MOVE_DETECTOR] New positions found: {new_positions}")

        # Update candidate map: increment count for positions that appear as "new"
        # and reset count for positions that don't appear as "new" anymore
        for coord in new_positions:
            if coord in self._candidate_map:
                self._candidate_map[coord] += 1
            else:
                self._candidate_map[coord] = 1
        
        # Remove candidates that are no longer "new" (they appeared in last_map now)
        candidates_to_remove = [coord for coord in self._candidate_map if coord not in new_positions]
        for coord in candidates_to_remove:
            del self._candidate_map[coord]
            if self.debug:
                print(f"[MOVE_DETECTOR] Removed unstable candidate: {coord}")

        if len(new_positions) == 0:
            # No change: all pieces already existed in previous frame
            # Clear all candidates since nothing new appeared
            self._candidate_map.clear()
            if self.debug:
                print(f"[MOVE_DETECTOR] NO_CHANGE: No new pieces detected")
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.NO_CHANGE)

        # Check for stable candidates (appeared in N consecutive frames)
        stable_candidates = [
            coord for coord, count in self._candidate_map.items()
            if count >= self.stability_threshold
        ]
        
        if self.debug:
            print(f"[MOVE_DETECTOR] Candidate stability: {dict(self._candidate_map)}")
            print(f"[MOVE_DETECTOR] Stable candidates (≥{self.stability_threshold} frames): {stable_candidates}")

        if len(stable_candidates) == 0:
            # No stable candidate yet, wait for more frames
            if self.debug:
                print(f"[MOVE_DETECTOR] NO_CHANGE: Waiting for stable detection (candidates: {list(self._candidate_map.keys())})")
            self._last_map = current_map
            return MoveDetectionResult(MoveStatus.NO_CHANGE)

        if len(stable_candidates) > 1:
            # More than 1 stable candidate → possibly due to unstable YOLO detection
            if self.debug:
                print(f"[MOVE_DETECTOR] MULTIPLE_NEW: Found {len(stable_candidates)} stable candidates: {stable_candidates}")
            self._last_map = current_map
            self._candidate_map.clear()  # Clear candidates after reporting
            return MoveDetectionResult(MoveStatus.MULTIPLE_NEW)

        # Exactly 1 stable candidate → this is a valid move
        (row, col) = stable_candidates[0]
        cls_id = current_map[(row, col)]
        if self.debug:
            print(f"[MOVE_DETECTOR] NEW_MOVE candidate: ({row},{col}) cls_id={cls_id} (stable for {self._candidate_map[(row, col)]} frames)")
        
        # Cross-reference with game_state if provided
        if game_state is not None:
            if not self._cross_reference_with_game_state(row, col, game_state):
                if self.debug:
                    print(f"[MOVE_DETECTOR] INVALID: Position ({row},{col}) already exists in game_state")
                self._last_map = current_map
                self._candidate_map.clear()
                return MoveDetectionResult(MoveStatus.INVALID)
        
        # Validate coordinates
        if not self._is_valid_coord(row, col) or cls_id <= 0:
            if self.debug:
                print(f"[MOVE_DETECTOR] INVALID: Coordinates invalid or cls_id <= 0")
            self._last_map = current_map
            self._candidate_map.clear()
            return MoveDetectionResult(MoveStatus.INVALID)

        # Update _last_map = current_map so next frame compares with this frame
        # Clear candidate_map since we've confirmed the move
        self._last_map = current_map
        self._candidate_map.clear()
        if self.debug:
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
    
    def _cross_reference_with_game_state(self, row: int, col: int, game_state) -> bool:
        #+ Cross-reference detected position with game state
        #+
        #+ Checks if the detected position is already occupied in the game state.
        #+ This helps avoid false positives when YOLO detects an old piece as new.
        #+
        #+ @param row Row index of detected position
        #+ @param col Column index of detected position
        #+ @param game_state Numpy array with board state (0=empty, 1=human, 2=AI)
        #+
        #+ @return True if position is empty in game_state (valid new move),
        #+         False if position is already occupied (false positive)
        import numpy as np
        if game_state is None:
            return True  # No game_state provided, skip check
        
        if not (0 <= row < game_state.shape[0] and 0 <= col < game_state.shape[1]):
            return False  # Out of bounds
        
        # Position is valid if it's empty (0) in game_state
        return int(game_state[row, col]) == 0

