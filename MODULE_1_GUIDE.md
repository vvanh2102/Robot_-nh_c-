# Module 1: Gomoku Game State Manager - Hướng Dẫn Sử Dụng

## ✅ Trạng Thái Module

**Module đã hoàn thành và test thành công!**

- ✅ Tất cả 11 tests đã pass
- ✅ Code đã được kiểm tra linter
- ✅ Sẵn sàng để tích hợp vào hệ thống

## 📋 Tổng Quan

Module `gomoku_game_state.py` quản lý toàn bộ trạng thái game Gomoku, bao gồm:
- Theo dõi trạng thái bàn cờ (13x13)
- Validation nước đi
- Phát hiện thay đổi từ detection
- Kiểm tra điều kiện thắng/thua/hòa
- Lưu lịch sử nước đi

## 🔧 Cách Sử Dụng

### 1. Import Module

```python
from gomoku_game_state import (
    GomokuGameState,
    EMPTY,
    HUMAN_PLAYER,
    AI_PLAYER,
    STATUS_PLAYING,
    STATUS_HUMAN_WON,
    STATUS_AI_WON,
    STATUS_DRAW
)
```

### 2. Khởi Tạo

```python
game_state = GomokuGameState(grid_size=13)
```

### 3. Cập Nhật Từ Detection

```python
# Từ YOLO detection results
detection_items = [
    DetectionItem(row=5, col=6, cls_id=1, u=100, v=200),
    DetectionItem(row=6, col=7, cls_id=2, u=150, v=250)
]

game_state.update_from_detection(detection_items)
```

### 4. Phát Hiện Nước Đi Mới

```python
new_move = game_state.detect_new_move()
if new_move:
    row, col, player = new_move
    print(f"New move: player {player} at ({row}, {col})")
```

### 5. Validate và Thực Hiện Nước Đi

```python
# Validate trước
if game_state.validate_move(row=5, col=6, player=HUMAN_PLAYER):
    # Thực hiện nước đi
    game_state.make_move(5, 6, HUMAN_PLAYER)
    
    # Kiểm tra thắng/thua
    status = game_state.check_win()
    if status == STATUS_HUMAN_WON:
        print("Human wins!")
```

### 6. Reset Game

```python
game_state.reset()  # Xóa bàn cờ, reset về trạng thái ban đầu
```

## 📊 Các Method Chính

### `update_from_detection(detection_items)`
- Cập nhật board state từ kết quả YOLO detection
- Lưu trạng thái trước đó để so sánh

### `detect_new_move() -> Optional[Tuple[int, int, int]]`
- So sánh board hiện tại vs board trước đó
- Trả về (row, col, player_id) nếu có nước đi mới
- Trả về None nếu không có thay đổi

### `validate_move(row, col, player) -> bool`
- Kiểm tra nước đi hợp lệ:
  - Vị trí trong phạm vi bàn cờ
  - Ô trống
  - Đúng lượt chơi

### `make_move(row, col, player) -> bool`
- Thực hiện nước đi (không validate)
- Cập nhật board state, move history
- Chuyển lượt chơi

### `check_win() -> str`
- Kiểm tra điều kiện thắng/thua/hòa
- Trả về: STATUS_PLAYING, STATUS_HUMAN_WON, STATUS_AI_WON, STATUS_DRAW

## 🧪 Test Module

Chạy test suite:

```bash
cd /home/ubuntu/FInal_gomoku_project_AI/Image_processing/Robot_-nh_c-
python3 test_gomoku_game_state.py
```

Kết quả mong đợi:
```
============================================================
Test Results: 11 passed, 0 failed
============================================================
✓ All tests passed! Module is ready for integration.
```

## 🔗 Tích Hợp Vào caro_gui1.py

Module này sẽ được tích hợp vào `MainWindow` class:

```python
# Trong __init__:
from gomoku_game_state import GomokuGameState
self.game_state = GomokuGameState(grid_size=GRID_SIZE)

# Trong on_det_result():
self.game_state.update_from_detection(items)
new_move = self.game_state.detect_new_move()
if new_move:
    row, col, player = new_move
    if self.game_state.validate_move(row, col, player):
        self.game_state.make_move(row, col, player)
        status = self.game_state.check_win()
        # Handle game end...
```

## ⚠️ Lưu Ý

1. **Luôn validate trước khi make_move**: `validate_move()` kiểm tra đầy đủ, `make_move()` không kiểm tra
2. **Update detection trước khi detect_new_move**: Phải gọi `update_from_detection()` trước
3. **Check win sau mỗi nước đi**: Gọi `check_win()` sau `make_move()`
4. **Thread safety**: Module này chưa thread-safe, cần lock khi dùng trong multi-thread

## 📝 Next Steps

Module này đã sẵn sàng. Tiếp theo sẽ tạo:
- **Module 2**: AI Strategy Manager (Minimax/Alpha-Beta)
- **Module 3**: Move Detector (so sánh detection results)


