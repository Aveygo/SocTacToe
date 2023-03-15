from utils import recv
import socket, threading, time, sqlite3, random
from text import *
from client import Client
from game import Game

class Lobby(threading.Thread):
    def __init__(self, c: sqlite3.Cursor, conn: sqlite3.Connection):
        super().__init__()
        self.clients:list[Client] = []
        self.games:list[Game] = []
        self.c = c
        self.conn = conn
    
    def add_user(self, client:Client):
        
        print(f"Added {client['name']} to lobby")
        
        client.sock.sendall(MAIN_MENU.format(
            client["name"], 
            round(client["rating"]),
            client["wins"],
            len(self.clients)
        ).encode())

        client.sock.sendall(ANY_KEY.encode())
        recv(client.sock)
        client.sock.sendall(LOBBY.encode())
        self.clients.append(client)
    
    def check_game(self, game:Game):
        # Check if game is running for too long
        if game.start_time + 80 < time.time():
            game.stop()
            self.games.remove(game)
            return
        
        # Check if both players respond to empty send
        try:
            game.player1.sock.sendall(b"")
            game.player2.sock.sendall(b"")
        except:
            game.stop()
            self.games.remove(game)
            return

        # Check if game is closed (client have ended the game)
        if game.closed:
            self.games.remove(game)
            return

    def run(self):
        while True:
            # Sort clients by rating
            clients = sorted(self.clients, key=lambda client: client["rating"], reverse=True)
            
            # Group clients into games of 2
            games = []
            for i in range(0, len(clients), 2):
                games.append(clients[i:i+2])

            # Send games to clients
            for game_room in games:
                if len(game_room) == 2:
                    
                    # Disconnect clients from lobby
                    self.clients.remove(game_room[0])
                    self.clients.remove(game_room[1])

                    # Create a game
                    game = Game(game_room[0], game_room[1])
                    game.start()
                    self.games.append(game)
            
            # Check if games are still running
            for game in self.games:
                self.check_game(game)

            time.sleep(5)