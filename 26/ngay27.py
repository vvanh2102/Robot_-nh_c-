import math
import random
depth_max = 4
class GomokuHeuristic:
    # Khởi tạo class GomokuHeuristic với bàn cờ và kích thước bàn cờ
    def __init__(self, board, size):
        self.board = board  # Bàn cờ (list 2D)
        self.size = size    # Kích thước bàn cờ (ví dụ: 15x15)

    # Kiểm tra xem tọa độ (y, x) có nằm trong phạm vi bàn cờ hay không
    def is_in(self, y, x):
        return 0 <= y < self.size and 0 <= x < self.size

    # Di chuyển từ vị trí (y, x) theo hướng (dy, dx) với khoảng cách length
    def march(self, y, x, dy, dx, length):
        yf = y + length * dy  # Tính toán vị trí cuối cùng theo hướng dy
        xf = x + length * dx  # Tính toán vị trí cuối cùng theo hướng dx
        # Nếu vị trí cuối cùng nằm ngoài bàn cờ, điều chỉnh lại
        while not self.is_in(yf, xf):
            yf -= dy
            xf -= dx
        return yf, xf  # Trả về vị trí hợp lệ

    # Tổng hợp điểm số từ scorecol vào sumcol
    def score_ready(self, scorecol):
        sumcol = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, -1: {}}
        for key in scorecol:
            for score in scorecol[key]:
                if key in sumcol[score]:
                    sumcol[score][key] += 1  # Tăng giá trị nếu key đã tồn tại
                else:
                    sumcol[score][key] = 1  # Khởi tạo giá trị nếu key chưa tồn tại
        return sumcol

    # Tính tổng giá trị của các điểm số trong sumcol
    def sum_sumcol_values(self, sumcol):
        for key in sumcol:
            if key == 5:
                sumcol[5] = int(1 in sumcol[5].values())  # Kiểm tra xem có ít nhất một giá trị 1 hay không
            else:
                sumcol[key] = sum(sumcol[key].values())  # Tính tổng các giá trị

    # Tính điểm số của một danh sách các ô (lis) dựa trên số lượng ô trống và ô được đánh bởi người chơi
    def score_of_list(self, lis, col):
        blank = lis.count(' ')  # Đếm số ô trống
        filled = lis.count(col)  # Đếm số ô được đánh bởi người chơi
        if blank + filled < 5:  # Nếu không đủ 5 ô liên tiếp
            return -1
        elif blank == 5:  # Nếu tất cả đều là ô trống
            return 0
        else:
            return filled  # Trả về số ô được đánh bởi người chơi

    # Tạo một danh sách các ô từ vị trí (y, x) đến (yf, xf) theo hướng (dy, dx)
    def row_to_list(self, y, x, dy, dx, yf, xf):
        row = []
        while y != yf + dy or x != xf + dx:  # Lặp cho đến khi đến vị trí cuối cùng
            if self.is_in(y, x):
                row.append(self.board[y][x])  # Thêm ô vào danh sách từ list 2D
            else:
                row.append(' ')  # Nếu nằm ngoài board thì thêm khoảng trắng
            y += dy  # Di chuyển theo hướng dy
            x += dx  # Di chuyển theo hướng dx
        return row

    # Tính điểm số cho một hàng (hoặc cột, đường chéo) từ vị trí bắt đầu đến vị trí kết thúc
    def score_of_row(self, cordi, dy, dx, cordf, col):
        colscores = []
        y, x = cordi  # Vị trí bắt đầu
        yf, xf = cordf  # Vị trí kết thúc
        row = self.row_to_list(y, x, dy, dx, yf, xf)  # Tạo danh sách các ô
        for start in range(len(row) - 4):  # Duyệt qua từng đoạn 5 ô liên tiếp
            score = self.score_of_list(row[start:start + 5], col)  # Tính điểm số
            colscores.append(score)  # Thêm điểm số vào danh sách
        return colscores

    # Tính điểm số cho tất cả các hàng, cột và đường chéo trên bàn cờ
    def score_of_col(self, col):
        f = self.size
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}
        for start in range(f):
            scores[(0, 1)].extend(self.score_of_row((start, 0), 0, 1, (start, f - 1), col))  # Hàng ngang
            scores[(1, 0)].extend(self.score_of_row((0, start), 1, 0, (f - 1, start), col))  # Hàng dọc
            scores[(1, 1)].extend(self.score_of_row((start, 0), 1, 1, (f - 1, f - 1 - start), col))  # Đường chéo chính
            scores[(-1, 1)].extend(self.score_of_row((start, 0), -1, 1, (0, start), col))  # Đường chéo phụ
            if start + 1 < f:
                scores[(1, 1)].extend(self.score_of_row((0, start + 1), 1, 1, (f - 2 - start, f - 1), col))  # Đường chéo chính (tiếp)
                scores[(-1, 1)].extend(self.score_of_row((f - 1, start + 1), -1, 1, (start + 1, f - 1), col))  # Đường chéo phụ (tiếp)
        return self.score_ready(scores)  # Tổng hợp điểm số

    # Tính điểm số cho một ô cụ thể (y, x)
    def score_of_col_one(self, col, y, x):
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}
        scores[(0, 1)].extend(self.score_of_row(self.march(y, x, 0, -1, 4), 0, 1, self.march(y, x, 0, 1, 4), col))  # Hàng ngang
        scores[(1, 0)].extend(self.score_of_row(self.march(y, x, -1, 0, 4), 1, 0, self.march(y, x, 1, 0, 4), col))  # Hàng dọc
        scores[(1, 1)].extend(self.score_of_row(self.march(y, x, -1, -1, 4), 1, 1, self.march(y, x, 1, 1, 4), col))  # Đường chéo chính
        scores[(-1, 1)].extend(self.score_of_row(self.march(y, x, -1, 1, 4), 1, -1, self.march(y, x, 1, -1, 4), col))  # Đường chéo phụ
        return self.score_ready(scores)  # Tổng hợp điểm số

    # Kiểm tra xem có tình huống chiến thắng hay không dựa trên điểm số
    def TF34score(self, score3, score4):
        for key4 in score4:
            if score4[key4] >= 1:  # Nếu có ít nhất một điểm số 4
                for key3 in score3:
                    if key3 != key4 and score3[key3] >= 2:  # Và có ít nhất hai điểm số 3
                        return True
        return False

    # Xác định tình huống chiến thắng dựa trên điểm số
    def winning_situation(self, sumcol):
        if 1 in sumcol[5].values():  # Nếu có 5 ô liên tiếp
            return 5
        elif len(sumcol[4]) >= 2 or (len(sumcol[4]) >= 1 and max(sumcol[4].values()) >= 2):  # Nếu có ít nhất hai điểm số 4
            return 4
        elif self.TF34score(sumcol[3], sumcol[4]):  # Nếu có tình huống TF34
            return 4
        else:
            score3 = sorted(sumcol[3].values(), reverse=True)  # Sắp xếp điểm số 3
            if len(score3) >= 2 and score3[0] >= score3[1] >= 2:  # Nếu có ít nhất hai điểm số 3
                return 3
        return 0

    def count_threats(self, col, y, x):
        # Tính điểm số cho ô (y, x) với người chơi col
        sumcol = self.score_of_col_one(col, y, x)
        self.sum_sumcol_values(sumcol)

        # Đếm số lượng mối đe dọa dựa trên điểm số
        threat_count = 0

        # Nếu có ít nhất một chuỗi 4 ô liên tiếp (điểm số 4)
        if sumcol[4] > 0:
            threat_count += sumcol[4]

        # Nếu có ít nhất hai chuỗi 3 ô liên tiếp (điểm số 3)
        if sumcol[3] >= 2:
            threat_count += sumcol[3] // 2

        return threat_count
    
    def calculate_weights(self, col, anticol, y, x):
        # Tính số lượng mối đe dọa của bạn và đối thủ
        num_threats = self.count_threats(col, y, x)
        num_opponent_threats = self.count_threats(anticol, y, x)

        # Tính trọng số tấn công và phòng thủ
        base_attack = 4
        base_defense = 6
        k = 4  # Hệ số tăng trọng số tấn công
        m = 4  # Hệ số tăng trọng số phòng thủ

        w_attack = base_attack + k * num_threats
        w_defense = base_defense + m * num_opponent_threats

        return w_attack, w_defense

    def stupid_score(self, col, anticol, y, x):
        M = 1000  # Hằng số lớn để ưu tiên chiến thắng
        res, adv, dis = 0, 0, 0

        # Lưu trữ giá trị ban đầu của ô để khôi phục sau khi tính toán
        original_value = self.board[y][x]

        # Tính trọng số linh hoạt
        w_attack, w_defense = self.calculate_weights(col, anticol, y, x)

        # Tính điểm số cho người chơi hiện tại (col)
        self.board[y][x] = col
        sumcol = self.score_of_col_one(col, y, x)
        a = self.winning_situation(sumcol)
        adv += a * M  # Ưu tiên chiến thắng
        self.sum_sumcol_values(sumcol)
        adv += sumcol[-1] + sumcol[1] + w_attack * sumcol[2] + w_attack * 2 * sumcol[3] + w_attack * 4 * sumcol[4]

        # Tính điểm số cho đối thủ (anticol)
        self.board[y][x] = anticol
        sumanticol = self.score_of_col_one(anticol, y, x)
        d = self.winning_situation(sumanticol)
        dis += d * (M - 100)  # Ưu tiên ngăn chặn đối thủ
        self.sum_sumcol_values(sumanticol)
        dis += sumanticol[-1] + sumanticol[1] + w_defense * sumanticol[2] + w_defense * 2 * sumanticol[3] + w_defense * 4 * sumanticol[4]

        res = adv + dis  # Tổng điểm số
        self.board[y][x] = original_value  # Đặt lại ô về trạng thái ban đầu
        return res
        
    # Kiểm tra chiến thắng cho một người chơi
    def check_winner(self, player):
        # Kiểm tra chiến thắng theo hàng ngang
        for y in range(self.size):
            for x in range(self.size - 4):
                if all(self.board[y][x + i] == player for i in range(5)):
                    return True
        
        # Kiểm tra chiến thắng theo hàng dọc
        for y in range(self.size - 4):
            for x in range(self.size):
                if all(self.board[y + i][x] == player for i in range(5)):
                    return True
        
        # Kiểm tra chiến thắng theo đường chéo chính (từ trái trên xuống phải dưới)
        for y in range(self.size - 4):
            for x in range(self.size - 4):
                if all(self.board[y + i][x + i] == player for i in range(5)):
                    return True
        
        # Kiểm tra chiến thắng theo đường chéo phụ (từ trái dưới lên phải trên)
        for y in range(4, self.size):
            for x in range(self.size - 4):
                if all(self.board[y - i][x + i] == player for i in range(5)):
                    return True
        
        return False
    
    # Kiểm tra bàn cờ đã đầy chưa
    def is_board_full(self):
        for y in range(self.size):
            for x in range(self.size):
                if self.board[y][x] == ' ':
                    return False
        return True
    
    # Tìm top n nước đi tốt nhất
    def get_top_moves(self, col, anticol, top_n=10):
        moves = []
        possible_moves = self.possible_moves()  # Lấy danh sách các nước đi có thể
        
        for move in possible_moves:
            y, x = move
            if self.board[y][x] == ' ':  # Chỉ xét các ô trống
                score = self.stupid_score(col, anticol, y, x)  # Tính điểm số heuristic
                moves.append((score, (y, x)))  # Thêm vào danh sách
        
        # Sắp xếp các nước đi theo điểm số giảm dần
        moves.sort(reverse=True, key=lambda x: x[0])
        
        # Trả về top_n nước đi tốt nhất
        return [move[1] for move in moves[:top_n]]
    
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
    
    # Kiểm tra nếu bàn cờ trống
    def is_empty(self):
        for y in range(self.size):
            for x in range(self.size):
                if self.board[y][x] != ' ':
                    return False
        return True


