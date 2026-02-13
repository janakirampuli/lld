'''
Docstring for examples.tictactoe.main

symbol -> enum
player -> name, symbol
board -> board, move(), check(), show()
game -> manage game flow, player turns, decide winner/draw

'''

from enum import Enum
from typing import List

class Symbol(Enum):
    X = 'X'
    O = 'O'
    EMPTY = '-'

class GameException(Exception):
    pass

class InvalidMoveException(Exception):
    pass

class Player:
    def __init__(self, name: str, symbol: Symbol):
        self.name = name
        self.symbol = symbol

class Board:
    def __init__(self, size: int):
        self.size = size
        self.board: List[List[Symbol]] = [[Symbol.EMPTY for _ in range(3)] for _ in range(3)]
        self.move_count = 0

    def is_valid(self, x: int, y: int):
        return 0 <= x < self.size and 0 <= x < self.size
    
    def place(self, symbol: Symbol, x: int, y: int):
        if not self.is_valid(x, y):
            raise InvalidMoveException(f'Invalid coordinate')
        if self.board[x][y] != Symbol.EMPTY:
            raise InvalidMoveException('cell is occupied')
        self.board[x][y] = symbol
        self.move_count += 1
        
    def check_winner(self, x: int, y: int, symbol: Symbol):
        if all(self.board[x][c] == symbol for c in range(self.size)):
            return True
        
        if all(self.board[r][y] == symbol for r in range(self.size)):
            return True
        
        if x == y:
            if all(self.board[i][i] == symbol for i in range(self.size)):
                return True
            
        return False

    def check_full(self):
        return self.move_count == self.size * self.size


    def show(self):
        for i in self.board:
            print(" ".join([p.value for p in i]))
        print()

class Game:
    def __init__(self, size: int, player1: Player, player2: Player):
        self.player1 = player1
        self.player2 = player2
        self.board = Board(size)
        self.current_player = player1

    def move(self, player: Player, x: int, y: int):
        if self.current_player != player:
            raise InvalidMoveException(f"invalid player")
        
        self.board.place(player.symbol, x, y)

        if self.board.check_winner(x, y, player.symbol):
            print(f"{self.current_player.name} WON")
            print("board state: ")
            self.board.show()
            return
        if self.board.check_full():
            print(f"Game DRAW")
            print("board state: ")
            self.board.show()
            return
        
        if player == self.player2:
            self.current_player = self.player1
        else:
            self.current_player = self.player2
        print(f"Player {self.current_player.name} move")
        print("board state: ")
        self.board.show()
    
def demo():

    p1 = Player('A', Symbol.X)
    p2 = Player('B', Symbol.O)

    game = Game(3, p1, p2)
    game.move(p1, 0, 0)
    game.move(p2, 1, 0)
    game.move(p1, 0, 1)
    game.move(p2, 1, 1)
    game.move(p1, 0, 2)

    
if __name__ == "__main__":
    demo()