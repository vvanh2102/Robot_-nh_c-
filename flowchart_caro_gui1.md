# Flowchart - Hệ thống Caro GUI Tự động

## Sơ đồ tổng quan luồng hoạt động của caro_gui1.py

```mermaid
flowchart TD
    Start([Khởi động ứng dụng]) --> Init[Khởi tạo MainWindow]
    Init --> InitState[Khởi tạo trạng thái:<br/>- game_state GomokuGameState<br/>- move_detector MoveDetector<br/>- ai_strategy GomokuAIStrategy<br/>- grid_robot GridRobot]
    InitState --> InitThreads[Khởi tạo Worker Threads:<br/>- CameraWorker thread<br/>- DetectionWorker thread]
    InitThreads --> BuildUI[Xây dựng giao diện UI:<br/>- Toolbar với các nút điều khiển<br/>- Camera view label<br/>- Board state table 13x13<br/>- Vacuum controls]
    BuildUI --> StartCam[Bắt đầu Camera Thread]

    %% Camera Thread Loop
    StartCam --> CamLoop{Camera Loop<br/>Thread 1}
    CamLoop -->|Liên tục| CaptureFrame[Capture Frame từ camera]
    CaptureFrame --> CheckCamOK{Frame OK?}
    CheckCamOK -->|Không| CamSleep[Sleep 0.01s]
    CamSleep --> CamLoop
    CheckCamOK -->|Có| EmitFrame[Emit newFrame signal]
    EmitFrame --> CamLoop

    %% Main Thread - Frame Handler
    EmitFrame --> OnNewFrame[on_new_frame<br/>Main Thread]
    OnNewFrame --> SaveLastFrame[Lưu last_frame]
    SaveLastFrame --> CheckDetect{Detection<br/>đang chạy?}
    CheckDetect -->|Không| DisplayDirect[Hiển thị frame trực tiếp<br/>lên lbl_view]
    CheckDetect -->|Có| CheckFrozen{Frozen?}
    CheckFrozen -->|Có| WaitUnfreeze[Đợi unfreeze]
    CheckFrozen -->|Không| UpdateDetThread[Cập nhật frame cho<br/>DetectionWorker]

    %% Detection Thread Loop
    UpdateDetThread --> DetLoop{Detection Loop<br/>Thread 2}
    DetLoop -->|Khi có frame mới| FindBoard[_find_board_roi:<br/>Dùng YOLO board_model<br/>tìm bounding box của bàn cờ]
    FindBoard --> BoardFound{Tìm thấy<br/>board ROI?}
    BoardFound -->|Không| DrawNoBoard[Vẽ text "No board ROI"<br/>lên frame]
    BoardFound -->|Có| ApplyShrink[Áp dụng shrink factor<br/>0.99 cho ROI]

    ApplyShrink --> DrawGrid[Vẽ lưới 13x13 và<br/>viền board lên frame]
    DrawGrid --> CropBoard[Crop board region<br/>từ frame gốc]
    CropBoard --> DetectPieces[Dùng YOLO piece_model<br/>detect quân cờ trong ROI<br/>với conf=0.35]

    DetectPieces --> ProcessBoxes[Xử lý detection boxes:<br/>- Tính center point<br/>- Convert sang grid coords<br/>- Map class: 0→player1, else→player2]
    ProcessBoxes --> FilterStable[Temporal filtering:<br/>Lọc detections ổn định<br/>qua DETECTION_STABILITY_FRAMES=3<br/>frames liên tiếp]

    FilterStable --> CreateItems[Tạo DetectionItem list<br/>cho stable detections]
    CreateItems --> DrawDetections[Vẽ circles & labels<br/>cho stable detections<br/>màu xanh/vàng<br/>và gray cho unstable]
    DrawDetections --> EmitResult[Emit result signal:<br/>annotated, roi, items]

    %% Main Thread - Detection Result Handler
    EmitResult --> HandleResult[on_det_result<br/>Main Thread]
    HandleResult --> BuildDetBoard[Tạo detection_board<br/>từ items]
    BuildDetBoard --> RefreshUI[_refresh_board:<br/>Cập nhật table widget<br/>từ game_state board]
    RefreshUI --> UpdatePrefill[Cập nhật prefill_cell<br/>từ last detection]
    UpdatePrefill --> DrawInstruction[Vẽ instruction text<br/>lên annotated frame]
    DrawInstruction --> DisplayAnnotated[Hiển thị annotated frame<br/>lên lbl_view]

    DisplayAnnotated --> CheckAutoPlay{Auto Play<br/>enabled &<br/>game_active?}

    CheckAutoPlay -->|Không| EndDetResult[Kết thúc xử lý]
    CheckAutoPlay -->|Có| DetectMove[move_detector.detect_new_move:<br/>So sánh items hiện tại<br/>với frame trước]

    DetectMove --> MoveStatus{Move Status}
    MoveStatus -->|NO_CHANGE| EndDetResult
    MoveStatus -->|MULTIPLE_NEW| ShowWarningMultiple[Hiển thị warning:<br/>Multiple new detections]
    MoveStatus -->|INVALID| ShowWarningInvalid[Hiển thị warning:<br/>Invalid coordinates]
    MoveStatus -->|NEW_MOVE| CheckPlayer{cls_id ==<br/>HUMAN_PLAYER?}

    CheckPlayer -->|Không| EndDetResult
    CheckPlayer -->|Có| ProcessHuman[_process_human_move]

    %% Human Move Processing
    ProcessHuman --> CheckGameActive{game_active?}
    CheckGameActive -->|Không| IgnoreMove[Bỏ qua move]
    CheckGameActive -->|Có| ValidateMove{game_state.validate_move:<br/>- Trong bounds?<br/>- Ô trống?<br/>- Đúng lượt?}

    ValidateMove -->|Không| ShowInvalid[Hiển thị lỗi<br/>invalid move với lý do]
    ValidateMove -->|Có| RegisterHuman[game_state.make_move<br/>cho HUMAN_PLAYER=1]

    RegisterHuman --> DebugPrintHuman[Debug: In board state<br/>và move history]
    DebugPrintHuman --> CheckWinHuman{game_state.check_win:<br/>Kiểm tra thắng/thua/hòa}

    CheckWinHuman -->|STATUS_HUMAN_WON| HandleEndHumanWin[_handle_game_end:<br/>Hiển thị "Player win"]
    CheckWinHuman -->|STATUS_DRAW| HandleEndDraw[_handle_game_end:<br/>Hiển thị "Draw"]
    CheckWinHuman -->|STATUS_PLAYING| StatusHumanDone[Update status:<br/>"AI thinking..."]

    StatusHumanDone --> TriggerAI[Kích hoạt _ai_turn]

    %% AI Turn Processing
    TriggerAI --> AITurn[_ai_turn]
    AITurn --> CheckAIGameActive{game_active?}
    CheckAIGameActive -->|Không| EndAITurn[Return]
    CheckAIGameActive -->|Có| GetBoard[Lấy board_state<br/>từ game_state]

    GetBoard --> DebugPrintAI[Debug: In board state<br/>trước AI computation]
    DebugPrintAI --> ComputeAI[ai_strategy.get_best_move:<br/>- Minimax with depth 1-3<br/>hoặc AlphaZero neural net]

    ComputeAI --> CheckValidAI{AI move<br/>valid?}
    CheckValidAI -->|Không row,col<0| NoMove[Hiển thị "AI has<br/>no valid moves"]
    CheckValidAI -->|Có| FreezeOn[sigFreeze.emit True:<br/>Dừng detection]

    FreezeOn --> RobotCheck{Robot<br/>connected?}
    RobotCheck -->|Có| RobotSequence[Robot thực hiện:<br/>1. pick_from_reserve<br/>2. place_cell row,col<br/>3. robot_goto_ref]
    RobotCheck -->|Không| RecordOnly[Chỉ ghi nhận nước đi<br/>không điều khiển robot]

    RobotSequence --> UpdateRobotPos[Cập nhật lbl_robot_pos:<br/>cell row,col → base x,y mm]
    RecordOnly --> UpdateRobotPos

    UpdateRobotPos --> ValidateAI{game_state.validate_move<br/>cho AI?}
    ValidateAI -->|Có| RegisterAI[game_state.make_move<br/>cho AI_PLAYER=2]
    ValidateAI -->|Không| SkipRegister[Bỏ qua registration]

    RegisterAI --> DebugPrintAIAfter[Debug: In board state<br/>và move history sau AI]
    DebugPrintAIAfter --> CheckWinAI{game_state.check_win}
    SkipRegister --> CheckWinAI

    CheckWinAI -->|STATUS_AI_WON| HandleEndAIWin[_handle_game_end:<br/>Hiển thị "AI win"]
    CheckWinAI -->|STATUS_DRAW| HandleEndDraw
    CheckWinAI -->|STATUS_PLAYING| FreezeOff[sigFreeze.emit False:<br/>Tiếp tục detection]

    FreezeOff --> EndAITurn

    %% Game End Handler
    HandleEndHumanWin --> GameEndCommon[_handle_game_end common]
    HandleEndAIWin --> GameEndCommon
    HandleEndDraw --> GameEndCommon

    GameEndCommon --> SetInactive[game_active = False]
    SetInactive --> ShowPopup[Hiển thị QMessageBox<br/>với kết quả]
    ShowPopup --> PlayAgain{User chọn<br/>"Play again"?}

    PlayAgain -->|Có| ResetGame[_reset_game_state:<br/>- game_state.reset<br/>- move_detector.reset<br/>- Clear board view]
    PlayAgain -->|Không| StopGame[Dừng game,<br/>giữ detection running]

    ResetGame --> StartDetect{Detection<br/>đang chạy?}
    StartDetect -->|Không| StartDetectNew[on_start_detect]
    StartDetect -->|Có| ContinueDetect[Tiếp tục detection]
    StartDetectNew --> ContinueDetect
    ContinueDetect --> EndDetResult

    %% Loop back
    EndDetResult --> DetLoop
    WaitUnfreeze --> OnNewFrame
    DisplayDirect --> OnNewFrame
    IgnoreMove --> EndDetResult
    ShowInvalid --> EndDetResult
    ShowWarningMultiple --> EndDetResult
    ShowWarningInvalid --> EndDetResult
    NoMove --> EndAITurn
    StopGame --> EndDetResult
    DrawNoBoard --> EmitResult

    %% Manual Controls
    UserClickPlace[User click "Place..."] --> OpenPlaceDialog[Mở PlaceDialog<br/>với prefill_cell]
    OpenPlaceDialog --> UserSelectCell[User chọn row, col]
    UserSelectCell --> ManualFreeze[sigFreeze.emit True]
    ManualFreeze --> SaveFrame[Lưu frame trước<br/>vào runs/ folder]
    SaveFrame --> ManualRobot[Robot sequence:<br/>pick→place→ref]
    ManualRobot --> ManualUnfreeze[sigFreeze.emit False]

    UserClickConnect[User click "Connect Robot"] --> InitRobot[Khởi tạo GridRobot<br/>Z_TABLE=130.0]
    InitRobot --> EnableVacuum[Enable vacuum buttons]

    UserClickStart[User click "Start Detect"] --> CheckYOLO{YOLO<br/>available?}
    CheckYOLO -->|Không| ShowError[Hiển thị error]
    CheckYOLO -->|Có| StartDetThread[det_thread.start<br/>det_thread.set_running True]

    UserClickVirtual[User click "Virtual Play"] --> OpenVirtualDialog[Mở VirtualGameDialog:<br/>Chơi vs AI<br/>không cần camera/robot]

    %% Styling
    classDef initStyle fill:#90EE90
    classDef cameraStyle fill:#87CEEB
    classDef detectionStyle fill:#DDA0DD
    classDef humanStyle fill:#FFD700
    classDef aiStyle fill:#FFA07A
    classDef endStyle fill:#FFB6C1
    classDef manualStyle fill:#98FB98

    class Start,Init,InitState,InitThreads,BuildUI initStyle
    class CamLoop,CaptureFrame,CheckCamOK,CamSleep,EmitFrame cameraStyle
    class DetLoop,FindBoard,BoardFound,ApplyShrink,DrawGrid,CropBoard,DetectPieces,ProcessBoxes,FilterStable,CreateItems,DrawDetections,EmitResult detectionStyle
    class ProcessHuman,CheckGameActive,ValidateMove,RegisterHuman,CheckWinHuman,StatusHumanDone humanStyle
    class AITurn,CheckAIGameActive,GetBoard,ComputeAI,CheckValidAI,FreezeOn,RobotCheck,RobotSequence,RegisterAI,CheckWinAI,FreezeOff aiStyle
    class HandleEndHumanWin,HandleEndAIWin,HandleEndDraw,GameEndCommon,SetInactive,ShowPopup,PlayAgain endStyle
    class UserClickPlace,OpenPlaceDialog,UserSelectCell,ManualFreeze,ManualRobot,UserClickConnect,UserClickStart,UserClickVirtual manualStyle
```

