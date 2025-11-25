#+ Gomoku Game State Manager
#+
#+ This module manages the game state for a Gomoku game, including board state
#+ tracking, move validation, change detection, and win condition checking.
#+ It serves as the core state management component for the automated robot
#+ Gomoku system.
#+
#+ Features:
#+   - Board state tracking (13x13 grid)
#+   - Move validation (position, turn, legality)
#+   - Change detection (compare previous vs current state)
#+   - Win condition checking (5 in a row)
#+   - Move history tracking
#+
#+ @code
#+ from gomoku_game_state import GomokuGameState
#+ game_state = GomokuGameState(grid_size=13)
#+ game_state.update_from_detection(detection_items)
#+ new_move = game_state.detect_new_move()
#+ @endcode
#+
#+ @author Automated Gomoku System
#+ @version 1.0
#+ @date 2024

# ============================================================================
# IMPORTS
# ============================================================================

from typing import Optional, Tuple, List
import numpy as np

# ============================================================================
# CONSTANTS
# ============================================================================

# Player identifiers
EMPTY = 0
HUMAN_PLAYER = 1
AI_PLAYER = 2

# Game status constants
STATUS_PLAYING = "playing"
STATUS_HUMAN_WON = "human_won"
STATUS_AI_WON = "ai_won"
STATUS_DRAW = "draw"

# ============================================================================
# GOMOKU GAME STATE CLASS
# ============================================================================

