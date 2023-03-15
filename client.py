from text import *
from utils import recv, check_name
import socket, threading, sqlite3, time

class Client(threading.Thread):
    def __init__(self, sock: socket.socket, addr: tuple, lobby, c: sqlite3.Cursor, conn: sqlite3.Connection):
        super().__init__()
        print("New client created!")
        self.sock = sock
        self.addr = addr
        
        self.client_info = None

        self.lobby = lobby
        self.current_room = lobby
        self.c = c
        self.conn = conn

        self.rating = 1000

    def __setitem__(self, key, value):
        if not key in ["name", "rating", "wins", "losses", "draws"]:
            raise KeyError("Invalid key")
        
        self.client_info[key] = value
        self.c.execute("UPDATE users SET {}=? WHERE host=?".format(key), (value, self.addr[0]))
        self.conn.commit()

    def __getitem__(self, key):
        if not key in ["name", "rating", "wins", "losses", "draws"]:
            raise KeyError("Invalid key")
        
        if self.client_info is None:
            self.client_info = self.get_data()

        return self.client_info[key]

    def get_data(self):
        self.c.execute("SELECT * FROM users WHERE host=?", (self.addr[0],))
        data = self.c.fetchone()
        if data is None:
            return None
        
        return {
            "host": data[0],
            "name": data[1],
            "rating": data[2],
            "wins": data[3],
            "losses": data[4],
            "draws": data[5]
        }

    def run(self):

        found_user = self.get_data()

        if found_user is None:
            self.sock.sendall(NEW_USER.encode())

            while True:
                self.sock.sendall(ENTER_NAME.encode())                
                self.name = recv(self.sock)                

                result = check_name(self.name)
                if result == True:
                    self.sock.sendall(NAME_CONFIRM.format(self.name).encode())
                    choice = recv(self.sock)
                    
                    if choice == "y":
                        break
                
                if result == "char":
                    self.sock.sendall(INVALID_NAME_CHARS.encode())
                elif result == "length":
                    self.sock.sendall(INVALID_NAME_LENGTH.encode())
                elif result == "swear":
                    self.sock.sendall(INVALID_NAME_SWEAR.encode())
                
            # Add user to database
            self.c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (self.addr[0], self.name, self.rating, 0, 0, 0))
            self.conn.commit()
        
        else:
            self.name = found_user["name"]
            self.rating = found_user["rating"]

        # Add user to current room
        while True:
            
            if not self.current_room is None:
                self.current_room.add_user(self)
                self.current_room = None
            
            time.sleep(0.5)