---

## Mô tả chi tiết các thành phần

### 1. **Khởi tạo (Màu xanh lá nhạt)**
- Khởi tạo `MainWindow` với tất cả state variables
- Tạo `GomokuGameState` (13x13), `MoveDetector`, `GomokuAIStrategy`
- Khởi tạo 2 worker threads: `CameraWorker` và `DetectionWorker`
- Xây dựng UI với toolbar, camera view, board table, controls

### 2. **Camera Thread (Màu xanh dương)**
- **Thread độc lập**, chạy liên tục
- Capture frames từ camera index 6
- Emit `newFrame` signal về main thread
- Không phụ thuộc vào detection state

### 3. **Detection Thread (Màu tím)**
- **Thread độc lập**, chỉ chạy khi `running_detect=True` và `frozen=False`
- **Bước 1**: Dùng YOLO `board_model` tìm board ROI
  - Tìm largest bounding box
  - Áp dụng shrink factor 0.99
- **Bước 2**: Crop ROI và dùng YOLO `piece_model` detect quân cờ
  - Confidence threshold: 0.35
  - Map class ID: 0→player1, else→player2
- **Bước 3**: Temporal filtering với 3 frames liên tiếp
  - Chỉ giữ detections xuất hiện ổn định qua 3 frames
- Emit `result` signal với annotated frame, ROI, detection items

