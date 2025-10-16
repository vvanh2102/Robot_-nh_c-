class GomokuHeuristic:
    # Khởi tạo lớp GomokuHeuristic để tính toán điểm số cho trò chơi Gomoku
    def __init__(self, board, size):
        self.board = board  # Lưu trữ bàn cờ
        self.size = size    # Lưu kích thước của bàn cờ

    def is_in(self, y, x):
        # Kiểm tra xem tọa độ (y, x) có nằm trong bàn cờ không
        return 0 <= y < self.size and 0 <= x < self.size

    def march(self, y, x, dy, dx, length):
        # Tính toán tọa độ cuối cùng sau khi di chuyển từ (y, x) theo hướng (dy, dx) với độ dài length
        yf = y + length * dy  # Tính tọa độ y cuối
        xf = x + length * dx  # Tính tọa độ x cuối
        while not self.is_in(yf, xf):
            # Nếu tọa độ không hợp lệ, lùi lại một bước
            yf -= dy  # Lùi lại theo hướng y
            xf -= dx  # Lùi lại theo hướng x
        return yf, xf  # Trả về tọa độ hợp lệ

    def score_ready(self, scorecol):
        # Tính toán tổng điểm cho các cột điểm
        sumcol = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, -1: {}}  # Khởi tạo từ điển để lưu điểm
        for key in scorecol:
            for score in scorecol[key]:
                # Cộng dồn số lượng cho mỗi điểm
                if key in sumcol[score]:
                    sumcol[score][key] += 1  # Tăng số lượng nếu đã có
                else:
                    sumcol[score][key] = 1  # Khởi tạo số lượng nếu chưa có
        return sumcol  # Trả về tổng điểm

    def sum_sumcol_values(self, sumcol):
        # Tính tổng giá trị cho mỗi cột điểm
        for key in sumcol:
            if key == 5:
                sumcol[5] = int(1 in sumcol[5].values())  # Kiểm tra xem có điểm 5 nào không
            else:
                sumcol[key] = sum(sumcol[key].values())  # Tính tổng các giá trị

    def score_of_list(self, lis, col):
        # Tính điểm cho một danh sách ô
        blank = lis.count(' ')  # Đếm số ô trống
        filled = lis.count(col)  # Đếm số ô đã được đánh
        if blank + filled < 5:
            return -1  # Không đủ ô để tính điểm
        elif blank == 5:
            return 0  # Tất cả ô đều trống
        else:
            return filled  # Trả về số ô đã được đánh

    def row_to_list(self, y, x, dy, dx, yf, xf):
        # Chuyển đổi hàng từ tọa độ (y, x) đến (yf, xf) thành danh sách
        row = []  # Khởi tạo danh sách rỗng
        while y != yf + dy or x != xf + dx:
            # Lặp cho đến khi đến tọa độ cuối
            row.append(self.board.get((y, x), ' '))  # Lấy giá trị từ bàn cờ, mặc định là ' ' nếu không có
            y += dy  # Di chuyển theo hướng y
            x += dx  # Di chuyển theo hướng x
        return row  # Trả về danh sách hàng

    def score_of_row(self, cordi, dy, dx, cordf, col):
        # Tính điểm cho một hàng từ tọa độ bắt đầu đến kết thúc
        colscores = []  # Khởi tạo danh sách để lưu điểm
        y, x = cordi  # Lấy tọa độ bắt đầu
        yf, xf = cordf  # Lấy tọa độ kết thúc
        row = self.row_to_list(y, x, dy, dx, yf, xf)  # Lấy danh sách hàng
        for start in range(len(row) - 4):
            # Lặp qua từng đoạn 5 ô trong hàng
            score = self.score_of_list(row[start:start + 5], col)  # Tính điểm cho đoạn 5 ô
            colscores.append(score)  # Thêm điểm vào danh sách
        return colscores  # Trả về danh sách điểm

    def score_of_col(self, col):
        # Tính điểm cho các cột trong bàn cờ
        f = self.size  # Lưu kích thước bàn cờ
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}  # Khởi tạo từ điển để lưu điểm cho các hướng
        for start in range(f):
            # Tính điểm cho từng hướng
            scores[(0, 1)].extend(self.score_of_row((start, 0), 0, 1, (start, f - 1), col))  # Hướng ngang
            scores[(1, 0)].extend(self.score_of_row((0, start), 1, 0, (f - 1, start), col))  # Hướng dọc
            scores[(1, 1)].extend(self.score_of_row((start, 0), 1, 1, (f - 1, f - 1 - start), col))  # Hướng chéo
            scores[(-1, 1)].extend(self.score_of_row((start, 0), -1, 1, (0, start), col))  # Hướng chéo ngược
            if start + 1 < f:
                scores[(1, 1)].extend(self.score_of_row((0, start + 1), 1, 1, (f - 2 - start, f - 1), col))  # Hướng chéo
                scores[(-1, 1)].extend(self.score_of_row((f - 1, start + 1), -1, 1, (start + 1, f - 1), col))  # Hướng chéo ngược
        return self.score_ready(scores)  # Trả về tổng điểm

    def score_of_col_one(self, col, y, x):
        # Tính điểm cho một ô cụ thể (y, x)
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}  # Khởi tạo từ điển để lưu điểm cho các hướng
        scores[(0, 1)].extend(self.score_of_row(self.march(y, x, 0, -1, 4), 0, 1, self.march(y, x, 0, 1, 4), col))  # Hướng ngang
        scores[(1, 0)].extend(self.score_of_row(self.march(y, x, -1, 0, 4), 1, 0, self.march(y, x, 1, 0, 4), col))  # Hướng dọc
        scores[(1, 1)].extend(self.score_of_row(self.march(y, x, -1, -1, 4), 1, 1, self.march(y, x, 1, 1, 4), col))  # Hướng chéo
        scores[(-1, 1)].extend(self.score_of_row(self.march(y, x, -1, 1, 4), 1, -1, self.march(y, x, 1, -1, 4), col))  # Hướng chéo ngược
        return self.score_ready(scores)  # Trả về tổng điểm

    def TF34score(self, score3, score4):
        # Kiểm tra xem có tình huống thắng nào không
        for key4 in score4:
            if score4[key4] >= 1:  # Nếu có ít nhất 1 điểm 4
                for key3 in score3:
                    if key3 != key4 and score3[key3] >= 2:  # Nếu có ít nhất 2 điểm 3 khác với điểm 4
                        return True  # Trả về True nếu có tình huống thắng
        return False  # Trả về False nếu không có tình huống thắng

    def winning_situation(self, sumcol):
        # Kiểm tra tình huống thắng dựa trên tổng điểm
        if 1 in sumcol[5].values():  # Nếu có điểm 5
            return 5  # Trả về 5
        elif len(sumcol[4]) >= 2 or (len(sumcol[4]) >= 1 and max(sumcol[4].values()) >= 2):  # Nếu có ít nhất 2 điểm 4
            return 4  # Trả về 4
        elif self.TF34score(sumcol[3], sumcol[4]):  # Kiểm tra tình huống thắng từ điểm 3 và 4
            return 4  # Trả về 4
        else:
            score3 = sorted(sumcol[3].values(), reverse=True)  # Sắp xếp điểm 3
            if len(score3) >= 2 and score3[0] >= score3[1] >= 2:  # Nếu có ít nhất 2 điểm 3
                return 3  # Trả về 3
        return 0  # Trả về 0 nếu không có tình huống thắng

    def stupid_score(self, col, anticol, y, x):
        # Tính điểm cho nước đi của người chơi
        M = 1000  # Hệ số cho điểm
        res, adv, dis = 0, 0, 0  # Khởi tạo các biến điểm

        self.board[(y, x)] = col  # Đánh dấu nước đi của người chơi
        sumcol = self.score_of_col_one(col, y, x)  # Tính điểm cho nước đi
        a = self.winning_situation(sumcol)  # Kiểm tra tình huống thắng
        adv += a * M  # Cộng điểm cho nước đi
        self.sum_sumcol_values(sumcol)  # Tính tổng giá trị cho các cột điểm
        adv += sumcol[-1] + sumcol[1] + 4 * sumcol[2] + 8 * sumcol[3] + 16 * sumcol[4]  # Cộng điểm cho các cột

        self.board[(y, x)] = anticol  # Đánh dấu nước đi của đối thủ
        sumanticol = self.score_of_col_one(anticol, y, x)  # Tính điểm cho nước đi của đối thủ
        d = self.winning_situation(sumanticol)  # Kiểm tra tình huống thắng
        dis += d * (M - 100)  # Cộng điểm cho nước đi của đối thủ
        self.sum_sumcol_values(sumanticol)  # Tính tổng giá trị cho các cột điểm
        dis += sumanticol[-1] + sumanticol[1] + 4 * sumanticol[2] + 8 * sumanticol[3] + 16 * sumanticol[4]  # Cộng điểm cho các cột

        res = adv + dis  # Tính tổng điểm
        self.board[(y, x)] = ' '  # Khôi phục ô về trạng thái trống
        return res  # Trả về điểm số


