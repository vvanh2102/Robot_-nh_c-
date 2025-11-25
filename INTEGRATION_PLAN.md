# Kế Hoạch Tích Hợp Hệ Thống Robot Đánh Cờ Gomoku

## 📋 Tổng Quan

Tích hợp 3 thành phần:
1. **caro_gui1.py** - Xử lý ảnh, nhận diện quân cờ, điều khiển robot
2. **test_gomoku_heuristic_control_robot.py** - AI Minimax/Alpha-Beta + Heuristic
3. **alpha_zero/** - Model AI đã training

## 🏗️ Kiến Trúc Tổng Thể

```
┌─────────────────────────────────────────────────────────────┐
│                    MainWindow (caro_gui1.py)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Camera       │  │ Detection    │  │ Robot        │    │
│  │ Worker       │  │ Worker       │  │ Control      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Game State Manager (NEW)                       │
│  • Board State Tracking                                     │
│  • Move Validation                                         │
│  • Change Detection                                         │
│  • Game Status (Win/Lose/Draw)                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Strategy Manager (NEW)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Minimax      │  │ Alpha-Zero    │  │ Heuristic    │    │
│  │ Alpha-Beta   │  │ Model         │  │ Evaluator    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Robot Action Executor                           │
│  • Pick from reserve                                        │
│  • Place at calculated position                            │
│  • Return to reference position                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Luồng Hoạt Động Thực Tế

### Phase 1: Khởi Tạo
```
1. User khởi động ứng dụng
2. Kết nối Camera → CameraWorker bắt đầu capture
3. Kết nối Robot → GridRobot được khởi tạo
4. Load AI Models:
   - Minimax/Alpha-Beta (built-in)
   - Alpha-Zero model (nếu có checkpoint)
5. Khởi tạo Game State Manager với bàn cờ trống
6. Chọn AI Strategy (Minimax hoặc Alpha-Zero)
```

### Phase 2: Game Loop (Tự Động)

```
┌─────────────────────────────────────────────────────────────┐
│  LOOP: Mỗi lượt chơi                                        │
└─────────────────────────────────────────────────────────────┘

STEP 1: Phát Hiện Nước Đi Của Người
├─ DetectionWorker liên tục scan bàn cờ
├─ So sánh board_state hiện tại vs board_state trước đó
├─ Phát hiện thay đổi:
│  ├─ Nếu có quân cờ mới xuất hiện
│  ├─ Xác định vị trí (row, col)
│  └─ Xác định player (1 = người, 2 = AI)
└─ Validate nước đi:
   ├─ Kiểm tra ô đã có quân chưa?
   ├─ Kiểm tra lượt chơi đúng chưa?
   └─ Nếu hợp lệ → Cập nhật Game State

STEP 2: Kiểm Tra Kết Thúc Game
├─ Game State Manager kiểm tra:
│  ├─ Người thắng? → Thông báo + Dừng game
│  ├─ AI thắng? → Thông báo + Dừng game
│  ├─ Hòa? → Thông báo + Dừng game
│  └─ Chưa kết thúc → Tiếp tục
└─ Nếu game chưa kết thúc → Chuyển sang STEP 3

STEP 3: AI Tính Toán Nước Đi
├─ Game State Manager truyền board_state cho AI Strategy Manager
├─ AI Strategy Manager:
│  ├─ Nếu chọn Minimax:
│  │  ├─ GomokuHeuristic tính điểm
│  │  ├─ Minimax/Alpha-Beta search
│  │  └─ Trả về (row, col) tốt nhất
│  │
│  └─ Nếu chọn Alpha-Zero:
│     ├─ Load model từ checkpoint
│     ├─ MCTS search (nếu có)
│     ├─ Neural network evaluation
│     └─ Trả về (row, col) tốt nhất
└─ Validate nước đi AI (đảm bảo ô trống)

STEP 4: Robot Thực Hiện Nước Đi AI
├─ Freeze detection (tránh nhiễu khi robot di chuyển)
├─ Robot Actions:
│  ├─ pick_from_reserve() → Lấy quân cờ từ kho
│  ├─ place_cell(row, col) → Đặt quân tại vị trí AI tính
│  └─ robot_goto_ref() → Về vị trí an toàn
├─ Lưu nước đi vào history
├─ Cập nhật Game State
└─ Unfreeze detection → Quay lại STEP 1
```

### Phase 3: Xử Lý Lỗi & Edge Cases

```
1. Detection không phát hiện được bàn cờ
   → Hiển thị "No board detected", chờ frame tiếp theo

2. Phát hiện nước đi không hợp lệ
   → Bỏ qua, không cập nhật game state
   → Log warning

3. AI tính toán lâu
   → Hiển thị "AI thinking..." trong status bar
   → Có thể timeout sau X giây

4. Robot lỗi khi đặt quân
   → Retry mechanism
   → Nếu fail → Thông báo lỗi, cho phép manual place

5. Người đánh sai lượt (đánh 2 lần liên tiếp)
   → Validate và từ chối nước đi
   → Thông báo "Not your turn"
```

## 📦 Các Module Cần Tạo

### 1. `gomoku_game_state.py`
```python
class GomokuGameState:
    - board_state: np.ndarray  # 13x13, 0=empty, 1=human, 2=AI
    - last_board_state: np.ndarray  # Để so sánh
    - current_turn: int  # 1=human, 2=AI
    - move_history: List[Tuple[int, int, int]]  # (row, col, player)
    - game_status: str  # "playing", "human_won", "ai_won", "draw"
    
    Methods:
    - update_from_detection(detections)
    - detect_new_move() -> Optional[Tuple[int, int]]
    - validate_move(row, col, player) -> bool
    - check_win() -> str
    - is_valid_position(row, col) -> bool
```

### 2. `gomoku_ai_strategy.py`
```python
class GomokuAIStrategy:
    - strategy_type: str  # "minimax" or "alphazero"
    - minimax_heuristic: GomokuHeuristic
    - alphazero_model: Optional[Model]
    
    Methods:
    - get_best_move(board_state, player) -> Tuple[int, int]
    - _minimax_move(board_state) -> Tuple[int, int]
    - _alphazero_move(board_state) -> Tuple[int, int]
```

### 3. `move_detector.py`
```python
class MoveDetector:
    - last_detections: List[DetectionItem]
    - current_detections: List[DetectionItem]
    
    Methods:
    - detect_new_move(last_state, current_state) -> Optional[DetectionItem]
    - compare_detections(old_items, new_items) -> List[DetectionItem]
```

## 🔧 Các Thay Đổi Cần Thiết Trong caro_gui1.py

### 1. Thêm Game State Management
```python
# Trong __init__:
self.game_state = GomokuGameState(GRID_SIZE)
self.ai_strategy = GomokuAIStrategy(strategy="minimax")  # hoặc "alphazero"
self.auto_play_mode = False
self.game_active = False
```

### 2. Thêm UI Controls
```python
# Trong _build_ui:
- "Start Game" button
- "Stop Game" button  
- "Reset Board" button
- AI Strategy selector (Minimax/Alpha-Zero)
- Auto Play toggle
```

### 3. Modify on_det_result()
```python
def on_det_result(self, annotated, roi, items):
    # Build board state từ detections
    board_state = self._build_board_from_detections(items)
    
    # Nếu auto_play_mode và game_active:
    if self.auto_play_mode and self.game_active:
        # Phát hiện nước đi mới của người
        new_move = self.game_state.detect_new_move(board_state)
        if new_move:
            # Validate và cập nhật
            if self.game_state.validate_move(new_move[0], new_move[1], 1):
                self.game_state.update_move(new_move[0], new_move[1], 1)
                # Kiểm tra thắng/thua
                status = self.game_state.check_win()
                if status == "playing":
                    # AI tính toán và đánh
                    self._ai_turn()
```

### 4. Thêm _ai_turn() Method
```python
def _ai_turn(self):
    # Freeze detection
    self.sigFreeze.emit(True)
    
    # AI tính toán
    row, col = self.ai_strategy.get_best_move(
        self.game_state.board_state, 
        player=2
    )
    
    # Robot thực hiện
    try:
        self.grid_robot.pick_from_reserve()
        self.grid_robot.place_cell(row, col)
        robot_goto_ref(self.grid_robot)
        
        # Cập nhật game state
        self.game_state.update_move(row, col, 2)
        
        # Kiểm tra thắng/thua
        status = self.game_state.check_win()
        if status != "playing":
            self._handle_game_end(status)
    except Exception as e:
        QMessageBox.critical(self, "AI Move Failed", str(e))
    finally:
        self.sigFreeze.emit(False)
```

## 🎮 Chế Độ Hoạt Động

### Mode 1: Manual Mode (Hiện tại)
- User click "Place" → Chọn vị trí → Robot đánh
- Detection chỉ để hiển thị, không tự động

### Mode 2: Auto Play Mode (Mới)
- Detection tự động phát hiện nước đi người
- AI tự động tính toán và robot tự động đánh
- Game loop tự động chạy

### Mode 3: Practice Mode
- Chỉ detection, không có robot
- Dùng để test detection accuracy

## 📝 Checklist Implementation

- [ ] Tạo `gomoku_game_state.py`
- [ ] Tạo `gomoku_ai_strategy.py` với adapter cho Minimax
- [ ] Tạo `move_detector.py`
- [ ] Modify `caro_gui1.py`:
  - [ ] Thêm game state management
  - [ ] Thêm UI controls (Start/Stop/Reset)
  - [ ] Modify `on_det_result()` để detect moves
  - [ ] Thêm `_ai_turn()` method
  - [ ] Thêm auto play toggle
- [ ] Tích hợp Alpha-Zero model (optional)
- [ ] Testing:
  - [ ] Test move detection
  - [ ] Test move validation
  - [ ] Test AI calculation
  - [ ] Test robot execution
  - [ ] Test full game loop

## 🚀 Ưu Tiên Implementation

1. **Phase 1**: Game State Manager + Move Detection (Core)
2. **Phase 2**: AI Strategy Manager với Minimax (AI cơ bản)
3. **Phase 3**: Auto Play Mode integration (Tự động hóa)
4. **Phase 4**: Alpha-Zero integration (Nâng cao)
5. **Phase 5**: Error handling & Polish (Hoàn thiện)

