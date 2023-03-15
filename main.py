# Simple lobby with socket
# User enters name and is added to the lobby to wait
import socket, sqlite3
from lobby import Lobby
from client import Client

conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (host text, name text, rating real, wins integer, losses integer, draws integer)")
conn.commit()

# Add the admin account if it doesn't exist
admin_name = "\033[31madmin\033[0m"
c.execute("SELECT * FROM users WHERE name=?", (admin_name,))
if c.fetchone() is None:
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", ("127.0.0.1", admin_name, 1000, 0, 0, 0))
    conn.commit()

lobby = Lobby(c, conn)
lobby.start()

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to the port
server_address = (socket.gethostbyname(socket.gethostname()), 8000)
print('Starting up on {} port {}...'.format(*server_address))
print("telnet " + socket.gethostbyname(socket.gethostname()) + " 8000")
sock.bind(server_address)

# Listen for incoming connections
sock.listen(10)

while True:
    # Wait for a connection
    print('Waiting for a connection...')
    connection, client_address = sock.accept()
    try:
        print('Connection from', client_address)
        client = Client(connection, client_address, lobby, c, conn)
        client.start()
    except:
        connection.close()