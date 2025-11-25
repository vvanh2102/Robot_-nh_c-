#+ Test Suite for MoveDetector
#+
#+ Validates detection comparison logic to ensure new moves are correctly
#+ identified and noise or invalid scenarios are handled gracefully.
#+
#+ @code
#+ python3 test_move_detector.py
#+ @endcode
#+
#+ @author Automated Gomoku System
#+ @version 1.0
#+ @date 2024

# ============================================================================
# IMPORTS
# ============================================================================

from dataclasses import dataclass
import sys

from move_detector import MoveDetector, MoveStatus

# ============================================================================
# MOCK DETECTION ITEM
# ============================================================================

@dataclass
class MockDetectionItem:
    row: int
    col: int
    cls_id: int

# ============================================================================
# TEST CASES
# ============================================================================


def test_no_previous_frame():
    print("Test 1: No previous frame...")
    detector = MoveDetector(grid_size=13)
    items = [MockDetectionItem(5, 6, 1)]
    result = detector.detect_new_move(items)
    assert result.status == MoveStatus.NEW_MOVE
    assert result.row == 5 and result.col == 6 and result.cls_id == 1
    print("  ✓ Passed")


def test_no_change_between_frames():
    print("Test 2: No change...")
    detector = MoveDetector(grid_size=13)
    items = [MockDetectionItem(5, 6, 1)]
    detector.detect_new_move(items)
    result = detector.detect_new_move(items)
    assert result.status == MoveStatus.NO_CHANGE
    print("  ✓ Passed")


def test_single_new_move():
    print("Test 3: Single new move...")
    detector = MoveDetector(grid_size=13)
    first = [MockDetectionItem(5, 6, 1)]
    detector.detect_new_move(first)
    second = first + [MockDetectionItem(7, 8, 2)]
    result = detector.detect_new_move(second)
    assert result.status == MoveStatus.NEW_MOVE
    assert result.row == 7 and result.col == 8 and result.cls_id == 2
    print("  ✓ Passed")


def test_multiple_new_moves():
    print("Test 4: Multiple new moves...")
    detector = MoveDetector(grid_size=13)
    first = [MockDetectionItem(5, 6, 1)]
    detector.detect_new_move(first)
    second = first + [MockDetectionItem(7, 8, 2), MockDetectionItem(4, 4, 1)]
    result = detector.detect_new_move(second)
    assert result.status == MoveStatus.MULTIPLE_NEW
    print("  ✓ Passed")


def test_invalid_coordinates():
    print("Test 5: Invalid coordinates...")
    detector = MoveDetector(grid_size=13)
    first = []
    detector.detect_new_move(first)
    second = [MockDetectionItem(-1, 0, 1)]
    result = detector.detect_new_move(second)
    assert result.status == MoveStatus.INVALID
    print("  ✓ Passed")


def test_reset_behavior():
    print("Test 6: Reset behavior...")
    detector = MoveDetector(grid_size=13)
    items = [MockDetectionItem(5, 6, 1)]
    detector.detect_new_move(items)
    detector.reset()
    result = detector.detect_new_move(items)
    assert result.status == MoveStatus.NEW_MOVE
    print("  ✓ Passed")


# ============================================================================
# MAIN RUNNER
# ============================================================================


def run_all_tests() -> bool:
    tests = [
        test_no_previous_frame,
        test_no_change_between_frames,
        test_single_new_move,
        test_multiple_new_moves,
        test_invalid_coordinates,
        test_reset_behavior,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
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
        print("✓ All tests passed! Move detector is ready.")
        return True
    print("✗ Some tests failed. Please fix issues before proceeding.")
    return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
