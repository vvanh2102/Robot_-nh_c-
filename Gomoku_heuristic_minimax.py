

class GomokuHeuristic:
    def __init__(self, board):
        self.board = board  # Lưu trữ bảng trò chơi hiện tại để sử dụng trong các hàm khác

    def is_in(self, y, x):
        # Kiểm tra xem tọa độ (y, x) có nằm trong phạm vi của bảng không
        return 0 <= y < len(self.board) and 0 <= x < len(self.board)

    def march(self, y, x, dy, dx, length):
        # Di chuyển từ vị trí (y, x) theo hướng (dy, dx) với khoảng cách `length`
        yf = y + length * dy  # Tính toán vị trí y mới
        xf = x + length * dx  # Tính toán vị trí x mới
        # Nếu vị trí mới (yf, xf) nằm ngoài bảng, điều chỉnh lại để nằm trong bảng
        while not self.is_in(yf, xf):
            yf -= dy  # Lùi lại theo hướng dy
            xf -= dx  # Lùi lại theo hướng dx
        return yf, xf  # Trả về vị trí hợp lệ cuối cùng

    def score_ready(self, scorecol):
        # Khởi tạo một từ điển để lưu trữ điểm số cho các trường hợp khác nhau
        sumcol = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, -1: {}}
        # Duyệt qua từng hướng (key) trong scorecol
        for key in scorecol:
            # Duyệt qua từng điểm số (score) trong hướng đó
            for score in scorecol[key]:
                # Nếu điểm số đã tồn tại trong sumcol, tăng giá trị lên 1
                if key in sumcol[score]:
                    sumcol[score][key] += 1
                else:
                    # Nếu chưa tồn tại, khởi tạo giá trị là 1
                    sumcol[score][key] = 1
        return sumcol  # Trả về từ điển điểm số đã được tổng hợp

    def sum_sumcol_values(self, sumcol):
        # Duyệt qua từng key trong sumcol
        for key in sumcol:
            # Nếu key là 5, kiểm tra xem có ít nhất một giá trị bằng 1 không
            if key == 5:
                sumcol[5] = int(1 in sumcol[5].values())  # Trả về 1 nếu có, ngược lại 0
            else:
                # Tính tổng các giá trị trong từ điển con
                sumcol[key] = sum(sumcol[key].values())

    def score_of_list(self, lis, col):
        # Đếm số lượng ô trống và ô được điền bởi màu `col`
        blank = lis.count(' ')  # Số ô trống
        filled = lis.count(col)  # Số ô được điền bởi `col`
        
        # Nếu tổng số ô trống và ô được điền ít hơn 5, trả về -1 (không hợp lệ)
        if blank + filled < 5:
            return -1
        # Nếu tất cả ô đều trống, trả về 0
        elif blank == 5:
            return 0
        else:
            # Trả về số ô được điền bởi `col`
            return filled

    def row_to_list(self, y, x, dy, dx, yf, xf):
        # Tạo một danh sách các ô từ vị trí (y, x) đến (yf, xf) theo hướng (dy, dx)
        row = []
        while y != yf + dy or x != xf + dx:
            row.append(self.board[y][x])  # Thêm giá trị ô hiện tại vào danh sách
            y += dy  # Di chuyển theo hướng dy
            x += dx  # Di chuyển theo hướng dx
        return row  # Trả về danh sách các ô

    def score_of_row(self, cordi, dy, dx, cordf, col):
        # Tính điểm số cho một hàng từ vị trí bắt đầu (cordi) đến vị trí kết thúc (cordf)
        colscores = []  # Danh sách lưu điểm số
        y, x = cordi  # Tọa độ bắt đầu
        yf, xf = cordf  # Tọa độ kết thúc
        row = self.row_to_list(y, x, dy, dx, yf, xf)  # Lấy danh sách các ô trong hàng
        # Duyệt qua từng đoạn 5 ô liên tiếp trong hàng
        for start in range(len(row) - 4):
            score = self.score_of_list(row[start:start + 5], col)  # Tính điểm số cho đoạn 5 ô
            colscores.append(score)  # Thêm điểm số vào danh sách
        return colscores  # Trả về danh sách điểm số

    def score_of_col(self, col):
        # Tính điểm số cho toàn bộ bảng dựa trên màu `col`
        f = len(self.board)  # Kích thước bảng
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}  # Khởi tạo từ điển lưu điểm số
        # Duyệt qua từng hàng và cột để tính điểm số
        for start in range(f):
            scores[(0, 1)].extend(self.score_of_row((start, 0), 0, 1, (start, f - 1), col))  # Hàng ngang
            scores[(1, 0)].extend(self.score_of_row((0, start), 1, 0, (f - 1, start), col))  # Hàng dọc
            scores[(1, 1)].extend(self.score_of_row((start, 0), 1, 1, (f - 1, f - 1 - start), col))  # Đường chéo chính
            scores[(-1, 1)].extend(self.score_of_row((start, 0), -1, 1, (0, start), col))  # Đường chéo phụ
            # Xử lý các trường hợp đặc biệt
            if start + 1 < f:
                scores[(1, 1)].extend(self.score_of_row((0, start + 1), 1, 1, (f - 2 - start, f - 1), col))
                scores[(-1, 1)].extend(self.score_of_row((f - 1, start + 1), -1, 1, (start + 1, f - 1), col))
        return self.score_ready(scores)  # Trả về điểm số đã được tổng hợp

    def score_of_col_one(self, col, y, x):
        # Tính điểm số cho một ô cụ thể (y, x) dựa trên màu `col`
        scores = {(0, 1): [], (-1, 1): [], (1, 0): [], (1, 1): []}  # Khởi tạo từ điển lưu điểm số
        # Tính điểm số cho các hướng xung quanh ô (y, x)
        scores[(0, 1)].extend(self.score_of_row(self.march(y, x, 0, -1, 4), 0, 1, self.march(y, x, 0, 1, 4), col))  # Hàng ngang
        scores[(1, 0)].extend(self.score_of_row(self.march(y, x, -1, 0, 4), 1, 0, self.march(y, x, 1, 0, 4), col))  # Hàng dọc
        scores[(1, 1)].extend(self.score_of_row(self.march(y, x, -1, -1, 4), 1, 1, self.march(y, x, 1, 1, 4), col))  # Đường chéo chính
        scores[(-1, 1)].extend(self.score_of_row(self.march(y, x, -1, 1, 4), 1, -1, self.march(y, x, 1, -1, 4), col))  # Đường chéo phụ
        return self.score_ready(scores)  # Trả về điểm số đã được tổng hợp

    def TF34score(self, score3, score4):
        # Kiểm tra xem có tình huống chiến thắng dựa trên điểm số của 3 và 4 ô liên tiếp không
        for key4 in score4:
            if score4[key4] >= 1:  # Nếu có ít nhất một đoạn 4 ô liên tiếp
                for key3 in score3:
                    if key3 != key4 and score3[key3] >= 2:  # Và có ít nhất hai đoạn 3 ô liên tiếp
                        return True  # Trả về True (có tình huống chiến thắng)
        return False  # Ngược lại, trả về False

    def winning_situation(self, sumcol):
        # Xác định tình huống chiến thắng dựa trên điểm số
        if 1 in sumcol[5].values():  # Nếu có 5 ô liên tiếp
            return 5  # Trả về 5 (chiến thắng)
        elif len(sumcol[4]) >= 2 or (len(sumcol[4]) >= 1 and max(sumcol[4].values()) >= 2):  # Nếu có ít nhất hai đoạn 4 ô liên tiếp hoặc một đoạn 4 ô với ít nhất hai lần xuất hiện
            return 4  # Trả về 4 (gần chiến thắng)
        elif self.TF34score(sumcol[3], sumcol[4]):  # Nếu có tình huống chiến thắng dựa trên 3 và 4 ô liên tiếp
            return 4  # Trả về 4 (gần chiến thắng)
        else:
            score3 = sorted(sumcol[3].values(), reverse=True)  # Sắp xếp điểm số của các đoạn 3 ô liên tiếp
            if len(score3) >= 2 and score3[0] >= score3[1] >= 2:  # Nếu có ít nhất hai đoạn 3 ô liên tiếp với điểm số cao
                return 3  # Trả về 3 (có tiềm năng chiến thắng)
        return 0  # Ngược lại, trả về 0 (không có tình huống chiến thắng)

    def stupid_score(self, col, anticol, y, x):
        # Tính điểm số tổng hợp cho một nước đi tại (y, x)
        M = 1000  # Hằng số lớn để ưu tiên các tình huống chiến thắng
        res, adv, dis = 0, 0, 0  # Khởi tạo biến lưu kết quả, điểm tấn công và điểm phòng thủ

        # Tấn công: Giả định đặt quân cờ `col` tại (y, x)
        self.board[y][x] = col  # Đặt quân cờ
        sumcol = self.score_of_col_one(col, y, x)  # Tính điểm số cho nước đi này
        a = self.winning_situation(sumcol)  # Xác định tình huống chiến thắng
        adv += a * M  # Cộng điểm tấn công dựa trên tình huống chiến thắng
        self.sum_sumcol_values(sumcol)  # Tính tổng điểm số
        adv += sumcol[-1] + sumcol[1] + 4 * sumcol[2] + 8 * sumcol[3] + 16 * sumcol[4]  # Cộng thêm điểm số dựa trên các đoạn ô liên tiếp

        # Phòng thủ: Giả định đặt quân cờ `anticol` tại (y, x)
        self.board[y][x] = anticol  # Đặt quân cờ đối thủ
        sumanticol = self.score_of_col_one(anticol, y, x)  # Tính điểm số cho nước đi này
        d = self.winning_situation(sumanticol)  # Xác định tình huống chiến thắng
        dis += d * (M - 100)  # Cộng điểm phòng thủ dựa trên tình huống chiến thắng
        self.sum_sumcol_values(sumanticol)  # Tính tổng điểm số
        dis += sumanticol[-1] + sumanticol[1] + 4 * sumanticol[2] + 8 * sumanticol[3] + 16 * sumanticol[4]  # Cộng thêm điểm số dựa trên các đoạn ô liên tiếp

        res = adv + dis  # Tính tổng điểm số
        self.board[y][x] = ' '  # Trả lại ô trống sau khi tính toán
        return res  # Trả về điểm số tổng hợp