class GomokuGame:
    def __init__(self, size=15):
        # Khởi tạo lớp GomokuGame để quản lý trò chơi
        self.size = size  # Lưu kích thước bàn cờ
        self.board = {}  # Sử dụng dictionary để lưu trữ bàn cờ
        self.heuristic = GomokuHeuristic(self.board, size)  # Khởi tạo đối tượng GomokuHeuristic
        self.player = 'X'  # Người chơi là 'X'
        self.computer = 'O'  # Máy tính là 'O'

    def print_board(self):
        # Hiển thị số cột ở hàng đầu tiên, đảm bảo căn chỉnh cho cả số một và hai chữ số
        header = "    "  # Khởi tạo tiêu đề
        for x in range(self.size):
            header += f"{x:2} "  # Thêm số cột vào tiêu đề
        print(header)  # In tiêu đề
        
        # Vẽ đường ngang ở đầu bảng
        print("   +" + "--+" * self.size)
        
        # Vẽ các hàng của bảng cờ
        for y in range(self.size):
            # Hiển thị số hàng, căn chỉnh phải
            row_str = f"{y:2} |"  # Khởi tạo chuỗi cho hàng
            
            # Hiển thị từng ô trên hàng
            for x in range(self.size):
                cell = self.board.get((y, x), ' ')  # Lấy giá trị ô từ bàn cờ
                row_str += f" {cell}|"  # Thêm giá trị ô vào chuỗi
            
            print(row_str)  # In chuỗi hàng
            print("   +" + "--+" * self.size)  # Vẽ đường ngang

    def is_winner(self, player):
        # Kiểm tra hàng ngang, dọc và chéo
        for y in range(self.size):
            for x in range(self.size - 4):
                # Kiểm tra hàng ngang
                if all(self.board.get((y, x + i), ' ') == player for i in range(5)):
                    return True  # Trả về True nếu có 5 ô liên tiếp
                # Kiểm tra hàng dọc
                if all(self.board.get((x + i, y), ' ') == player for i in range(5)):
                    return True  # Trả về True nếu có 5 ô liên tiếp
        for y in range(self.size - 4):
            for x in range(self.size - 4):
                # Kiểm tra đường chéo chính
                if all(self.board.get((y + i, x + i), ' ') == player for i in range(5)):
                    return True  # Trả về True nếu có 5 ô liên tiếp
                # Kiểm tra đường chéo phụ
                if all(self.board.get((y + i, x + 4 - i), ' ') == player for i in range(5)):
                    return True  # Trả về True nếu có 5 ô liên tiếp
        return False  # Trả về False nếu không có ai thắng

    def is_board_full(self):
        # Kiểm tra xem bàn cờ đã đầy chưa
        return all(self.board.get((y, x), ' ') != ' ' for y in range(self.size) for x in range(self.size))

    def player_move(self, y, x):
        # Xử lý nước đi của người chơi
        if 0 <= y < self.size and 0 <= x < self.size and self.board.get((y, x), ' ') == ' ':
            self.board[(y, x)] = self.player  # Đánh dấu nước đi của người chơi
            return True  # Trả về True nếu nước đi hợp lệ
        return False  # Trả về False nếu nước đi không hợp lệ

    def computer_move(self):
        # Xử lý nước đi của máy tính
        best_score = -float('inf')  # Khởi tạo điểm tốt nhất
        best_move = None  # Khởi tạo nước đi tốt nhất
        for y in range(self.size):
            for x in range(self.size):
                if self.board.get((y, x), ' ') == ' ':  # Nếu ô trống
                    score = self.heuristic.stupid_score(self.computer, self.player, y, x)  # Tính điểm cho nước đi
                    if score > best_score:  # Nếu điểm cao hơn điểm tốt nhất
                        best_score = score  # Cập nhật điểm tốt nhất
                        best_move = (y, x)  # Cập nhật nước đi tốt nhất
        if best_move:
            self.board[best_move] = self.computer  # Đánh dấu nước đi của máy tính
            print(f"Máy tính đã đánh vào vị trí: {best_move[0]} {best_move[1]}")  # In ra vị trí máy tính đánh

    def play(self):
        # Bắt đầu trò chơi
        print("\n===== CHÀO MỪNG ĐẾN VỚI GOMOKU (GAME CỜ CARO) =====")
        print("Hãy nhập tọa độ y x (hàng và cột) để đánh X vào vị trí đó")
        print("Bạn là X, máy tính là O")
        print("Người chơi đi trước\n")
        
        while True:
            self.print_board()  # In bàn cờ
            if self.is_winner(self.player):  # Kiểm tra người chơi thắng
                print("\n🎉 Chúc mừng! Bạn đã thắng! 🎉")
                break  # Kết thúc trò chơi
            if self.is_winner(self.computer):  # Kiểm tra máy tính thắng
                print("\n😓 Máy tính đã thắng! 😓")
                break  # Kết thúc trò chơi
            if self.is_board_full():  # Kiểm tra bàn cờ đã đầy
                print("\n🤝 Hòa! Bàn cờ đã đầy 🤝")
                break  # Kết thúc trò chơi

            # Lượt người chơi
            try:
                y, x = map(int, input("\nNhập tọa độ (y x): ").split())  # Nhập tọa độ
                if not self.player_move(y, x):  # Kiểm tra nước đi hợp lệ
                    print("❌ Nước đi không hợp lệ! Hãy kiểm tra lại tọa độ và đảm bảo ô chưa được đánh.")
                    continue  # Quay lại vòng lặp nếu không hợp lệ
            except ValueError:
                print("❌ Nhập sai định dạng! Hãy nhập hai số nguyên cách nhau bởi dấu cách, ví dụ: 7 8")
                continue  # Quay lại vòng lặp nếu nhập sai định dạng

            # Kiểm tra người chơi thắng ngay sau nước đi
            if self.is_winner(self.player):
                self.print_board()  # In bàn cờ
                print("\n🎉 Chúc mừng! Bạn đã thắng! 🎉")
                break  # Kết thúc trò chơi

            # Lượt máy tính
            print("\nĐến lượt máy tính...")
            self.computer_move()  # Máy tính thực hiện nước đi
            

# Khởi tạo và chơi game
if __name__ == "__main__":
    game = GomokuGame()  # Tạo đối tượng trò chơi
    game.play()  # Bắt đầu trò chơi