class GomokuGameState:
    #+ Game state manager for Gomoku
    #+
    #+ Manages the complete game state including board position, move history,
    #+ turn tracking, and win condition checking. Provides methods to update
    #+ state from detection results and validate moves.
    #+
    #+ Attributes:
    #+   - board_state: Current board state as numpy array (grid_size x grid_size)
    #+   - last_board_state: Previous board state for change detection
    #+   - current_turn: Current player (1=human, 2=AI)
    #+   - move_history: List of moves as (row, col, player) tuples
    #+   - game_status: Current game status string
    #+   - grid_size: Size of the game board (default 13)
    
    def __init__(self, grid_size: int = 13):
        #+ Initialize game state manager
        #+
        #+ Creates a new game state with an empty board and initializes
        #+ all tracking variables.
        #+
        #+ @code
        #+ game_state = GomokuGameState(grid_size=13)
        #+ @endcode
        #+
        #+ @param grid_size Size of the game board (default: 13)
        self.grid_size = grid_size
        self.board_state = np.zeros((grid_size, grid_size), dtype=np.int8)
        self.last_board_state = np.zeros((grid_size, grid_size), dtype=np.int8)
        self.current_turn = HUMAN_PLAYER  # Human goes first
        self.move_history: List[Tuple[int, int, int]] = []
        self.game_status = STATUS_PLAYING
        self.total_moves = 0
    
    def reset(self) -> None:
        #+ Reset game state to initial state
        #+
        #+ Clears the board, resets turn to human, clears move history,
        #+ and sets game status back to playing.
        #+
        #+ @code
        #+ game_state.reset()
        #+ @endcode
        self.board_state = np.zeros((self.grid_size, self.grid_size), dtype=np.int8)
        self.last_board_state = np.zeros((self.grid_size, self.grid_size), dtype=np.int8)
        self.current_turn = HUMAN_PLAYER
        self.move_history.clear()
        self.game_status = STATUS_PLAYING
        self.total_moves = 0
    
    def update_from_detection(self, detection_items: List) -> None:
        #+ Update board state from detection results
        #+
        #+ Converts detection items (from YOLO) into board state array.
        #+ Detection items should have row, col, and cls_id attributes.
        #+ This method builds the current board state from all detected pieces.
        #+
        #+ @code
        #+ detection_items = [
        #+     DetectionItem(row=5, col=6, cls_id=1, u=100, v=200),
        #+     DetectionItem(row=6, col=7, cls_id=2, u=150, v=250)
        #+ ]
        #+ game_state.update_from_detection(detection_items)
        #+ @endcode
        #+
        #+ @param detection_items List of DetectionItem objects from YOLO detection
        self.last_board_state = self.board_state.copy()
        self.board_state = np.zeros((self.grid_size, self.grid_size), dtype=np.int8)
        
        for item in detection_items:
            if hasattr(item, 'row') and hasattr(item, 'col') and hasattr(item, 'cls_id'):
                row = int(item.row)
                col = int(item.col)
                cls_id = int(item.cls_id)
                
                if self._is_valid_position(row, col):
                    self.board_state[row, col] = cls_id
    
    def detect_new_move(self) -> Optional[Tuple[int, int, int]]:
        #+ Detect new move by comparing current and previous board states
        #+
        #+ Compares the current board state with the last board state to
        #+ identify newly placed pieces. Returns the first new move found
        #+ as (row, col, player_id) tuple, or None if no new move detected.
        #+
        #+ @code
        #+ new_move = game_state.detect_new_move()
        #+ if new_move:
        #+     row, col, player = new_move
        #+     print(f"New move detected: player {player} at ({row}, {col})")
        #+ @endcode
        #+
        #+ @return Tuple of (row, col, player_id) if new move found, None otherwise
        diff = self.board_state - self.last_board_state
        
        # Find positions where difference is non-zero
        changed_positions = np.where(diff != 0)
        
        if len(changed_positions[0]) == 0:
            return None
        
        # Get first changed position
        row = int(changed_positions[0][0])
        col = int(changed_positions[1][0])
        player_id = int(self.board_state[row, col])
        
        # Only return if it's a valid new piece (not empty)
        if player_id != EMPTY:
            return (row, col, player_id)
        
        return None
    
    def validate_move(self, row: int, col: int, player: int) -> bool:
        #+ Validate if a move is legal
        #+
        #+ Checks if a move is valid by verifying:
        #+   - Position is within board boundaries
        #+   - Target cell is empty
        #+   - It is the correct player's turn
        #+
        #+ @code
        #+ if game_state.validate_move(row=5, col=6, player=1):
        #+     game_state.make_move(5, 6, 1)
        #+ else:
        #+     print("Invalid move!")
        #+ @endcode
        #+
        #+ @param row Row index (0-based)
        #+ @param col Column index (0-based)
        #+ @param player Player identifier (1=human, 2=AI)
        #+
        #+ @return True if move is valid, False otherwise
        # Check position is valid
        if not self._is_valid_position(row, col):
            return False
        
        # Check cell is empty
        if self.board_state[row, col] != EMPTY:
            return False
        
        # Check it's the correct player's turn
        if player != self.current_turn:
            return False
        
        return True
    
    def make_move(self, row: int, col: int, player: int) -> bool:
        #+ Make a move on the board
        #+
        #+ Places a piece on the board at the specified position for the
        #+ given player. Updates move history and switches turn. Does not
        #+ validate the move - use validate_move() first.
        #+
        #+ @code
        #+ if game_state.validate_move(5, 6, 1):
        #+     game_state.make_move(5, 6, 1)
        #+ @endcode
        #+
        #+ @param row Row index (0-based)
        #+ @param col Column index (0-based)
        #+ @param player Player identifier (1=human, 2=AI)
        #+
        #+ @return True if move was made, False otherwise
        if not self._is_valid_position(row, col):
            return False
        
        if self.board_state[row, col] != EMPTY:
            return False
        
        # Update board state
        self.last_board_state = self.board_state.copy()
        self.board_state[row, col] = player
        
        # Update move history
        self.move_history.append((row, col, player))
        self.total_moves += 1
        
        # Switch turn
        self.current_turn = AI_PLAYER if player == HUMAN_PLAYER else HUMAN_PLAYER
        
        return True
    
    def check_win(self) -> str:
        #+ Check if game has ended and determine winner
        #+
        #+ Checks all possible winning conditions (5 in a row horizontally,
        #+ vertically, or diagonally) for both players. Also checks for draw
        #+ condition (board full with no winner).
        #+
        #+ @code
        #+ status = game_state.check_win()
        #+ if status == STATUS_HUMAN_WON:
        #+     print("Human wins!")
        #+ elif status == STATUS_AI_WON:
        #+     print("AI wins!")
        #+ @endcode
        #+
        #+ @return Game status string (STATUS_PLAYING, STATUS_HUMAN_WON, STATUS_AI_WON, STATUS_DRAW)
        # Check for human win (5 in a row)
        if self._check_win_for_player(HUMAN_PLAYER):
            self.game_status = STATUS_HUMAN_WON
            return STATUS_HUMAN_WON
        
        # Check for AI win (5 in a row)
        if self._check_win_for_player(AI_PLAYER):
            self.game_status = STATUS_AI_WON
            return STATUS_AI_WON
        
        # Check for draw (board full)
        if self._is_board_full():
            self.game_status = STATUS_DRAW
            return STATUS_DRAW
        
        self.game_status = STATUS_PLAYING
        return STATUS_PLAYING
    
    def _is_valid_position(self, row: int, col: int) -> bool:
        #+ Check if position is within board boundaries
        #+
        #+ @param row Row index
        #+ @param col Column index
        #+
        #+ @return True if position is valid, False otherwise
        return 0 <= row < self.grid_size and 0 <= col < self.grid_size
    
    def _check_win_for_player(self, player: int) -> bool:
        #+ Check if specified player has won (5 in a row)
        #+
        #+ Checks all directions (horizontal, vertical, both diagonals) for
        #+ 5 consecutive pieces of the specified player.
        #+
        #+ @param player Player identifier (1=human, 2=AI)
        #+
        #+ @return True if player has won, False otherwise
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal (top-left to bottom-right)
            (1, -1)   # Diagonal (top-right to bottom-left)
        ]
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.board_state[row, col] == player:
                    for dy, dx in directions:
                        if self._check_line(row, col, dy, dx, player, 5):
                            return True
        
        return False
    
    def _check_line(self, start_row: int, start_col: int, dy: int, dx: int, player: int, length: int) -> bool:
        #+ Check if there are 'length' consecutive pieces in a line
        #+
        #+ Starting from (start_row, start_col), checks if there are 'length'
        #+ consecutive pieces of the specified player in the given direction.
        #+
        #+ @param start_row Starting row
        #+ @param start_col Starting column
        #+ @param dy Row direction (-1, 0, or 1)
        #+ @param dx Column direction (-1, 0, or 1)
        #+ @param player Player identifier
        #+ @param length Required consecutive length (default 5)
        #+
        #+ @return True if line of required length found, False otherwise
        for i in range(length):
            check_row = start_row + i * dy
            check_col = start_col + i * dx
            
            if not self._is_valid_position(check_row, check_col):
                return False
            
            if self.board_state[check_row, check_col] != player:
                return False
        
        return True
    
    def _is_board_full(self) -> bool:
        #+ Check if board is completely filled
        #+
        #+ @return True if board is full, False otherwise
        return np.all(self.board_state != EMPTY)
    
    def get_board_state(self) -> np.ndarray:
        #+ Get current board state as numpy array
        #+
        #+ @return Copy of current board state array
        return self.board_state.copy()
    
    def get_move_history(self) -> List[Tuple[int, int, int]]:
        #+ Get move history
        #+
        #+ @return List of moves as (row, col, player) tuples
        return self.move_history.copy()
    
    def get_current_turn(self) -> int:
        #+ Get current player's turn
        #+
        #+ @return Current player identifier (1=human, 2=AI)
        return self.current_turn
    
    def get_game_status(self) -> str:
        #+ Get current game status
        #+
        #+ @return Game status string
        return self.game_status

