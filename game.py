from client import Client
import socket, threading, random, time
from utils import elo
from text import *
from utils import recv

class Game(threading.Thread):
    def __init__(self, player1:Client, player2:Client):
        super().__init__()

        # Shuffle the players so that the first player is random
        players = [player1, player2]
        random.shuffle(players)
        self.player1 = players[0]
        self.player2 = players[1]
        
        # Tic tac toe board, X is always player1, O is always player2,
        # However, the board is rendered as X from the player's perspective
        self.board = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

        # Random id for debugging
        self.id_ = random.randint(9999, 99999)

        # Game states
        self.finished = False
        self.draw = False
        self.winner = None
        self.closed = False

        # Lobby will end the game after 90 seconds
        self.start_time = time.time() 
    
    def end_game(self, elo_result=0):
        if self.closed:
            return
        
        if self.draw or self.winner is None:
            elo_result = 0
            self.player1["draws"] += 1
            self.player2["draws"] += 1
        else:
            if self.winner == "X":
                elo_result = 1
                self.player1["wins"] += 1
                self.player2["losses"] += 1
            else:
                elo_result = 2
                self.player2["wins"] += 1
                self.player1["losses"] += 1
            
        # Calculate rating
        player1_new_rating, player2_new_rating = elo(self.player1["rating"], self.player2["rating"], elo_result)
        
        # Show rating change        
        player1_delta = int(player1_new_rating - self.player1["rating"])
        player2_delta = int(player2_new_rating - self.player2["rating"])
        player1_delta = f"+{player1_delta}" if player1_delta > 0 else f"{player1_delta}"
        player2_delta = f"+{player2_delta}" if player2_delta > 0 else f"{player2_delta}"

        try:
            self.player1.sock.sendall(GAME_END.format(
                "WIN" if self.winner == "X" else "LOSS" if self.winner == "O" else "ABANDONED" if self.winner == None else "DRAW",
                f"{self.player1['name']} ({round(self.player1['rating'])} {player1_delta})",
                f"{self.player2['name']} ({round(self.player2['rating'])} {player2_delta})"
            ).encode())
            self.player1["rating"] = player1_new_rating
            self.player1.current_room = self.player1.lobby
        except Exception as e:
            print("Player1", e)
        try:    
            self.player2.sock.sendall(GAME_END.format(
                "WIN" if self.winner == "O" else "LOSS" if self.winner == "X" else "ABANDONED" if self.winner == None else "DRAW",
                f"{self.player2['name']} ({round(self.player2['rating'])} {player2_delta})",
                f"{self.player1['name']} ({round(self.player1['rating'])} {player1_delta})"
            ).encode())
            self.player2["rating"] = player2_new_rating
            self.player2.current_room = self.player2.lobby
        except Exception as e:
            print("Player2", e)
            
        self.closed = True
    
    def stop(self):
        self.finished = True
        self.winner = None
        self.end_game()
    
    def check_state(self) -> bool:
        """
        Returns True if the game is finished, otherwise False
        """
        # Check rows
        for i in range(0, 9, 3):
            if self.board[i] == self.board[i+1] == self.board[i+2]:
                self.finished = True
                self.winner = self.board[i]
                return True
            
        # Check columns
        for i in range(3):
            if self.board[i] == self.board[i+3] == self.board[i+6]:
                self.finished = True
                self.winner = self.board[i]
                return True

        # Check diagonals
        if self.board[0] == self.board[4] == self.board[8]:
            self.finished = True
            self.winner = self.board[0]
            return True
        
        if self.board[2] == self.board[4] == self.board[6]:
            self.finished = True
            self.winner = self.board[2]
            return True
        
        # Check if the game is a draw
        if not any(i.isdigit() for i in self.board):
            self.finished = True
            self.draw = True
            return True
        
        return False
            
    def render(self, perspective:int):
        if perspective == 1:
            # Player 1's perspective, do nothing
            board = self.board
        else:
            # Player 2's perspective, swap X and O
            board = []
            for i in self.board:
                if i == "X":
                    board.append("O")
                elif i == "O":
                    board.append("X")
                else:
                    board.append(i)
        
        return "\r\n" + BOARD.format(*board) + "\r\n"

    def get_move(self, socket):
        while not self.finished:
            socket.sendall(MOVE_REQUEST.encode())
            move = recv(socket)
            if move not in self.board or not move.isdigit():
                socket.sendall(INVALID_MOVE.encode())
                continue
            break
        return move

    def game_loop(self):
        # Send to player 1 that they are starting first 
        self.player1.sock.sendall(MOVING_FIRST.encode())
        
        # Send boards to players
        self.player1.sock.sendall(self.render(1).encode())
        self.player2.sock.sendall(self.render(2).encode())
        
        while not self.finished:

            # Send to player 2 that they are waiting for player 1 to move
            self.player2.sock.sendall(WAITING_FOR_OPPONENT.encode())
            
            # Get player 1's move
            move = self.get_move(self.player1.sock)
            self.board[int(move)-1] = "X"

            # Send boards to players
            self.player1.sock.sendall(self.render(1).encode())
            self.player2.sock.sendall(self.render(2).encode())

            # Check the state
            state = self.check_state()
            if state:
                break

            # Send to player 1 that they are waiting for player 2 to move
            self.player1.sock.sendall(WAITING_FOR_OPPONENT.encode())

            # Get player 2's move
            move = self.get_move(self.player2.sock)
            self.board[int(move)-1] = "O"

            # Send boards to players
            self.player1.sock.sendall(self.render(1).encode())
            self.player2.sock.sendall(self.render(2).encode())

            # Check the state
            state = self.check_state()
            if state:
                break

    def run(self):
        # Test game
        self.player1.sock.sendall(GAME_START.format(
            self.id_,
            f'{self.player1["name"]} ({round(self.player1["rating"])})',
            f'{self.player2["name"]} ({round(self.player2["rating"])})'
        ).encode())
        self.player2.sock.sendall(GAME_START.format(
            self.id_,
            f'{self.player2["name"]} ({round(self.player2["rating"])})',
            f'{self.player1["name"]} ({round(self.player1["rating"])})'
        ).encode())

        # Game loop
        try:
            self.game_loop()
        except Exception as e:
            print(e)
            self.stop()

        self.end_game()

       

