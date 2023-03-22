# Simple http server / file requestor with python sockets
import socket, os

# Create a socket object
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Get local machine name and port
host, port = "0.0.0.0", 80

# Bind to the port
s.bind((host, port))

# Now wait for client connection.
s.listen(5)

print('Listening...')

while True:
    # Establish connection with client.
    c, addr = s.accept()

    # Receive data from client (request)
    data = c.recv(1024)

    try:
        # Parse data to get file name
        filename = data.split()[1].decode()[1:]

        # Common practice to return index.html if no file is specified
        if filename == "":
            filename = "index.html"

        # Check if file exists
        if not os.path.exists(filename):
            c.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
        else:
            
            print("Requesting file: " + filename)

            # Set mimetype based on file extension
            mimetype = "text/" + filename.split(".")[-1]

            # Open file
            data = open(filename, "rb").read()

            # Send HTTP header into socket
            c.send(b"HTTP/1.1 200 OK\r\n")
            c.send(b"Content-Type: " + mimetype.encode() + b"\r\n")
            c.send(b"\r\n")

            # Send the content of the requested file to the client
            c.send(data)
            
            # End response
            c.send(b"\r\n")

    except Exception as e:
        # return 404 error
        c.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
    
    # Close connection
    c.close()
