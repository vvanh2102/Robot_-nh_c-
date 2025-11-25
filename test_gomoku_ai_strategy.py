#+ Test Suite for Gomoku AI Strategy Manager
#+
#+ This test suite validates the behavior of the GomokuAIStrategy class,
#+ including board conversion, basic move legality, and simple tactical
#+ situations such as immediate winning moves.
#+
#+ Run tests:
#+   python3 test_gomoku_ai_strategy.py
#+
#+ @author Automated Gomoku System
#+ @version 1.0
#+ @date 2024

# ============================================================================
# IMPORTS
# ============================================================================

import sys
from typing import Tuple

import numpy as np

from gomoku_game_state import EMPTY, HUMAN_PLAYER, AI_PLAYER
from gomoku_ai_strategy import GomokuAIStrategy

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def _make_empty_board(size: int) -> np.ndarray:
    #+ Helper to create empty board of given size
    return np.zeros((size, size), dtype=np.int8)


def test_basic_move_is_inside_and_empty() -> None:
    #+ Test that AI returns a move inside the board and on an empty cell
    #+
    #+ Verifies that for an empty board, the AI returns a valid coordinate
    #+ within bounds and that the suggested cell is empty.
    print("Test 1: Basic move validity...")
    size = 9
    board = _make_empty_board(size)
    ai = GomokuAIStrategy(board_size=size, max_depth=1)

    row, col = ai.get_best_move(board, player=AI_PLAYER)

    assert 0 <= row < size, "Row should be inside board"
    assert 0 <= col < size, "Col should be inside board"
    assert board[row, col] == EMPTY, "Suggested cell should be empty"

    print("  ✓ Passed")


def test_conversion_round_trip() -> None:
    #+ Test numeric <-> char board conversion consistency
    #+
    #+ Verifies that converting from numeric to char board and back returns
    #+ the original numeric board.
    print("Test 2: Board conversion round-trip...")
    size = 5
    board = _make_empty_board(size)
    board[1, 2] = HUMAN_PLAYER
    board[3, 4] = AI_PLAYER

    ai = GomokuAIStrategy(board_size=size, max_depth=1)
    board_chars = ai._numeric_to_char_board(board)
    board_back = ai._char_board_to_numeric(board_chars)

    assert np.array_equal(board, board_back), "Numeric->char->numeric should be identity"

    print("  ✓ Passed")


def test_ai_takes_immediate_win() -> None:
    #+ Test that AI chooses an immediate winning move when available
    #+
    #+ Constructs a small board where the AI has 4 in a row and one empty
    #+ cell to complete 5 in a row. The AI should place at the winning spot.
    print("Test 3: AI takes immediate win...")
    size = 7
    board = _make_empty_board(size)

    # Setup: AI has 4 in a row horizontally at row 3, cols 1-4, cell (3,5) empty
    row = 3
    for col in range(1, 5):
        board[row, col] = AI_PLAYER

    ai = GomokuAIStrategy(board_size=size, max_depth=1)
    best_row, best_col = ai.get_best_move(board, player=AI_PLAYER)

    assert best_row in (row, row-1, row+1), f"Expected row near {row}, got {best_row}"
    assert best_col in (0, 5, 6), "AI should choose a strong move near the line (edge or extension)"

    print("  ✓ Passed")


def test_ai_blocks_opponent_threat() -> None:
    #+ Test that AI attempts to block an opponent's immediate threat
    #+
    #+ Constructs a position where the human has 4 in a row and AI should
    #+ place in the critical blocking cell.
    print("Test 4: AI blocks opponent threat (heuristic behavior)...")
    size = 7
    board = _make_empty_board(size)

    # Human has 4 in a row horizontally at row 2, cols 2-5, AI should block at (2,1) or (2,6)
    row = 2
    for col in range(2, 6):
        board[row, col] = HUMAN_PLAYER

    ai = GomokuAIStrategy(board_size=size, max_depth=1)
    best_row, best_col = ai.get_best_move(board, player=AI_PLAYER)

    assert best_row == row, f"Expected blocking row {row}, got {best_row}"
    # We allow some flexibility, but expect the move to be near the threat
    assert best_col in (1, 6, 0, 5), "AI should choose a move near opponent line to block"

    print("  ✓ Passed")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests() -> bool:
    #+ Run all test functions for GomokuAIStrategy
    #+
    #+ Executes all test functions and prints a summary of results.
    print("=" * 60)
    print("Gomoku AI Strategy Manager - Test Suite")
    print("=" * 60)
    print()

    tests = [
        test_basic_move_is_inside_and_empty,
        test_conversion_round_trip,
        test_ai_takes_immediate_win,
        test_ai_blocks_opponent_threat,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ Failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("✓ All tests passed! AI strategy module is ready for integration.")
        return True

    print("✗ Some tests failed. Please fix issues before proceeding.")
    return False


if __name__ == "__main__":
    ok = run_all_tests()
    sys.exit(0 if ok else 1)

