# Luồng Hoạt Động Chi Tiết - Hệ Thống Robot Đánh Cờ Gomoku

## 🔄 Main Game Loop Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION START                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  1. Initialize Components         │
        │     • Camera Worker               │
        │     • Detection Worker            │
        │     • Robot Connection            │
        │     • Game State Manager          │
        │     • AI Strategy Manager         │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  2. User Actions                   │
        │     • Connect Robot               │
        │     • Start Detection              │
        │     • Click "Start Game"           │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────┐
        │  3. AUTO PLAY MODE ACTIVATED      │
        │     game_active = True             │
        │     auto_play_mode = True         │
        └───────────────────────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────────────────────┐
        │              MAIN GAME LOOP (Continuous)            │
        └─────────────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  STEP A: CAMERA & DETECTION                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ CameraWorker captures frame                          │   │
│  │   ↓                                                   │   │
│  │ DetectionWorker processes frame                      │   │
│  │   ↓                                                   │   │
│  │ Detects board ROI + pieces                           │   │
│  │   ↓                                                   │   │
│  │ Emits: (annotated_frame, roi, detection_items)      │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────┐
│  STEP B: PROCESS DETECTION RESULTS                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ on_det_result() called                              │   │
│  │   ↓                                                   │   │
│  │ Build board_state from detection_items               │   │
│  │   ↓                                                   │   │
│  │ IF auto_play_mode AND game_active:                   │   │
│  │   ↓                                                   │   │
│  │   Compare with last_board_state                      │   │
│  │   ↓                                                   │   │
│  │   Detect new move (if any)                           │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ New Move       │
                    │ Detected?      │
                    └───────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
              YES                      NO
                │                       │
                ▼                       ▼
┌───────────────────────────┐  ┌──────────────────────┐
│ STEP C: VALIDATE MOVE     │  │ Wait for next frame  │
│ ┌─────────────────────┐   │  │ (Loop back to A)     │
│ │ Validate:           │   │  └──────────────────────┘
│ │ • Position valid?   │   │
│ │ • Cell empty?       │   │
│ │ • Correct turn?     │   │
│ └─────────────────────┘   │
└───────────────────────────┘
                │
        ┌───────┴───────┐
        │               │
      VALID          INVALID
        │               │
        ▼               ▼
┌───────────────┐  ┌──────────────┐
│ Update Game   │  │ Ignore move  │
│ State:        │  │ Log warning  │
│ • board_state │  │ Continue     │
│ • move_history│  └──────────────┘
│ • current_turn│
└───────────────┘
        │
        ▼
┌───────────────────────────┐
│ STEP D: CHECK GAME STATUS │
│ ┌─────────────────────┐   │
│ │ Check win condition:│   │
│ │ • Human won?        │   │
│ │ • AI won?           │   │
│ │ • Draw?             │   │
│ │ • Continue?         │   │
│ └─────────────────────┘   │
└───────────────────────────┘
        │
    ┌───┴───┐
    │       │
  GAME    CONTINUE
   END       │
    │        ▼
    │  ┌──────────────────────────┐
    │  │ STEP E: AI TURN           │
    │  │ ┌──────────────────────┐  │
    │  │ │ Freeze detection     │  │
    │  │ │   ↓                   │  │
    │  │ │ AI calculates move:   │  │
    │  │ │   • Minimax search    │  │
    │  │ │   • OR Alpha-Zero    │  │
    │  │ │   ↓                   │  │
    │  │ │ Get (row, col)        │  │
    │  │ └──────────────────────┘  │
    │  └──────────────────────────┘
    │        │
    │        ▼
    │  ┌──────────────────────────┐
    │  │ STEP F: ROBOT EXECUTION   │
    │  │ ┌──────────────────────┐  │
    │  │ │ pick_from_reserve()   │  │
    │  │ │   ↓                   │  │
    │  │ │ place_cell(row, col)  │  │
    │  │ │   ↓                   │  │
    │  │ │ robot_goto_ref()      │  │
    │  │ └──────────────────────┘  │
    │  └──────────────────────────┘
    │        │
    │        ▼
    │  ┌──────────────────────────┐
    │  │ Update Game State         │
    │  │ • board_state[row][col]=2 │
    │  │ • move_history.append()    │
    │  │ • current_turn = 1        │
    │  └──────────────────────────┘
    │        │
    │        ▼
    │  ┌──────────────────────────┐
    │  │ Check Game Status Again   │
    │  │ (Same as STEP D)          │
    │  └──────────────────────────┘
    │        │
    │        ▼
    │  ┌──────────────────────────┐
    │  │ Unfreeze detection        │
    │  │ Return to STEP A          │
    │  └──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│ GAME END HANDLING        │
