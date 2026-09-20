#+ Gomoku AI Strategy Manager
#+
#+ This module provides AI move selection for Gomoku using either a
#+ heuristic-based minimax search or an AlphaZero-based MCTS player.
#+ It acts as an adapter between the numeric board representation used by
#+ the game state manager and the underlying AI engines.
#+
#+ Features:
#+   - Conversion between numpy board (0/1/2) and character board (' ', 'X', 'O')
#+   - Heuristic scoring for candidate moves
#+   - Minimax search with configurable depth and alpha-beta pruning
#+   - Simple public API: get_best_move(board_state, player)
#+
#+ @code
#+ from gomoku_ai_strategy import GomokuAIStrategy
#+ from gomoku_game_state import AI_PLAYER
#+
#+ ai = GomokuAIStrategy(board_size=13, max_depth=2)
#+ row, col = ai.get_best_move(board_state, player=AI_PLAYER)
#+ @endcode
#+
#+ @author Automated Gomoku System
#+ @version 1.0
#+ @date 2024

# ============================================================================
# IMPORTS
# ============================================================================

from typing import Tuple, Optional

import numpy as np

from gomoku_game_state import EMPTY, HUMAN_PLAYER, AI_PLAYER
from pathlib import Path
import sys
import os

# Add project root to sys.path so we can import heuristic / AlphaZero modules
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from algorithm_AI_trainning.python.Gomoku_heuristic_minimax import GomokuHeuristic

# Ensure AlphaZero package root is on sys.path so that imports like
# `from alpha_zero.envs.gomoku import GomokuEnv` work correctly.
AZ_ROOT = PROJECT_ROOT / "algorithm_AI_trainning" / "alpha_zero"
if str(AZ_ROOT) not in sys.path:
    sys.path.insert(0, str(AZ_ROOT))

try:
    # Optional AlphaZero imports (may fail if dependencies are missing)
    from alpha_zero.envs.gomoku import GomokuEnv
    from alpha_zero.core.network import AlphaZeroNet
    from alpha_zero.core.pipeline import (
        create_mcts_player,
        disable_auto_grad,
    )
    _ALPHAZERO_AVAILABLE = True
except Exception:
    _ALPHAZERO_AVAILABLE = False

# ============================================================================
# CONSTANTS
# ============================================================================

# Mapping from numeric players to board characters
HUMAN_CHAR = 'X'
AI_CHAR = 'O'
EMPTY_CHAR = ' '

# Strategy identifiers
STRATEGY_MINIMAX = "minimax"
STRATEGY_ALPHAZERO = "alphazero"

# ============================================================================
# GOMOKU AI STRATEGY CLASS
# ============================================================================

