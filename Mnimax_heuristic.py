# Kích thước bàn cờ
BOARD_SIZE = 3
# Số lượng ô liên tiếp cần thiết để chiến thắng
WIN_CONDITION = 3
# Phần thưởng khi chiến thắng
REWARD = 10


class TicTacToe:

    def __init__(self, board):
        self.board = board
        self.player = 'O'
        self.computer = 'X'

    def run(self):
        print("Computer starts...")

        while True:
            self.move_computer()
            self.move_player()

    def print_board(self):
        for i in range(BOARD_SIZE):
            row = '|'.join(self.board.get(i * BOARD_SIZE + j + 1, ' ') for j in range(BOARD_SIZE))
            print(row)
            if i < BOARD_SIZE - 1:
                print('-' * (BOARD_SIZE * 2 - 1))
        print('\n')

    def is_cell_free(self, position):
        return self.board.get(position, ' ') == ' '

    def update_player_position(self, player, position):
        if self.is_cell_free(position):
            self.board[position] = player
            self.check_game_state()
        else:
            print("Can't insert there!")
            self.move_player()

    def check_game_state(self):
        self.print_board()

        if self.is_draw():
            print("Draw!")
            exit()

        if self.is_winning(self.player):
            print("Player wins!")
            exit()

        if self.is_winning(self.computer):
            print("Computer wins!")
            exit()

    def is_winning(self, player):
        # Kiểm tra các hàng
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE - WIN_CONDITION + 1):
                if all(self.board.get(i * BOARD_SIZE + j + k + 1, '') == player for k in range(WIN_CONDITION)):
                    return True

        # Kiểm tra các cột
        for j in range(BOARD_SIZE):
            for i in range(BOARD_SIZE - WIN_CONDITION + 1):
                if all(self.board.get((i + k) * BOARD_SIZE + j + 1, '') == player for k in range(WIN_CONDITION)):
                    return True

        # Kiểm tra các đường chéo chính (từ trái trên sang phải dưới)
        for i in range(BOARD_SIZE - WIN_CONDITION + 1):
            for j in range(BOARD_SIZE - WIN_CONDITION + 1):
                if all(self.board.get((i + k) * BOARD_SIZE + (j + k) + 1, '') == player for k in range(WIN_CONDITION)):
                    return True

        # Kiểm tra các đường chéo phụ (từ phải trên sang trái dưới)
        for i in range(WIN_CONDITION - 1, BOARD_SIZE):
            for j in range(BOARD_SIZE - WIN_CONDITION + 1):
                if all(self.board.get((i - k) * BOARD_SIZE + (j + k) + 1, '') == player for k in range(WIN_CONDITION)):
                    return True

        return False

    def is_draw(self):
        return all(self.board.get(i, ' ') != ' ' for i in range(1, BOARD_SIZE * BOARD_SIZE + 1))

    def move_player(self):
        position = int(input("Enter the position for 'O':  "))
        self.update_player_position(self.player, position)

    def move_computer(self):
        best_score = -float('inf')
        best_move = 0

        # Duyệt qua tất cả các ô trống
        for position in range(1, BOARD_SIZE * BOARD_SIZE + 1):
            if self.is_cell_free(position):
                self.board[position] = self.computer
                score = self.minimax(0, -float('inf'), float('inf'), False)
                self.board[position] = ' '

                if score > best_score:
                    best_score = score
                    best_move = position

        self.board[best_move] = self.computer
        self.check_game_state()

    def minimax(self, depth, alpha, beta, is_maximizer):
        # Kiểm tra terminal state
        if self.is_winning(self.computer):
            return REWARD - depth
        if self.is_winning(self.player):
            return -REWARD + depth
        if self.is_draw():
            return 0

        if is_maximizer:
            best_score = -float('inf')
            for position in range(1, BOARD_SIZE * BOARD_SIZE + 1):
                if self.is_cell_free(position):
                    self.board[position] = self.computer
                    score = self.minimax(depth + 1, alpha, beta, False)
                    self.board[position] = ' '

                    if score > best_score:
                        best_score = score

                    alpha = max(alpha, score)
                    if alpha >= beta:
                        break  # Alpha-Beta Pruning: Cắt bỏ các nhánh không cần thiết
            return best_score
        else:
            best_score = float('inf')
            for position in range(1, BOARD_SIZE * BOARD_SIZE + 1):
                if self.is_cell_free(position):
                    self.board[position] = self.player
                    score = self.minimax(depth + 1, alpha, beta, True)
                    self.board[position] = ' '

                    if score < best_score:
                        best_score = score

                    beta = min(beta, score)
                    if alpha >= beta:
                        break  # Alpha-Beta Pruning: Cắt bỏ các nhánh không cần thiết
            return best_score


if __name__ == '__main__':
    board = {i: ' ' for i in range(1, BOARD_SIZE * BOARD_SIZE + 1)}

    game = TicTacToe(board)
    game.run()