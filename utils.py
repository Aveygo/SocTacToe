import socket 

VALID_ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
VALID_NUM = "0123456789"
VALID_SPECIAL = "\\_[]"
VALID_CHARS = VALID_ALPHA + VALID_NUM + VALID_SPECIAL
BANNED = ["admin", "cock", "dick", "fuck", "bitch", "nigger", "pussy", "shit", "wank", "ass", "arse", "\n", "\r"]

def recv(sock:socket.socket, size:int=1024) -> str:
    # Telnet sends char-by-char and netcat sends line-by-line
    message = ""
    while True:
        data = sock.recv(size).decode()
        # Check for backspace
        if data == "\x08":
            message = message[:-1]
            continue

        message += data
        if data.endswith("\r\n"):
            break
    return message.strip()


def check_name(name:str) -> str:
    """
    Check if a name is valid.
    :param name: The name to check
    :return: True if the name is valid, otherwise a string describing the error
    """
    for char in name:
        if char not in VALID_CHARS:
            return "char"
    
    if len(name) > 32:
        return "length"
    
    if len(name) < 3:
        return "length"
    
    for swear in BANNED:
        if swear in "".join([i for i in name.lower() if i in VALID_ALPHA]):
            return "swear"
    
    return True

def elo(player1_rating:float, player2_rating:float, winner:int) -> tuple:
    """
    Calculate the new ratings for two players.
    :param player1_rating: The rating of player 1
    :param player2_rating: The rating of player 2
    :param winner: The winner of the game. 1 for player 1, 2 for player 2, 0 for a draw.
    :return: The new ratings for both players
    """
    if winner not in [0, 1, 2]:
        raise ValueError("winner must be 0, 1, or 2")
    
    expected_score_player1 = 1 / (1 + 10 ** ((player2_rating - player1_rating) / 400))
    expected_score_player2 = 1 / (1 + 10 ** ((player1_rating - player2_rating) / 400))
    
    if winner == 1:
        player1_rating += 32 * (1 - expected_score_player1)
        player2_rating += 32 * (0 - expected_score_player2)
    elif winner == 2:
        player1_rating += 32 * (0 - expected_score_player1)
        player2_rating += 32 * (1 - expected_score_player2)
    else:
        player1_rating += 32 * (0.5 - expected_score_player1)
        player2_rating += 32 * (0.5 - expected_score_player2)
    
    return player1_rating, player2_rating