class GomokuAIStrategy:
    #+ AI strategy manager for Gomoku
    #+
    #+ Provides a high-level interface for computing the best move for the AI
    #+ player on a given board state. Internally, it converts the numeric
    #+ representation (0/1/2) into a character-based board used by the
    #+ heuristic evaluator, and either runs a minimax search or uses an
    #+ AlphaZero-based MCTS player depending on the configured strategy.
    #+
    #+ Attributes:
    #+   - board_size: Size of the board (e.g., 13)
    #+   - max_depth: Maximum depth for minimax search (for minimax strategy)
    #+   - use_alpha_beta: Enable/disable alpha-beta pruning
    #+   - strategy_type: AI engine type ("minimax" or "alphazero")
    
    def __init__(
        self,
        board_size: int = 13,
        max_depth: int = 2,
        use_alpha_beta: bool = True,
        strategy_type: str = STRATEGY_MINIMAX,
    ) -> None:
        #+ Initialize AI strategy manager
        #+
        #+ @code
        #+ ai = GomokuAIStrategy(board_size=13, max_depth=2)
        #+ @endcode
        #+
        #+ @param board_size Size of the game board (default: 13)
        #+ @param max_depth Maximum search depth for minimax (default: 2)
        #+ @param use_alpha_beta Enable alpha-beta pruning (default: True)
        #+ @param strategy_type AI engine type ("minimax" or "alphazero")
        self.board_size = board_size
        self.max_depth = max_depth
        self.use_alpha_beta = use_alpha_beta
        self.strategy_type = strategy_type if strategy_type in (STRATEGY_MINIMAX, STRATEGY_ALPHAZERO) else STRATEGY_MINIMAX

        # AlphaZero-related members (lazy init)
        self._az_env = None
        self._az_mcts_player = None
        self._az_device = None
        self._az_c_puct_base = 19652.0
        self._az_c_puct_init = 1.25
        self._az_ckpt_path = os.path.join(
            PROJECT_ROOT,
            "algorithm_AI_trainning",
            "alpha_zero",
            "checkpoints",
            "gomoku",
            "13x13",
            "training_steps_200000.ckpt",
        )

    # ---------------------------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------------------------

    def get_best_move(self, board_state: np.ndarray, player: int) -> Tuple[int, int]:
        #+ Compute the best move for the given player
        #+
        #+ Selects a move for the specified player using the configured
        #+ AI strategy (minimax or AlphaZero).
        #+
        #+ @code
        #+ row, col = ai.get_best_move(board_state, player=AI_PLAYER)
        #+ @endcode
        #+
        #+ @param board_state Current board state as numpy array (NxN) with
        #+        values: 0=empty, 1=human, 2=AI
        #+ @param player Player identifier (HUMAN_PLAYER or AI_PLAYER)
        #+
        #+ @return Tuple of (row, col) for the selected move
        if self.strategy_type == STRATEGY_ALPHAZERO:
            return self._alphazero_move(board_state, player)

        # Default: minimax strategy
        board_chars = self._numeric_to_char_board(board_state)
        is_ai_maximizing = player == AI_PLAYER

        # 1) Immediate tactical checks (fast path)
        if player == AI_PLAYER:
            win_move = self._find_immediate_win(board_chars, AI_CHAR)
            if win_move is not None:
                return win_move
            block_move = self._find_immediate_win(board_chars, HUMAN_CHAR)
            if block_move is not None:
                return block_move

        # 2) Strategic search using minimax
        _, move = self._minimax(
            board_chars,
            depth=self.max_depth,
            maximizing=is_ai_maximizing,
            current_player=player,
            alpha=float("-inf"),
            beta=float("inf"),
        )

        if move is None:
            return -1, -1
        return move

    # ---------------------------------------------------------------------
    # INTERNAL HELPERS
    # ---------------------------------------------------------------------

    def _numeric_to_char_board(self, board_state: np.ndarray) -> list:
        #+ Convert numeric board (0/1/2) to character board (' ', 'X', 'O')
        #+
        #+ @param board_state Numpy array with values 0,1,2
        #+
        #+ @return 2D list of characters
        size = board_state.shape[0]
        board_chars = []
        for row in range(size):
            row_chars = []
            for col in range(size):
                value = int(board_state[row, col])
                if value == HUMAN_PLAYER:
                    row_chars.append(HUMAN_CHAR)
                elif value == AI_PLAYER:
                    row_chars.append(AI_CHAR)
                else:
                    row_chars.append(EMPTY_CHAR)
            board_chars.append(row_chars)
        return board_chars

    def _char_board_to_numeric(self, board_chars: list) -> np.ndarray:
        #+ Convert character board (' ', 'X', 'O') back to numeric board (0/1/2)
        #+
        #+ @param board_chars 2D list of characters
        #+
        #+ @return Numpy array with values 0,1,2
        size = len(board_chars)
        board_state = np.zeros((size, size), dtype=np.int8)
        for row in range(size):
            for col in range(size):
                cell = board_chars[row][col]
                if cell == HUMAN_CHAR:
                    board_state[row, col] = HUMAN_PLAYER
                elif cell == AI_CHAR:
                    board_state[row, col] = AI_PLAYER
                else:
                    board_state[row, col] = EMPTY
        return board_state

    def _find_immediate_win(self, board_chars: list, char: str) -> Optional[Tuple[int, int]]:
        #+ Find an immediate winning move for the given character
        #+
        #+ Tries placing the given character on each empty cell and checks
        #+ if that results in 5 in a row. Returns the first winning move
        #+ found, or None if no such move exists.
        #+
        #+ @param board_chars 2D list of characters
        #+ @param char Player character ('X' for human, 'O' for AI)
        #+
        #+ @return Tuple of (row, col) if winning move found, None otherwise
        size = len(board_chars)
        for row in range(size):
            for col in range(size):
                if board_chars[row][col] != EMPTY_CHAR:
                    continue
                # Try move
                board_chars[row][col] = char
                if self._has_five_in_a_row(board_chars, char):
                    # Undo before returning
                    board_chars[row][col] = EMPTY_CHAR
                    return row, col
                # Undo move
                board_chars[row][col] = EMPTY_CHAR
        return None

    def _has_five_in_a_row(self, board_chars: list, char: str) -> bool:
        #+ Check if the given character has at least 5 in a row anywhere
        #+
        #+ Checks horizontal, vertical, and both diagonal directions for a
        #+ sequence of 5 consecutive cells occupied by the specified char.
        #+
        #+ @param board_chars 2D list of characters
        #+ @param char Character to check ('X' or 'O')
        #+
        #+ @return True if there is a line of 5, False otherwise
        size = len(board_chars)
        directions = [
            (0, 1),   # horizontal
            (1, 0),   # vertical
            (1, 1),   # main diagonal
            (1, -1),  # anti diagonal
        ]

        def in_bounds(r: int, c: int) -> bool:
            return 0 <= r < size and 0 <= c < size

        for row in range(size):
            for col in range(size):
                if board_chars[row][col] != char:
                    continue
                for dy, dx in directions:
                    count = 1
                    # Extend in positive direction
                    r, c = row + dy, col + dx
                    while in_bounds(r, c) and board_chars[r][c] == char:
                        count += 1
                        r += dy
                        c += dx
                    # Extend in negative direction
                    r, c = row - dy, col - dx
                    while in_bounds(r, c) and board_chars[r][c] == char:
                        count += 1
                        r -= dy
                        c -= dx
                    if count >= 5:
                        return True
        return False

    def _evaluate_board(self, board_chars: list, player: int) -> int:
        #+ Evaluate board position using heuristic
        #+
        #+ Uses `GomokuHeuristic.stupid_score` to compute the score for the
        #+ specified player at the current board state by aggregating scores
        #+ over all possible empty positions.
        #+
        #+ @param board_chars 2D list of characters
        #+ @param player Player identifier (HUMAN_PLAYER or AI_PLAYER)
        #+
        #+ @return Integer heuristic score (higher is better for AI)
        size = len(board_chars)
        heuristic = GomokuHeuristic(board_chars)
        
        if player == AI_PLAYER:
            my_char = AI_CHAR
            opp_char = HUMAN_CHAR
        else:
            my_char = HUMAN_CHAR
            opp_char = AI_CHAR
        
        total_score = 0
        for row in range(size):
            for col in range(size):
                if board_chars[row][col] == EMPTY_CHAR:
                    score = heuristic.stupid_score(my_char, opp_char, row, col)
                    total_score += score
        
        return total_score

    def _is_terminal(self, board_chars: list) -> bool:
        #+ Check if the game is in a terminal state (win or full board)
        #+
        #+ @param board_chars 2D list of characters
        #+
        #+ @return True if no more moves are possible
        size = len(board_chars)
        for row in range(size):
            for col in range(size):
                if board_chars[row][col] == EMPTY_CHAR:
                    return False
        return True

    def _init_alphazero_if_needed(self) -> bool:
        #+ Lazily initialize AlphaZero environment and MCTS player
        if not _ALPHAZERO_AVAILABLE:
            return False
        if self._az_env is not None and self._az_mcts_player is not None:
            return True

        try:
            import torch
        except Exception:
            return False

        # Select device
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")

        env = GomokuEnv(board_size=self.board_size, num_stack=8)
        input_shape = env.observation_space.shape
        num_actions = env.action_space.n

        network = AlphaZeroNet(
            input_shape=input_shape,
            num_actions=num_actions,
            num_res_block=10,
            num_filters=40,
            num_fc_units=80,
            gomoku=True,
        ).to(device)
        disable_auto_grad(network)

        if os.path.isfile(self._az_ckpt_path):
            loaded_state = torch.load(self._az_ckpt_path, map_location=device)
            if "network" in loaded_state:
                network.load_state_dict(loaded_state["network"])
        network.eval()

        mcts_player = create_mcts_player(
            network=network,
            device=device,
            num_simulations=200,
            num_parallel=4,
            root_noise=False,
            deterministic=False,
        )

        self._az_env = env
        self._az_mcts_player = mcts_player
        self._az_device = device
        return True

    def _sync_alphazero_env(self, board_state: np.ndarray, player: int) -> None:
        #+ Synchronize AlphaZero environment with external board state
        #+
        #+ Debug: Log board state before syncing with AlphaZero
        #+ Board state format: 0=empty, 1=HUMAN_PLAYER, 2=AI_PLAYER
        #+ AlphaZero format: 0=empty, 1=black, 2=white
        print(f"[ALPHAZERO_SYNC] Syncing board state for player={player} (AI_PLAYER={AI_PLAYER})")
        print(f"[ALPHAZERO_SYNC] Board state shape: {board_state.shape}, dtype: {board_state.dtype}")
        print(f"[ALPHAZERO_SYNC] Board state summary: EMPTY={np.sum(board_state == 0)}, "
              f"HUMAN={np.sum(board_state == HUMAN_PLAYER)}, AI={np.sum(board_state == AI_PLAYER)}")
        
        env = self._az_env
        env.reset()

        # Copy numeric board directly (1=black, 2=white)
        # Note: Our board_state uses 1=HUMAN_PLAYER, 2=AI_PLAYER
        # AlphaZero expects: 1=black (first player), 2=white (second player)
        # We assume: HUMAN_PLAYER=1 maps to black, AI_PLAYER=2 maps to white
        env.board[:, :] = board_state.astype(np.int8)
        
        print(f"[ALPHAZERO_SYNC] AlphaZero env.board summary: EMPTY={np.sum(env.board == 0)}, "
              f"BLACK={np.sum(env.board == 1)}, WHITE={np.sum(env.board == 2)}")

        # Legal actions: only empty cells are legal
        env.legal_actions[:] = 1
        for row in range(self.board_size):
            for col in range(self.board_size):
                if env.board[row, col] != 0:
                    action = env.coords_to_action((row, col))
                    if action is not None:
                        env.legal_actions[action] = 0

        env.to_play = AI_PLAYER if player == AI_PLAYER else HUMAN_PLAYER
        env.steps = int(np.count_nonzero(env.board))
        env.winner = None
        env.last_player = None
        env.last_move = None

        # Reset history buffer and board deltas
        env.board_deltas = env.get_empty_queue()
        env.board_deltas.appendleft(np.copy(env.board))
        del env.history[:]

    def _alphazero_move(self, board_state: np.ndarray, player: int) -> Tuple[int, int]:
        #+ Compute move using AlphaZero-based MCTS player
        #+
        #+ Returns (-1, -1) if AlphaZero is not available or initialization fails.
        if not self._init_alphazero_if_needed():
            return -1, -1

        self._sync_alphazero_env(board_state, player)
        env = self._az_env

        move, *_ = self._az_mcts_player(
            env,
            None,
            self._az_c_puct_base,
            self._az_c_puct_init,
        )

        row, col = env.action_to_coords(move)
        return int(row), int(col)

    def _minimax(
        self,
        board_chars: list,
        depth: int,
        maximizing: bool,
        current_player: int,
        alpha: float,
        beta: float,
    ) -> Tuple[int, Optional[Tuple[int, int]]]:
        #+ Minimax search with alpha-beta pruning
        #+
        #+ Recursively searches the game tree up to a given depth using the
        #+ heuristic evaluator. Returns the best score and corresponding move
        #+ for the current player.
        #+
        #+ @param board_chars 2D list of characters representing board state
        #+ @param depth Remaining search depth
        #+ @param maximizing True if current node is maximizing player
        #+ @param current_player Current player identifier
        #+ @param alpha Alpha value for alpha-beta pruning
        #+ @param beta Beta value for alpha-beta pruning
        #+
        #+ @return Tuple of (score, (row, col) or None)
        
        # Terminal condition: depth 0 or no more moves
        if depth == 0 or self._is_terminal(board_chars):
            score_ai = self._evaluate_board(board_chars, AI_PLAYER)
            score_human = self._evaluate_board(board_chars, HUMAN_PLAYER)
            # Overall score is AI minus human
            return score_ai - score_human, None
        
        size = len(board_chars)
        best_move: Optional[Tuple[int, int]] = None
        
        if maximizing:
            best_score = float('-inf')
        else:
            best_score = float('inf')
        
        # Iterate over all possible moves
        for row in range(size):
            for col in range(size):
                if board_chars[row][col] != EMPTY_CHAR:
                    continue
                
                # Apply move
                if current_player == AI_PLAYER:
                    board_chars[row][col] = AI_CHAR
                    next_player = HUMAN_PLAYER
                    next_maximizing = False
                else:
                    board_chars[row][col] = HUMAN_CHAR
                    next_player = AI_PLAYER
                    next_maximizing = True
                
                # Recursive call
                score, _ = self._minimax(
                    board_chars,
                    depth=depth - 1,
                    maximizing=next_maximizing,
                    current_player=next_player,
                    alpha=alpha,
                    beta=beta,
                )
                
                # Undo move
                board_chars[row][col] = EMPTY_CHAR
                
                # Update best score and move
                if maximizing:
                    if score > best_score:
                        best_score = score
                        best_move = (row, col)
                    if self.use_alpha_beta:
                        alpha = max(alpha, best_score)
                        if beta <= alpha:
                            break
                else:
                    if score < best_score:
                        best_score = score
                        best_move = (row, col)
                    if self.use_alpha_beta:
                        beta = min(beta, best_score)
                        if beta <= alpha:
                            break
            # Break outer loop on pruning
            if self.use_alpha_beta and beta <= alpha:
                break
        
        return int(best_score), best_move