class GomokuGame:
    def __init__(self, size=15):
        self.size = size
        # Khởi tạo bàn cờ là list 2D với tất cả các ô là khoảng trắng
        self.board = [[' ' for _ in range(size)] for _ in range(size)]
        self.heuristic = GomokuHeuristic(self.board, size)
        self.player = 'X'  # Người chơi là 'X'
        self.computer = 'O'  # Máy tính là 'O'
        self.first_computer_move = True  # Biến kiểm tra xem có phải nước đi đầu tiên của máy tính

    def print_board(self):
        # Hiển thị số cột ở hàng đầu tiên, đảm bảo căn chỉnh cho cả số một và hai chữ số
        header = "    "
        for x in range(self.size):
            header += f"{x:2} "
        print(header)
        
        # Vẽ đường ngang ở đầu bảng
        print("   +" + "--+" * self.size)
        
        # Vẽ các hàng của bảng cờ
        for y in range(self.size):
            # Hiển thị số hàng, căn chỉnh phải
            row_str = f"{y:2} |"
            
            # Hiển thị từng ô trên hàng
            for x in range(self.size):
                cell = self.board[y][x]
                row_str += f" {cell}|"
            
            print(row_str)
            print("   +" + "--+" * self.size)

    # Kiểm tra người chơi đã thắng chưa (sử dụng heuristic)
    def is_winner(self, player):
        return self.heuristic.check_winner(player)

    # Kiểm tra bàn cờ đã đầy chưa (sử dụng heuristic)
    def is_board_full(self):
        return self.heuristic.is_board_full()

    def player_move(self, y, x):
        if 0 <= y < self.size and 0 <= x < self.size and self.board[y][x] == ' ':
            self.board[y][x] = self.player # Đánh dấu ô (y, x) là của người chơi
            return True
        return False

    def minimax_alpha_beta(self, depth, alpha, beta, maximizing_player):
        if depth == 0 or self.is_winner(self.player) or self.is_winner(self.computer) or self.is_board_full():
            if self.is_winner(self.computer):
                return (None, 1000000000)
            elif self.is_winner(self.player):
                return (None, -1000000000)
            else:
                return (None, 0)

        if maximizing_player:
            max_eval = -math.inf
            best_move = None
            # Sử dụng heuristic để lấy top nước đi tốt nhất
            top_moves = self.heuristic.get_top_moves(self.computer, self.player)
            for move in top_moves:
                y, x = move
                self.board[y][x] = self.computer
                eval = self.minimax_alpha_beta(depth - 1, alpha, beta, False)[1]
                self.board[y][x] = ' '
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return (best_move, max_eval)
        else:
            min_eval = math.inf
            best_move = None
            # Sử dụng heuristic để lấy top nước đi tốt nhất
            top_moves = self.heuristic.get_top_moves(self.player, self.computer)
            for move in top_moves:
                y, x = move
                self.board[y][x] = self.player
                eval = self.minimax_alpha_beta(depth - 1, alpha, beta, True)[1]
                self.board[y][x] = ' '
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return (best_move, min_eval)

    def find_player_move(self):
        # Tìm vị trí nước đi đầu tiên của người chơi
        for y in range(self.size):
            for x in range(self.size):
                if self.board[y][x] == self.player:
                    return (y, x)
        return None
    
    def random_move_near_player(self, player_move, radius=3):
        y_player, x_player = player_move
        
        # Tạo danh sách các vị trí hợp lệ trong phạm vi radius
        valid_positions = []
        
        for y in range(max(0, y_player - radius), min(self.size, y_player + radius + 1)):
            for x in range(max(0, x_player - radius), min(self.size, x_player + radius + 1)):
                # Kiểm tra ô trống và không phải là vị trí của người chơi
                if self.board[y][x] == ' ' and (y != y_player or x != x_player):
                    # Tính khoảng cách Manhattan từ vị trí người chơi
                    distance = abs(y - y_player) + abs(x - x_player)
                    if 1 <= distance <= radius:  # Đảm bảo không quá gần và không quá xa
                        valid_positions.append((y, x))
        
        # Nếu có vị trí hợp lệ, chọn ngẫu nhiên một trong số đó
        if valid_positions:
            return random.choice(valid_positions)
        
        # Fallback nếu không tìm thấy vị trí hợp lệ
        return self.get_center_or_random_move()
    
    def get_center_or_random_move(self):
        # Ưu tiên đánh ở giữa bàn cờ hoặc gần giữa
        center = self.size // 2
        if self.board[center][center] == ' ':
            return (center, center)
        
        # Tạo danh sách các vị trí trống gần tâm
        center_region = []
        for y in range(center-2, center+3):
            for x in range(center-2, center+3):
                if 0 <= y < self.size and 0 <= x < self.size and self.board[y][x] == ' ':
                    center_region.append((y, x))
        
        if center_region:
            return random.choice(center_region)
        
        # Nếu không có vị trí nào gần tâm, chọn ngẫu nhiên một ô trống
        empty_cells = []
        for y in range(self.size):
            for x in range(self.size):
                if self.board[y][x] == ' ':
                    empty_cells.append((y, x))
        
        if empty_cells:
            return random.choice(empty_cells)
        
        # Nếu không có ô trống nào (không nên xảy ra), trả về (0, 0)
        return (0, 0)

    def computer_move(self):
        if self.first_computer_move:
            # Nước đi đầu tiên của máy tính sẽ ngẫu nhiên gần với nước đi của người chơi
            player_move = self.find_player_move()
            if player_move:
                y, x = self.random_move_near_player(player_move)
                self.board[y][x] = self.computer
                print(f"Máy tính đã đánh vào vị trí: {y} {x}")
                self.first_computer_move = False  # Đánh dấu là đã thực hiện nước đi đầu tiên
            else:
                # Fallback nếu không tìm thấy nước đi của người chơi
                best_move, _ = self.minimax_alpha_beta(depth_max, -math.inf, math.inf, True)
                if best_move:
                    y, x = best_move
                    self.board[y][x] = self.computer
                    print(f"Máy tính đã đánh vào vị trí: {y} {x}")
                    self.first_computer_move = False
        else:
            # Các nước đi tiếp theo sẽ sử dụng minimax
            best_move, _ = self.minimax_alpha_beta(depth_max, -math.inf, math.inf, True)
            if best_move:
                y, x = best_move
                self.board[y][x] = self.computer
                print(f"Máy tính đã đánh vào vị trí: {y} {x}")

    def play(self):
        print("\n===== CHÀO MỪNG ĐẾN VỚI GOMOKU (GAME CỜ CARO) =====")
        print("Hãy nhập tọa độ y x (hàng và cột) để đánh X vào vị trí đó")
        print("Bạn là X, máy tính là O")
        print("Người chơi đi trước\n")
        
        while True:
            self.print_board()
            if self.is_winner(self.player):
                print("\n🎉 Chúc mừng! Bạn đã thắng! 🎉")
                break
            if self.is_winner(self.computer):
                print("\n😓 Máy tính đã thắng! 😓")
                break
            if self.is_board_full():
                print("\n🤝 Hòa! Bàn cờ đã đầy 🤝")
                break

            # Lượt người chơi
            try:
                y, x = map(int, input("\nNhập tọa độ (y x): ").split())
                if not self.player_move(y, x):
                    print("❌ Nước đi không hợp lệ! Hãy kiểm tra lại tọa độ và đảm bảo ô chưa được đánh.")
                    continue
            except ValueError:
                print("❌ Nhập sai định dạng! Hãy nhập hai số nguyên cách nhau bởi dấu cách, ví dụ: 7 8")
                continue

            # Kiểm tra người chơi thắng ngay sau nước đi
            if self.is_winner(self.player):
                self.print_board()
                print("\n🎉 Chúc mừng! Bạn đã thắng! 🎉")
                break

            # Lượt máy tính
            print("\nĐến lượt máy tính...")
            self.computer_move()


# Khởi tạo và chơi game
if __name__ == "__main__":
    game = GomokuGame()
    game.play()