### 4. **Main Thread - Detection Result Handler**
- Nhận detection results từ detection thread
- Cập nhật UI board table từ `game_state` (source of truth)
- **Không** overwrite game_state với tất cả detections
- Nếu auto_play enabled: dùng `MoveDetector` so sánh frames để tìm NEW moves

### 5. **Human Move Processing (Màu vàng)**
- `MoveDetector` phát hiện move mới bằng cách so sánh detections
- Validate move qua `game_state.validate_move`:
  - Kiểm tra bounds (0-12)
  - Kiểm tra ô trống
  - Kiểm tra đúng lượt (HUMAN_PLAYER=1)
- Nếu hợp lệ: `game_state.make_move` và kiểm tra thắng/thua
- Nếu game tiếp tục: trigger AI turn

### 6. **AI Turn Processing (Màu cam)**
- **Freeze detection** để robot hoạt động an toàn
- AI compute best move:
  - **Minimax**: depth 1-3 với heuristic evaluation
  - **AlphaZero**: neural network policy
- Nếu robot connected:
  - `pick_from_reserve()`: Lấy quân từ kho
  - `place_cell(row, col)`: Đặt quân lên bàn cờ
  - `robot_goto_ref()`: Về vị trí an toàn
- Register move vào `game_state` và kiểm tra thắng/thua
- **Unfreeze detection** để tiếp tục

