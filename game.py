"""
An implementation of the game and the game board

@author: Blaise Wang
"""
import itertools

import numpy as np

from mcts_alphaZero import MCTSPlayer


class Board:
    def __init__(self, n: int):
        self.n = n
        self.round = 0
        self.winner = -1
        self.move_list = []
        self.chess = np.repeat(0, self.n * self.n).reshape(self.n, self.n)
        self.initialize_moves()

    def initialize_moves(self):
        self.add_move(3, 4)
        self.add_move(3, 3)
        self.add_move(4, 3)
        self.add_move(4, 4)

    def initialize(self):
        self.round = 0
        self.winner = -1
        self.move_list = []
        self.chess[0:self.n, 0:self.n] = 0
        self.initialize_moves()

    def add_move(self, x: int, y: int):
        self.round += 1
        self.move_list.append((x, y))
        self.chess[x, y] = 2 if self.round % 2 == 0 else 1

        directions = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]
        for dx, dy in directions:
            tx, ty = x, y
            while self.in_board(tx + dx, ty + dy):
                tx += dx
                ty += dy
                if self.chess[tx, ty] == 0:
                    break
                if self.chess[tx, ty] == self.get_opponent_player():
                    while tx - dx != x or ty - dy != y:
                        tx -= dx
                        ty -= dy
                        self.chess[tx, ty] = 1 if self.get_opponent_player() == 1 else 2
                    break

    def remove_move(self):
        self.round -= 1
        x, y = self.move_list.pop()
        self.chess[x, y] = 0

    def move_to_location(self, move: int) -> (int, int):
        x = self.n - move // self.n - 1
        y = move % self.n
        return x, y

    def location_to_move(self, x: int, y: int) -> int:
        return (self.n - x - 1) * self.n + y

    def in_board(self, pos_x, pos_y):
        if pos_x < 0 or pos_y < 0 or pos_x >= self.n or pos_y >= self.n:
            return False
        return True

    def get_available_moves(self, player):
        potential_move_list = []
        directions = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]]
        for x, y in list(itertools.product(range(self.n), range(self.n))):
            if self.chess[x, y] != 0:
                continue
            for dx, dy in directions:
                flag = False
                tx, ty = x, y
                while self.in_board(tx + dx, ty + dy):
                    tx += dx
                    ty += dy
                    if self.chess[tx, ty] == 0:
                        break
                    if abs(player - self.chess[tx, ty]) == 1:
                        flag = True
                    else:
                        if flag:
                            potential_move_list.append(self.location_to_move(x, y))
                        break
        return list(set(potential_move_list))

    def get_current_state(self):
        player = self.get_current_player()
        opponent = 2 if player == 1 else 1
        square_state = np.zeros((4, self.n, self.n))
        for (x, y), value in np.ndenumerate(self.chess):
            if value == player:
                square_state[0][self.n - x - 1][y] = 1.0
            elif value == opponent:
                square_state[1][self.n - x - 1][y] = 1.0
        if self.get_move_number() > 0:
            x, y = self.move_list[self.get_move_number() - 1]
            square_state[2][self.n - x - 1][y] = 1.0
        if self.get_current_player() == 1:
            square_state[3][:, :] = 1.0
        return square_state[:, ::-1, :]

    def get_move_number(self) -> int:
        return len(self.move_list)

    def get_current_player(self) -> int:
        return 1 if self.round % 2 == 0 else 2

    def get_opponent_player(self) -> int:
        return 2 if self.round % 2 == 0 else 1

    def get_color_number(self) -> (int, int):
        white = 0
        black = 0
        for x, y in list(itertools.product(range(self.n), range(self.n))):
            black += 1 if self.chess[x, y] == 1 else 0
            white += 1 if self.chess[x, y] == 2 else 0
        return black, white

    def has_winner(self):
        if len(self.get_available_moves(self.get_current_player())):
            return -1
        else:
            self.round += 1
            if len(self.get_available_moves(self.get_opponent_player())):
                return -1
            else:
                black, white = self.get_color_number()
                self.winner = 1 if black > white else 2 if black < white else 0
                return self.winner


class Game:
    def __init__(self, board: 'Board'):
        self.board = board

    def start_play(self, args) -> int:
        player1, player2, index = args
        if index % 2:
            player1, player2 = player2, player1
        self.board.initialize()
        while self.board.winner == -1:
            player_in_turn = player1 if self.board.get_current_player() == 1 else player2
            move, _ = player_in_turn.get_action(self.board)
            x, y = self.board.move_to_location(move)
            self.board.add_move(x, y)
            winner = self.board.has_winner()
            if winner != -1:
                if not winner:
                    return winner
                if index % 2:
                    return 1 if winner == 2 else 2

    def start_self_play(self, player: 'MCTSPlayer', temp=1e-3):
        """ start a self-play game using a MCTS player, reuse the search tree
        store the self-play data: (state, mcts_probabilities, z)
        """
        self.board.initialize()
        states, mcts_probabilities, current_players = [], [], []
        while self.board.winner == -1:
            move, move_probabilities = player.get_action(self.board, temp=temp)
            # store the data
            states.append(self.board.get_current_state())
            mcts_probabilities.append(move_probabilities)
            current_players.append(self.board.get_current_player())
            # perform a move
            x, y = self.board.move_to_location(move)
            self.board.add_move(x, y)
            winner = self.board.has_winner()
            if winner != -1:
                # winner from the perspective of the current player of each state
                winners_z = np.zeros(len(current_players))
                if winner != -1:
                    winners_z[np.array(current_players) == winner] = 1.0
                    winners_z[np.array(current_players) != winner] = -1.0
                # reset MCTS root node
                player.reset_player()
                return zip(states, mcts_probabilities, winners_z)