│ • Show winner message     │
│ • Save game history       │
│ • Reset board (optional)  │
└──────────────────────────┘
```

## 📊 State Machine Diagram

```
                    ┌─────────────┐
                    │   IDLE      │
                    │ (Not started)│
                    └─────────────┘
                           │
                    [Start Game]
                           │
                           ▼
                    ┌─────────────┐
                    │  WAITING    │
                    │  (Human)    │◄────────┐
                    └─────────────┘          │
                           │                 │
                    [Human Move]             │
                    Detected                 │
                           │                 │
                           ▼                 │
                    ┌─────────────┐          │
                    │  VALIDATING │          │
                    │   MOVE      │          │
                    └─────────────┘          │
                           │                 │
                    ┌──────┴──────┐          │
                    │             │          │
                VALID         INVALID        │
                    │             │          │
                    ▼             ▼          │
            ┌─────────────┐  ┌──────────┐   │
            │  CHECKING   │  │  IGNORE  │   │
            │    WIN      │  │  MOVE    │───┘
            └─────────────┘  └──────────┘
                    │
            ┌───────┴───────┐
            │               │
         GAME END      CONTINUE
            │               │
            ▼               ▼
    ┌─────────────┐  ┌─────────────┐
    │   ENDED     │  │  AI TURN    │
    │ (Win/Draw)  │  │  (Thinking) │
    └─────────────┘  └─────────────┘
                           │
                    [AI Calculates]
                           │
                           ▼
                    ┌─────────────┐
                    │  ROBOT     │
                    │  MOVING    │
                    └─────────────┘
                           │
                    [Move Complete]
                           │
                           ▼
                    ┌─────────────┐
                    │  CHECKING   │
                    │    WIN      │
                    └─────────────┘
                           │
                    ┌───────┴───────┐
                    │               │
                 GAME END      CONTINUE
                    │               │
                    ▼               │
            ┌─────────────┐         │
            │   ENDED     │         │
            └─────────────┘         │
                                    │
                                    ┘
                            (Loop back)
```

## 🔍 Move Detection Logic

```
┌─────────────────────────────────────────┐
│  Previous Detection:                     │
│  board_state_prev[13][13]               │
│  = {0, 1, 2}                             │
└─────────────────────────────────────────┘
                    │
                    │ Compare
                    ▼
┌─────────────────────────────────────────┐
│  Current Detection:                      │
│  board_state_curr[13][13]               │
│  = {0, 1, 2}                             │
└─────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Find Differences:    │
        │  diff = curr - prev   │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  For each (row, col): │
        │  IF diff[row][col] != 0:│
        │    → New piece placed │
        │    → Record position  │
        │    → Determine player  │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Validate:            │
        │  • Only ONE new piece? │
        │  • Correct player?    │
        │  • Valid position?     │
        └───────────────────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Return Move:  │
            │ (row, col,   │
            │  player_id)  │
            └───────────────┘
```

## 🤖 Robot Execution Sequence

```
┌─────────────────────────────────────────┐
│  AI Calculated Move: (row=6, col=7)      │
└─────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 1. Freeze Detection   │
        │    frozen = True      │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 2. Pick from Reserve  │
        │    pick_from_reserve()│
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 3. Move to Position   │
        │    place_cell(6, 7)   │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 4. Return to Safe     │
        │    robot_goto_ref()   │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 5. Update Game State  │
        │    board[6][7] = 2    │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 6. Unfreeze Detection │
        │    frozen = False    │
        └───────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ 7. Wait for Human Move│
        │    (Back to detection) │
        └───────────────────────┘
```

## ⚠️ Error Handling Flow

```
┌─────────────────────────────────────────┐
│  ERROR DETECTED                          │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    DETECTION              ROBOT ERROR
    ERROR                      │
        │                       │
        ▼                       ▼
┌───────────────┐      ┌───────────────┐
│ • No board    │      │ • Pick failed  │
│   detected    │      │ • Place failed │
│ • Low conf    │      │ • Timeout      │
│ • Invalid ROI │      │ • Connection   │
└───────────────┘      └───────────────┘
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │ Error Handler:        │
        │ • Log error            │
        │ • Show message         │
        │ • Retry (if possible)   │
        │ • Fallback action      │
        └───────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    RECOVERABLE          CRITICAL
        │                       │
        ▼                       ▼
┌───────────────┐      ┌───────────────┐
│ Continue game │      │ Stop game     │
│ Wait retry    │      │ Show error    │
│ Skip turn     │      │ Require fix   │
└───────────────┘      └───────────────┘
```