### 7. **Game End Handler (Màu hồng)**
- Set `game_active = False`
- Hiển thị QMessageBox với kết quả
- Hỏi user "Play again?"
  - **Yes**: Reset game state và tiếp tục detection
  - **No**: Dừng game nhưng giữ detection running

### 8. **Manual Controls (Màu xanh lá)**
- **Place button**: Mở dialog chọn cell → robot place
- **Connect Robot**: Khởi tạo GridRobot
- **Start/Stop Detect**: Bật/tắt detection thread
- **Virtual Play**: Mở dialog chơi vs AI không cần camera/robot
- **Vacuum ON/OFF**: Điều khiển vacuum gripper

---

## Luồng dữ liệu chính

### Camera → Detection → Main Thread
```
Camera capture → newFrame signal → on_new_frame → update_frame(DetectionWorker)
→ YOLO detection → result signal → on_det_result → UI update
```

### Move Detection → Game Logic
```
Detection items → MoveDetector.detect_new_move → _process_human_move
→ game_state.make_move → check_win → _ai_turn → robot place
→ game_state.make_move → check_win
```

### Freeze Mechanism
```
sigFreeze.emit(True) → _apply_freeze → det_thread.set_running(False)
→ Robot operations (safe, no interference)
→ sigFreeze.emit(False) → det_thread.set_running(True)
```

