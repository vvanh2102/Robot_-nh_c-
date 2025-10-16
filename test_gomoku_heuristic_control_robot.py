import sys
import sqlite3
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                            QVBoxLayout, QLabel, QTabWidget, QFormLayout, QLineEdit, 
                            QColorDialog, QHBoxLayout, QGroupBox, QTableWidget, 
                            QTableWidgetItem, QMessageBox, QProgressBar, QSpinBox, 
                            QDoubleSpinBox, QGridLayout, QComboBox)  # Added QComboBox
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QPoint, QTimer, QElapsedTimer, QThread, pyqtSignal
import random
from datetime import datetime
import socket
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt

class GomokuBoard(QWidget):
    def __init__(self, parent=None, size=15):
        super().__init__(parent)
        self.size = size
        self.board = self.make_empty_board(size)
        self.colors = {'w': QColor(255, 255, 255), 'b': QColor(0, 0, 0)}
        self.cell_size = 60
        self.margin = 30
        self.move_history = []
        self.win = False
        self.status_label = None
        self.player_time = 0
        self.ai_time = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.start_time = None
        self.player_timer = QElapsedTimer()
        self.ai_timer = QElapsedTimer()
        self.human_vs_human = False
        self.current_player = 'b'
        self.history = []
        self.player_name = "Player"
        self.ai_name = "AI"
        self.start_time = None
        self.total_moves = 0
        self.winner = None
        self.player_name_label = QLabel("Player Name: ")
        self.player_time_label = QLabel("Player Time: 0 s")
        self.ai_time_label = QLabel("AI Time: 0 s")
        self.ai_label = QLabel("AI")
        self.parent_window = parent
        self.difficulty = "Easy"  # Add this line
        
        total_size = self.cell_size * size + 2 * self.margin
        self.setMinimumSize(total_size, total_size)
        self.setMaximumSize(total_size, total_size)
        self.setStyleSheet("background-color: #DEB887;")  # Burlywood color for board
        self.create_db()

    def create_db(self):
        conn = sqlite3.connect('gomoku_history.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS history
                     (id INTEGER PRIMARY KEY, player TEXT, move TEXT)''')
        conn.commit()
        conn.close()

    def make_empty_board(self, sz):
        return [[" "]*sz for _ in range(sz)]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw grid
        pen = QPen(Qt.GlobalColor.black, 1)
        painter.setPen(pen)

        for i in range(self.size):
            # Horizontal lines
            painter.drawLine(
                self.margin, self.margin + i * self.cell_size,
                self.margin + (self.size - 1) * self.cell_size, self.margin + i * self.cell_size
            )
            # Vertical lines
            painter.drawLine(
                self.margin + i * self.cell_size, self.margin,
                self.margin + i * self.cell_size, self.margin + (self.size - 1) * self.cell_size
            )

        # Draw stones
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] != ' ':
                    color = self.colors[self.board[i][j]]
                    painter.setBrush(color)
                    center_x = self.margin + j * self.cell_size
                    center_y = self.margin + i * self.cell_size
                    painter.drawEllipse(QPoint(center_x, center_y), 15, 15)

        if self.win:
            self.show_winner_line(painter)

        # Draw last move indicator
        if self.move_history:
            last_move = self.move_history[-1]
            last_x = self.margin + last_move[0] * self.cell_size
            last_y = self.margin + last_move[1] * self.cell_size
            painter.setBrush(QColor(255, 0, 0))  # Red color for last move
            painter.drawEllipse(QPoint(last_x, last_y), 5, 5)

    def mousePressEvent(self, event):
        if self.win:
            return

        if self.start_time is None:
            if not self.parent_window.player_name_input.text().strip():
                QMessageBox.warning(self, "Input Error", "Player name cannot be empty! Please save your name before starting the game.")
                return
            self.start_time = datetime.now()
            # QMessageBox.information(self, "Game Start", "Both players have pressed a point. The game has started!")

        x = round((event.position().x() - self.margin) / self.cell_size)
        y = round((event.position().y() - self.margin) / self.cell_size)

        if not self.is_in(y, x) or self.board[y][x] != ' ':
            return

        # Player's move
        if self.current_player == 'b':
            if self.player_timer.isValid():
                self.player_time += self.player_timer.elapsed() / 1000
            self.board[y][x] = 'b'
            self.move_history.append((x, y))
            self.update()
            self.player_time_label.setText(f"Player Time: {self.player_time:.2f} s")
            self.player_timer.invalidate()
            self.current_player = 'w'
        else:
            if self.ai_timer.isValid():
                self.ai_time += self.ai_timer.elapsed() / 1000
            self.board[y][x] = 'w'
            self.move_history.append((x, y))
            self.update()
            self.ai_time_label.setText(f"AI Time: {self.ai_time:.2f} s")
            self.ai_timer.invalidate()
            self.current_player = 'b'

        self.history.append((self.current_player, (x, y)))
        self.total_moves += 1
        self.save_history_to_db()

        game_res = self.is_win()
        if game_res in ["White won", "Black won", "Draw"]:
            self.win = True
            self.winner = game_res
            if not self.human_vs_human:
                self.winner_name = "AI" if game_res == "White won" else self.player_name
            else:
                self.winner_name = self.player_name if game_res == "White won" else self.ai_name
            if self.status_label:
                self.status_label.setText(f"Người chiến thắng: {self.winner_name }")
            self.update()
            self.save_game_data_to_db()
            return

        if not self.human_vs_human:
            # AI's move (white)
            self.ai_timer.start()
            ay, ax = self.best_move('w')
            if self.is_in(ay, ax) and self.board[ay][ax] == ' ':
                self.board[ay][ax] = 'w'
                self.move_history.append((ax, ay))
                self.update()
                self.ai_time += self.ai_timer.elapsed() / 1000
                self.ai_time_label.setText(f"AI Time: {self.ai_time:.2f} s")
                self.ai_timer.invalidate()

                self.history.append(('w', (ax, ay)))
                self.total_moves += 1
                self.save_history_to_db()

                game_res = self.is_win()
                if game_res in ["White won", "Black won", "Draw"]:
                    self.win = True
                    self.winner = game_res
                    self.winner_name = "AI" if game_res == "White won" else self.player_name
                    if self.status_label:
                        self.status_label.setText(f"Người chiến thắng: {self.winner_name}")
                    self.update()
                    self.save_game_data_to_db()
                else:
                    self.current_player = 'b'
                    self.player_timer.start()

        self.update_history()

    def is_in(self, y, x):
        return 0 <= y < len(self.board) and 0 <= x < len(self.board)

    def is_empty(self):
        return all(cell == ' ' for row in self.board for cell in row)

    def is_win(self):
        black = self.score_of_col('b')
        white = self.score_of_col('w')
        
        self.sum_sumcol_values(black)
        self.sum_sumcol_values(white)
        
        if 5 in black and black[5] == 1:
            return 'Black won'
        elif 5 in white and white[5] == 1:
            return 'White won'
            
        if sum(black.values()) == black[-1] and sum(white.values()) == white[-1] or not self.possible_moves():
            return 'Draw'
            
        return 'Continue playing'

    def march(self, y, x, dy, dx, length):
        yf = y + length*dy 
        xf = x + length*dx
        while not self.is_in(yf, xf):
            yf -= dy
            xf -= dx
        return yf, xf

    def score_ready(self, scorecol):
        sumcol = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, -1: {}}
        for key in scorecol:
            for score in scorecol[key]:
                if key in sumcol[score]:
                    sumcol[score][key] += 1
                else:
                    sumcol[score][key] = 1
        return sumcol

    def sum_sumcol_values(self, sumcol):
        for key in sumcol:
            if key == 5:
                sumcol[5] = int(1 in sumcol[5].values())
            else:
                sumcol[key] = sum(sumcol[key].values())

    def score_of_list(self, lis, col):
        blank = lis.count(' ')
        filled = lis.count(col)
        
        if blank + filled < 5:
            return -1
        elif blank == 5:
            return 0
        else:
            return filled

    def row_to_list(self, y, x, dy, dx, yf, xf):
        row = []
        while y != yf + dy or x != xf + dx:
            row.append(self.board[y][x])
            y += dy
            x += dx
        return row

    def score_of_row(self, cordi, dy, dx, cordf, col):
        colscores = []
        y, x = cordi
        yf, xf = cordf
        row = self.row_to_list(y, x, dy, dx, yf, xf)
        for start in range(len(row)-4):
            score = self.score_of_list(row[start:start+5], col)
            colscores.append(score)
        return colscores

    def score_of_col(self, col):
        f = len(self.board)
        scores = {(0,1): [], (-1,1): [], (1,0): [], (1,1): []}
        
        for start in range(f):
            scores[(0,1)].extend(self.score_of_row((start, 0), 0, 1, (start, f-1), col))
            scores[(1,0)].extend(self.score_of_row((0, start), 1, 0, (f-1, start), col))
            scores[(1,1)].extend(self.score_of_row((start, 0), 1, 1, (f-1, f-1-start), col))
            scores[(-1,1)].extend(self.score_of_row((start, 0), -1, 1, (0, start), col))
            
            if start + 1 < f:
                scores[(1,1)].extend(self.score_of_row((0, start+1), 1, 1, (f-2-start, f-1), col))
                scores[(-1,1)].extend(self.score_of_row((f-1, start+1), -1, 1, (start+1, f-1), col))
                
        return self.score_ready(scores)

    def score_of_col_one(self, col, y, x):
        scores = {(0,1): [], (-1,1): [], (1,0): [], (1,1): []}
        
        scores[(0,1)].extend(self.score_of_row(self.march(y, x, 0, -1, 4), 0, 1, self.march(y, x, 0, 1, 4), col))
        scores[(1,0)].extend(self.score_of_row(self.march(y, x, -1, 0, 4), 1, 0, self.march(y, x, 1, 0, 4), col))
        scores[(1,1)].extend(self.score_of_row(self.march(y, x, -1, -1, 4), 1, 1, self.march(y, x, 1, 1, 4), col))
        scores[(-1,1)].extend(self.score_of_row(self.march(y, x, -1, 1, 4), 1, -1, self.march(y, x, 1, -1, 4), col))
        
        return self.score_ready(scores)

    def possible_moves(self):
        taken = []
        directions = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (-1,-1), (-1,1), (1,-1)]
        cord = {}
        
        for i in range(len(self.board)):
            for j in range(len(self.board)):
                if self.board[i][j] != ' ':
                    taken.append((i,j))
                    
        for direction in directions:
            dy, dx = direction
            for coord in taken:
                y, x = coord
                for length in [1,2,3,4]:
                    move = self.march(y, x, dy, dx, length)
                    if move not in taken and move not in cord:
                        cord[move] = False
        return cord

    def TF34score(self, score3, score4):
        for key4 in score4:
            if score4[key4] >= 1:
                for key3 in score3:
                    if key3 != key4 and score3[key3] >= 2:
                        return True
        return False

    def stupid_score(self, col, anticol, y, x):
        M = 1000
        res, adv, dis = 0, 0, 0
        
        # Attack
        self.board[y][x] = col
        sumcol = self.score_of_col_one(col, y, x)       
        a = self.winning_situation(sumcol)
        adv += a * M
        self.sum_sumcol_values(sumcol)
        adv += sumcol[-1] + sumcol[1] + 4*sumcol[2] + 8*sumcol[3] + 16*sumcol[4]
        
        # Defense
        self.board[y][x] = anticol
        sumanticol = self.score_of_col_one(anticol, y, x)  
        d = self.winning_situation(sumanticol)
        dis += d * (M-100)
        self.sum_sumcol_values(sumanticol)
        dis += sumanticol[-1] + sumanticol[1] + 4*sumanticol[2] + 8*sumanticol[3] + 16*sumanticol[4]

        res = adv + dis
        
        self.board[y][x] = ' '
        return res

    def winning_situation(self, sumcol):
        if 1 in sumcol[5].values():
            return 5
        elif len(sumcol[4]) >= 2 or (len(sumcol[4]) >= 1 and max(sumcol[4].values()) >= 2):
            return 4
        elif self.TF34score(sumcol[3], sumcol[4]):
            return 4
        else:
            score3 = sorted(sumcol[3].values(), reverse=True)
            if len(score3) >= 2 and score3[0] >= score3[1] >= 2:
                return 3
        return 0

    def best_move(self, col):
        self.timer.stop()
        anticol = 'w' if col == 'b' else 'b'
        
        if self.is_empty():
            return (int(len(self.board) * random.random()), 
                   int(len(self.board[0]) * random.random()))
        
        moves = self.possible_moves()
        best_score = float('-inf')
        best_move = None
        
        for move in moves:
            y, x = move
            score = self.stupid_score(col, anticol, y, x)
            if score > best_score:
                best_score = score
                best_move = move

            # Add random factor for Easy mode
            if self.difficulty == "Easy" and random.random() < 0.3:  # 30% chance to make a random move
                possible_moves = list(moves.keys())
                if possible_moves:
                    best_move = random.choice(possible_moves)
        
        self.timer.start()
        return best_move if best_move is not None else (0, 0)

    def update_time(self):
        # This method is no longer needed for time calculation
        pass

    def show_winner_line(self, painter):
        pen = QPen(Qt.GlobalColor.red, 3)
        painter.setPen(pen)
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] != ' ':
                    for dy, dx in [(0, 1), (1, 0), (1, 1), (1, -1)]:
                        if self.check_winner_line(i, j, dy, dx):
                            start_x = self.margin + j * self.cell_size
                            start_y = self.margin + i * self.cell_size
                            end_x = self.margin + (j + 4 * dx) * self.cell_size
                            end_y = self.margin + (i + 4 * dy) * self.cell_size
                            painter.drawLine(start_x, start_y, end_x, end_y)
                            return

    def check_winner_line(self, y, x, dy, dx):
        color = self.board[y][x]
        for k in range(1, 5):
            ny, nx = y + k * dy, x + k * dx
            if not self.is_in(ny, nx) or self.board[ny][nx] != color:
                return False
        return True

    def restart_game(self):
        self.board = self.make_empty_board(self.size)
        self.move_history = []
        self.win = False
        self.start_time = None
        self.status_label.setText("Game in progress...")
        self.update()
        self.player_time = 0
        self.ai_time = 0
        self.player_timer.invalidate()
        self.ai_timer.invalidate()
        self.current_player = 'b'
        self.player_time_label.setText("Player Time: 0 s")
        self.ai_time_label.setText("AI Time: 0 s")
        self.history = []
        self.total_moves = 0
        self.winner = None
        self.winner_name = None
        self.save_history_to_db()
        self.update()
        self.update_history()

    def save_history_to_db(self):
        conn = sqlite3.connect('gomoku_history.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS history
                     (id INTEGER PRIMARY KEY, player TEXT, move TEXT)''')
        c.execute('DELETE FROM history')
        for move in self.history:
            c.execute('INSERT INTO history (player, move) VALUES (?, ?)', (move[0], str(move[1])))
        conn.commit()
        conn.close()
        self.parent().parent().update_history()

    def save_game_data_to_db(self):
        conn = sqlite3.connect('gomoku_history.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS game_data
                     (id INTEGER PRIMARY KEY, player_name TEXT, ai_name TEXT, winner TEXT, start_time TEXT, total_moves INTEGER, moves TEXT, player_time REAL, ai_time REAL)''')
        # c.execute('DELETE FROM game_data')
        c.execute('INSERT INTO game_data (player_name, ai_name, winner, start_time, total_moves, moves, player_time, ai_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                  (self.player_name, self.ai_name , self.winner_name, self.start_time.strftime("%Y-%m-%d %H:%M:%S"), self.total_moves, str(self.history), self.player_time, self.ai_time))
        conn.commit()
        conn.close()

    def update_history(self):
        self.parent().parent().update_history()

class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.batch_norm1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.batch_norm2 = nn.BatchNorm2d(out_channels)
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        out = torch.relu(self.batch_norm1(self.conv1(x)))
        out = self.batch_norm2(self.conv2(out))
        out += self.shortcut(x)
        out = torch.relu(out)
        return out

class GomokuModel(nn.Module):
    def __init__(self):
        super(GomokuModel, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, padding=1)
        self.res_block1 = ResidualBlock(32, 64)
        self.res_block2 = ResidualBlock(64, 64)
        self.fc1 = nn.Linear(64 * 15 * 15, 512)
        self.fc2 = nn.Linear(512, 225)
    
    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = self.res_block1(x)
        x = self.res_block2(x)
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x.view(-1, 15, 15)

class RobotThread(QThread):
    position_updated = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, ip, port):
        super().__init__()
        self.ip = ip
        self.port = port
        self.socket = None
        self.running = False
        self.auto_mode = True  # Add auto mode flag

    def set_mode(self, auto):
        self.auto_mode = auto
        if self.socket:
            self.send_command(f"MODE {'AUTO' if auto else 'MANUAL'}")

    def connect_robot(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.ip, self.port))
            self.running = True
            self.connection_status.emit(True)
            self.start()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def disconnect_robot(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connection_status.emit(False)

    def run(self):
        while self.running:
            try:
                data = self.socket.recv(1024).decode()
                if data:
                    self.position_updated.emit(data)
            except Exception as e:
                self.error_occurred.emit(str(e))
                self.disconnect_robot()

    def send_command(self, command):
        if self.socket:
            try:
                self.socket.sendall(command.encode())
            except Exception as e:
                self.error_occurred.emit(str(e))

class GomokuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Caro Game Control Robot")
        self.pos_inputs = {}  # Initialize pos_inputs dictionary
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        self.board_widget = GomokuBoard(self)
        layout.addWidget(self.board_widget)
        
        right_panel = QVBoxLayout()
        layout.addLayout(right_panel)
        
        tab_widget = QTabWidget()
        right_panel.addWidget(tab_widget)
        
        main_tab = QWidget()
        main_layout = QVBoxLayout(main_tab)
        
        form_layout = QFormLayout()
        self.player_name_input = QLineEdit()
        form_layout.addRow("Player Name:", self.player_name_input)
        
        self.player2_name_input = QLineEdit()
        form_layout.addRow("Player 2 Name:", self.player2_name_input)
        
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        form_layout.addRow("Point Color:", self.color_button)
        
        self.mode_button = QPushButton("Switch to Human vs. Human")
        self.mode_button.clicked.connect(self.switch_mode)
        form_layout.addRow("Game Mode:", self.mode_button)
        
        self.save_names_button = QPushButton("Save Names")
        self.save_names_button.clicked.connect(self.save_player_names)
        form_layout.addRow(self.save_names_button)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Easy", "Hard"])
        self.difficulty_combo.currentTextChanged.connect(self.change_difficulty)
        form_layout.addRow("Difficulty:", self.difficulty_combo)
        
        main_layout.addLayout(form_layout)
        
        self.status_label = QLabel("Game in progress...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 34px; font-weight: bold;")
        self.board_widget.status_label = self.status_label
        main_layout.addWidget(self.status_label)
        
        main_layout.addWidget(self.board_widget.player_name_label)
        main_layout.addWidget(self.board_widget.player_time_label)
        main_layout.addWidget(self.board_widget.ai_time_label)
        main_layout.addWidget(self.board_widget.ai_label)
        
        restart_button = QPushButton("Restart Game")
        restart_button.clicked.connect(self.restart_game)
        main_layout.addWidget(restart_button)
        
        tab_widget.addTab(main_tab, "Main")
        
        all_history_tab = QWidget()
        all_history_layout = QVBoxLayout(all_history_tab)
        self.all_history_label = QLabel("All Game History")
        all_history_layout.addWidget(self.all_history_label)
        
        self.all_history_table = QTableWidget()
        self.all_history_table.setColumnCount(8)
        self.all_history_table.setHorizontalHeaderLabels(["Player", "AI/Player 2", "Move", "Winner", "Start Time", "Total Moves", "Player 1 Time", "Player 2 Time"])
        all_history_layout.addWidget(self.all_history_table)
        
        self.show_history_button = QPushButton("Show History")
        self.show_history_button.clicked.connect(self.load_all_history_from_db)
        all_history_layout.addWidget(self.show_history_button)
        
        self.clear_db_button = QPushButton("Clear Database")
        self.clear_db_button.clicked.connect(self.clear_database)
        all_history_layout.addWidget(self.clear_db_button)
        
        tab_widget.addTab(all_history_tab, "All History")
        
        config_tab = self.create_config_tab()
        tab_widget.addTab(config_tab, "Robot Config")
        
        tab_widget.addTab(self.create_train_tab(), "Train MCTS")
        
        self.load_history_from_db()
        self.load_all_history_from_db()
        
        self.apply_modern_ui()

    def apply_modern_ui(self):
        self.setStyleSheet("""
            QLabel {
                font-size: 20px;
                color: #333;

                padding: 5px;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLineEdit {
                padding: 8px;
                font-size: 16px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTableWidget {
                font-size: 14px;
                border: 1px solid #ccc;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: 1px solid #ddd;
                font-size: 14px;
            }
        """)
        self.status_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px; border-radius: 5px; background-color: #f0f0f0;")

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.board_widget.colors['b'] = color

    def switch_mode(self):
        if self.board_widget.human_vs_human:
            self.board_widget.human_vs_human = False
            self.mode_button.setText("Switch to Human vs. Human")
        else:
            self.board_widget.human_vs_human = True
            self.mode_button.setText("Switch to Human vs. AI")

    def save_player_names(self):
        player_name = self.player_name_input.text().strip()
        if not player_name:
            QMessageBox.warning(self, "Input Error", "Player name cannot be empty!")
            return
        
        self.board_widget.player_name = player_name
        self.board_widget.ai_name = self.player2_name_input.text().strip() if self.board_widget.human_vs_human else "AI"
        self.board_widget.player_name_label.setText(f"Player Name: {self.board_widget.player_name}")
        self.board_widget.ai_label.setText(f"Player 2: {self.board_widget.ai_name}")

    def change_difficulty(self, difficulty):
        self.board_widget.difficulty = difficulty
        QMessageBox.information(self, "Difficulty Changed", f"Game difficulty set to {difficulty}")

    def update_history(self):
        # This method is no longer needed since the history tab is removed
        pass

    def restart_game(self):
        self.board_widget.restart_game()
        self.update_history()

    def load_history_from_db(self):
        conn = sqlite3.connect('gomoku_history.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS history
                     (id INTEGER PRIMARY KEY, player TEXT, move TEXT)''')
        c.execute('SELECT player, move FROM history')
        self.board_widget.history = [(row[0], eval(row[1])) for row in c.fetchall()]
        conn.close()
        self.update_history()

    def load_all_history_from_db(self):
        conn = sqlite3.connect('gomoku_history.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS game_data
                     (id INTEGER PRIMARY KEY, player_name TEXT, ai_name TEXT, winner TEXT, start_time TEXT, total_moves INTEGER, moves TEXT, player_time REAL, ai_time REAL)''')
        c.execute('SELECT player_name, ai_name, winner, start_time, total_moves, moves, player_time, ai_time FROM game_data')
        all_history = c.fetchall()
        conn.close()
        
        all_history.reverse()  # Reverse the list of history games
        
        self.all_history_table.setRowCount(len(all_history))
        for row_idx, (player_name, ai_name, winner, start_time, total_moves, moves, player_time, ai_time) in enumerate(all_history):
            self.all_history_table.setItem(row_idx, 0, QTableWidgetItem(player_name))
            self.all_history_table.setItem(row_idx, 1, QTableWidgetItem(ai_name))
            self.all_history_table.setItem(row_idx, 2, QTableWidgetItem(moves))
            self.all_history_table.setItem(row_idx, 3, QTableWidgetItem(winner))
            self.all_history_table.setItem(row_idx, 4, QTableWidgetItem(start_time))
            self.all_history_table.setItem(row_idx, 5, QTableWidgetItem(str(total_moves)))
            self.all_history_table.setItem(row_idx, 6, QTableWidgetItem(f"{player_time:.2f} s"))
            self.all_history_table.setItem(row_idx, 7, QTableWidgetItem(f"{ai_time:.2f} s"))

    def clear_database(self):
        conn = sqlite3.connect('gomoku_history.db')
        c = conn.cursor()
        c.execute('DELETE FROM history')
        c.execute('DELETE FROM game_data')
        conn.commit()
        conn.close()
        self.load_all_history_from_db()
        self.update_history()
        self.board_widget.restart_game()

    def connect_to_robot(self):
        ip = self.robot_ip_input.text()
        port = self.robot_port_input.text()
        # Add logic to connect to the robot using the provided IP and port
        success = self.try_connect_to_robot(ip, port)
        if success:
            self.connect_button.setStyleSheet("background-color: #28a745; color: white;")
            self.connect_button.setText("Disconnect")
            self.connect_button.clicked.disconnect()
            self.connect_button.clicked.connect(self.disconnect_from_robot)
            QMessageBox.information(self, "Connection Successful", f"Connected to robot at {ip}:{port}")
        else:
            self.connect_button.setStyleSheet("background-color: #dc3545; color: white;")
            self.connect_button.setText("Reconnect")
            QMessageBox.warning(self, "Connection Failed", f"Failed to connect to robot at {ip}:{port}")

    def disconnect_from_robot(self):
        # Add logic to disconnect from the robot
        self.connect_button.setStyleSheet("background-color: #007BFF; color: white;")
        self.connect_button.setText("Connect to Robot")
        self.connect_button.clicked.disconnect()
        self.connect_button.clicked.connect(self.connect_to_robot)
        QMessageBox.information(self, "Disconnected", "Disconnected from the robot")

    def try_connect_to_robot(self, ip, port):
        try:
            # Create a socket object
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)  # Set timeout to 5 seconds
            # Connect to the robot
            s.connect((ip, int(port)))
            s.close()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def create_train_tab(self):
        train_tab = QWidget()
        train_layout = QVBoxLayout(train_tab)
        
        self.train_button = QPushButton("Train MCTS Model")
        self.train_button.clicked.connect(self.train_mcts_model)
        train_layout.addWidget(self.train_button)
        
        self.save_model_button = QPushButton("Save Model")
        self.save_model_button.clicked.connect(self.save_model)
        train_layout.addWidget(self.save_model_button)
        
        self.show_loss_button = QPushButton("Show Training Loss")
        self.show_loss_button.clicked.connect(self.show_training_loss)
        train_layout.addWidget(self.show_loss_button)
        
        self.progress_bar = QProgressBar()
        train_layout.addWidget(self.progress_bar)
        
        self.batch_size_input = QLineEdit()
        train_layout.addWidget(QLabel("Batch Size:"))
        train_layout.addWidget(self.batch_size_input)
        
        self.epochs_input = QLineEdit()
        train_layout.addWidget(QLabel("Number of Epochs:"))
        train_layout.addWidget(self.epochs_input)
        
        return train_tab

    def load_model_for_prediction(self):
        try:
            self.model = GomokuModel()
            self.model.load_state_dict(torch.load('gomoku_model.pth'))
            self.model.eval()
            QMessageBox.information(self, "Model Loaded", "The model has been loaded successfully for prediction.")
        except Exception as e:
            QMessageBox.warning(self, "Loading Failed", f"Failed to load the model: {e}")

    def train_mcts_model(self):
        self.progress_bar.setValue(0)
        self.model = GomokuModel()
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        self.losses = []
        
        batch_size = int(self.batch_size_input.text())
        epochs = int(self.epochs_input.text())
        
        # Add logic to train the MCTS model using data from the database
        # Update the progress bar as the training progresses
        total_steps = epochs * 100  # Example total steps
        for step in range(total_steps):
            # Perform training step
            # Example: dummy training loop
            self.optimizer.zero_grad()
            inputs = torch.randn(batch_size, 1, 15, 15)  # Dummy input
            targets = torch.randn(batch_size, 15, 15)  # Dummy target
            outputs = self.model(inputs)
            loss = self.criterion(outputs, targets)
            loss.backward()
            self.optimizer.step()
            
            self.losses.append(loss.item())
            self.progress_bar.setValue(int((step + 1) * 100 / total_steps))
        QMessageBox.information(self, "Training Complete", "The MCTS model has been trained successfully.")

    def save_model(self):
        torch.save(self.model.state_dict(), 'gomoku_model.pth')
        QMessageBox.information(self, "Model Saved", "The MCTS model has been saved successfully.")

    def show_training_loss(self):
        plt.plot(self.losses)
        plt.xlabel('Training Steps')
        plt.ylabel('Loss')
        plt.title('Training Loss Over Time')
        plt.show()

    def create_config_tab(self):
        config_tab = QWidget()
        config_layout = QVBoxLayout(config_tab)

        # Connection group
        connection_group = QGroupBox("Robot Connection Settings")
        connection_layout = QHBoxLayout()
        
        self.robot_ip_input = QLineEdit("192.168.1.100")
        self.robot_port_input = QSpinBox()
        self.robot_port_input.setRange(1, 65535)
        self.robot_port_input.setValue(502)
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.toggle_robot_connection)

        connection_layout.addWidget(QLabel("IP:"))
        connection_layout.addWidget(self.robot_ip_input)
        connection_layout.addWidget(QLabel("Port:"))
        connection_layout.addWidget(self.robot_port_input)
        connection_layout.addWidget(self.connect_button)
        connection_group.setLayout(connection_layout)
        config_layout.addWidget(connection_group)

        # Mode control group
        mode_group = QGroupBox("Operation Mode")
        mode_layout = QHBoxLayout()
        
        self.mode_button = QPushButton("Switch to Manual Mode")
        self.mode_button.setCheckable(True)
        self.mode_button.clicked.connect(self.toggle_robot_mode)
        self.mode_button.setEnabled(False)
        
        mode_layout.addWidget(self.mode_button)
        mode_group.setLayout(mode_layout)
        config_layout.addWidget(mode_group)

        # Manual control group
        self.manual_group = QGroupBox("Manual Control")
        manual_layout = QVBoxLayout()

        # Jog control buttons
        jog_layout = QGridLayout()
        jog_buttons = {
            'X+': (0, 2), 'X-': (0, 0),
            'Y+': (0, 1), 'Y-': (2, 1),
            'Z+': (1, 2), 'Z-': (1, 0),
            'R+': (2, 2), 'R-': (2, 0)
        }

        for label, pos in jog_buttons.items():
            btn = QPushButton(label)
            btn.setEnabled(False)
            btn.pressed.connect(lambda l=label: self.start_jog(l))
            btn.released.connect(self.stop_jog)
            self.pos_inputs[f'jog_{label}'] = btn
            jog_layout.addWidget(btn, pos[0], pos[1])

        manual_layout.addLayout(jog_layout)
        
        # Speed control
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed:"))
        self.speed_input = QSpinBox()
        self.speed_input.setRange(1, 100)
        self.speed_input.setValue(50)
        self.speed_input.setEnabled(False)
        speed_layout.addWidget(self.speed_input)
        manual_layout.addLayout(speed_layout)

        self.manual_group.setLayout(manual_layout)
        self.manual_group.setEnabled(False)
        config_layout.addWidget(self.manual_group)

        # Position control group 
        position_group = QGroupBox("Position Control")
        position_layout = QVBoxLayout()
        
        # Add position input spinboxes
        position_inputs = QHBoxLayout()
        for axis in ['X', 'Y', 'Z', 'R']:
            axis_layout = QVBoxLayout()
            axis_layout.addWidget(QLabel(f"{axis}:"))
            spin = QDoubleSpinBox()
            spin.setRange(-1000, 1000)
            spin.setSingleStep(1)
            self.pos_inputs[axis] = spin
            axis_layout.addWidget(spin)
            position_inputs.addLayout(axis_layout)
        
        position_layout.addLayout(position_inputs)
        
        # Add move to position button
        self.move_abs_button = QPushButton("Move to Position")
        self.move_abs_button.clicked.connect(self.move_robot_absolute)
        self.move_abs_button.setEnabled(False)
        position_layout.addWidget(self.move_abs_button)
        
        position_group.setLayout(position_layout)
        config_layout.addWidget(position_group)

        # ...rest of existing config tab code...

        self.robot_thread = None
        self.set_robot_connected_state(False)

        return config_tab

    def toggle_robot_mode(self):
        if not self.robot_thread:
            return
            
        auto_mode = not self.mode_button.isChecked()
        self.mode_button.setText("Switch to " + ("Manual Mode" if auto_mode else "Auto Mode"))
        
        # Change button color based on mode
        if auto_mode:
            self.mode_button.setStyleSheet("""
                QPushButton {
                    background-color: #007BFF;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 16px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
        else:
            self.mode_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 16px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
        
        self.manual_group.setEnabled(not auto_mode)
        self.speed_input.setEnabled(not auto_mode)
        for btn in self.pos_inputs.values():
            if isinstance(btn, QPushButton) and btn.text().startswith(('X', 'Y', 'Z', 'R')):
                btn.setEnabled(not auto_mode)
        
        self.robot_thread.set_mode(auto_mode)

    def set_robot_connected_state(self, connected):
        self.connect_button.setText("Disconnect" if connected else "Connect")
        self.mode_button.setEnabled(connected)
        self.move_abs_button.setEnabled(connected)
        if not connected:
            self.manual_group.setEnabled(False)
            self.mode_button.setChecked(False)
            self.mode_button.setText("Switch to Manual Mode")
        self.statusBar().showMessage('Connected to Robot' if connected else 'Disconnected from Robot')

    def move_robot_absolute(self):
        if not self.robot_thread:
            return
            
        x = self.pos_inputs['X'].value()
        y = self.pos_inputs['Y'].value()
        z = self.pos_inputs['Z'].value()
        r = self.pos_inputs['R'].value()
        
        command = f"MOVE X{x} Y{y} Z{z} R{r}"
        self.robot_thread.send_command(command)

    def start_jog(self, direction):
        if not self.robot_thread or self.robot_thread.auto_mode:
            return
            
        speed = self.speed_input.value()
        command = f"JOG {direction} {speed}"
        self.robot_thread.send_command(command)

    def stop_jog(self):
        if not self.robot_thread or self.robot_thread.auto_mode:
            return
            
        self.robot_thread.send_command("STOP")

    def update_robot_position(self, position):
        self.position_label.setText(f"Current Position: {position}")

    def show_robot_error(self, message):
        QMessageBox.critical(self, "Robot Error", message)

    def closeEvent(self, event):
        if self.robot_thread:
            self.robot_thread.disconnect_robot()
        super().closeEvent(event)

    def toggle_robot_connection(self):
        """Handle robot connection toggling"""
        if not hasattr(self, 'robot_thread') or self.robot_thread is None:
            # Try to connect
            ip = self.robot_ip_input.text()
            port = self.robot_port_input.value()
            self.robot_thread = RobotThread(ip, port)
            self.robot_thread.position_updated.connect(self.update_robot_position)
            self.robot_thread.connection_status.connect(self.set_robot_connected_state)
            self.robot_thread.error_occurred.connect(self.show_robot_error)
            self.robot_thread.connect_robot()
        else:
            # Disconnect
            self.robot_thread.disconnect_robot()
            self.robot_thread = None
            self.set_robot_connected_state(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GomokuWindow()
    window.showMaximized()
    window.show()
    sys.exit(app.exec())