---

## Temporal Filtering (Stability)

Detection worker sử dụng temporal filtering để tránh false positives:

1. Mỗi frame, lưu detections vào `_detection_history`
2. Giữ tối đa `DETECTION_STABILITY_FRAMES = 3` frames gần nhất
3. Chỉ emit detections xuất hiện trong **TẤT CẢ** 3 frames
4. Vẽ stable detections màu xanh/vàng, unstable màu xám

**Lợi ích**: Loại bỏ noise, chỉ nhận nước đi thực sự ổn định

---

## Thread Safety

- **Camera thread**: Emit frames qua signal (thread-safe)
- **Detection thread**:
  - Dùng `_lock` để protect `_last_frame`
  - `update_frame()` thread-safe với lock
- **Main thread**: Nhận signals và cập nhật UI (Qt event loop)
- **Freeze flag**: Dùng signal `sigFreeze` để sync giữa threads

---

## AI Strategy

### Minimax (Heuristic)
- Depth 1-3 configurable
- Heuristic evaluation function
- Alpha-beta pruning (nếu implemented)

### AlphaZero (Neural Network)
- Policy network cho move selection
- Không cần depth (single forward pass)
- Cần model file trained trước

---

## Robot Control Flow

```
pick_from_reserve()
  → Move to reserve position
  → Vacuum ON
  → Pick piece

place_cell(row, col)
  → Convert (row,col) to (X,Y) base coords
  → Move to position above cell
  → Lower Z
  → Vacuum OFF (release piece)
  → Raise Z

robot_goto_ref()
  → Move to safe reference position
  → REF_POSE = (214.2, -6.0, 439.9, -178.1, 0.7, -180.0)
```

---

## File Dependencies

- `grid_actions.py`: GridRobot class, cell_to_robot_xy
- `gomoku_game_state.py`: GomokuGameState, constants
- `gomoku_ai_strategy.py`: GomokuAIStrategy (Minimax/AlphaZero)
- `move_detector.py`: MoveDetector, MoveStatus
- `lastbc.pt`: YOLO board detection model
- `last.pt`: YOLO piece detection model

---

## Configuration Constants

```python
GRID_SIZE = 13                    # 13x13 board
CAMERA_INDEX = 6                  # Camera device
CONF_PIECE = 0.35                 # YOLO confidence
DETECTION_STABILITY_FRAMES = 3    # Temporal filtering
SHRINK_FACTOR = 0.99              # Board ROI shrink
CELL_SIZE = 60                    # UI cell size (pixels)
```

---

## Kết luận

Hệ thống hoạt động với **3 threads song song**:
1. **Camera Thread**: Liên tục capture frames
2. **Detection Thread**: YOLO detection khi enabled
3. **Main Thread**: UI, game logic, robot control

**Game loop**: Human move (detected) → Validate → AI compute → Robot place → Repeat

**Key features**:
- Temporal filtering cho stable detections
- Freeze mechanism cho robot safety
- Support cả Minimax và AlphaZero
- Virtual play mode để test AI
- Robust error handling và validation
