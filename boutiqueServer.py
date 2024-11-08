import socket
import threading
import json
import sqlite3
import sys
import datetime

# Dictionaries that can be accessed across all threads
onlineUsers = {}
offlineUsers = {}
messages = {}
lock = threading.Lock()

# Initialize a SQLite database 
def initDb():
    dbConn = sqlite3.connect('auboutique.db')
    cursor = dbConn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            username TEXT UNIQUE,
            password TEXT,
            status TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            owner TEXT,
            description TEXT,
            buyer TEXT,
            status TEXT,
            picture TEXT,
            ETA REAL
        )
    ''')
    dbConn.commit()
    return dbConn

def currentOnlineUsers(user):
    currentTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with lock:
        onlineUsers[user]= f"Logged in on: {currentTime}"

def lastSeen(user):
    currentTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with lock:
        offlineUsers[user] = f"Last seen on: {currentTime}"

def handleClient(conn, addr):
    print(f"New connection: {addr}")
    username = None
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            method, path, body = parseRequest(data)
        
            if path == '/register' and method == 'POST':
                response = registerUser(json.loads(body))
                conn.send(response.encode())
            elif path == '/login' and method == 'POST':
                response, username = loginUser(json.loads(body))
                conn.send(response.encode())
                if "Login successful" in response:
                    currentOnlineUsers(username)
                    try:
                        del offlineUsers[username]
                    except KeyError:
                            pass
            elif path == '/logout' and method == 'POST':
                response = logoutUser(json.loads(body))
                conn.send(response.encode())
            elif path == '/add_product' and method == 'POST':
                response = addProduct(json.loads(body))
                conn.send(response.encode())
            elif path.startswith('/products') and method == 'GET':
                response = getProducts(path)
                conn.send(response.encode())
            elif path == '/buy_product' and method == 'POST':
                response = buyProduct(json.loads(body))
                conn.send(response.encode())
            elif path.startswith('/get_logs') and method == 'GET':
                response = getLogs(path)
                conn.send(response.encode())
            elif path == '/message' and method == 'POST':
                response = sendMessage(json.loads(body))
                conn.send(response.encode())
            elif path.startswith('/check_online') and method == 'GET':
                response = checkOnline(path)
                conn.send(response.encode())
            elif path.startswith('/check_inbox') and method == 'GET':
                response = inbox(path)
                conn.send(response.encode())
            else:
                conn.send("HTTP/1.1 404 Not Found\r\n\r\n".encode())
        
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
        conn.send(f"HTTP/1.1 500 Internal Server Error\r\n\r\n{str(e)}".encode())

    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                print(f"Error closing connection: {e}")

def parseRequest(request):
    lines = request.splitlines()
    method, path = lines[0].split(' ')[:2]
    body = lines[-1] if method == 'POST' else ''
    return method, path, body

# User Management
def registerUser(data):
    conn = initDb()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (name, email, username, password, status) VALUES (?, ?, ?, ?, ?)',
                       (data['name'], data['email'], data['username'], data['password'], 'offline'))
        conn.commit()
        return "HTTP/1.1 200 OK\r\n\r\nUser registered successfully."
    except sqlite3.IntegrityError:
        return "HTTP/1.1 400 Bad Request\r\n\r\nUsername already exists."
    finally:
        conn.close()

def loginUser(data):
    conn = initDb()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (data['username'], data['password']))
    user = cursor.fetchone()

    if user:
        cursor.execute('UPDATE users SET status="online" WHERE username=?', (data['username']))
        conn.commit()
        return "HTTP/1.1 200 OK\r\n\r\nLogin successful.", data['username']
    return "HTTP/1.1 401 Unauthorized\r\n\r\nInvalid credentials.", None


def logoutUser(data):
    conn = initDb()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=?', (data['username'],))
    user = cursor.fetchone()
    if user:
        cursor.execute('UPDATE users SET status="offline" WHERE username=?', (data['username'],))
        conn.commit()
        lastSeen(data['username'])
        onlineUsers.pop(data['username'], None)
        messages.pop(data['username'], None)
        return "HTTP/1.1 200 OK\r\n\r\nLogout successful."
    return "HTTP/1.1 400 Bad Request\r\n\r\nUser is not logged in."


# Product Management
def addProduct(data):
    conn = initDb()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, price, owner, description, buyer, status, picture, ETA) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (data['name'], data['price'], data['owner'], data['description'], None, 'available', data['picture'], data['ETA']))
    conn.commit()
    return "HTTP/1.1 200 OK\r\n\r\nProduct added successfully."

def getProducts(path):
    conn = initDb()
    cursor = conn.cursor()
    
    owner = None
    if '?' in path:
        params = path.split('?')[1]
        if params.startswith("owner="):
            owner = params.split("=")[1]
    
    if owner:
        cursor.execute('SELECT * FROM products WHERE status="available" AND owner=?', (owner,))
    else:
        cursor.execute('SELECT * FROM products WHERE status="available"')
    
    products = cursor.fetchall()
    productList = [{'id': p[0], 'name': p[1], 'price': p[2], 'owner': p[3], 'description': p[4], 'picture': p[7], 'ETA': p[8]} for p in products]
    return f"HTTP/1.1 200 OK\r\n\r\n{json.dumps(productList)}"

def buyProduct(data):
    conn = initDb()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM products WHERE id=?', (data['id'],))
    product = cursor.fetchone()

    if product:
        if product is None:
            return "HTTP/1.1 404 Not Found\r\n\r\nItem not found."

        if product[6] == "sold":
            return "HTTP/1.1 403 Forbidden\r\n\r\nItem has already been sold."

        cursor.execute('UPDATE products SET buyer=?, status="sold" WHERE id=?', (data['buyer'], data['id']))
        conn.commit()

        return f"HTTP/1.1 200 OK\r\n\r\nConfirmation: Collect from AUB Post Office in {product[7]} days."
    return "HTTP/1.1 404 Not Found\r\n\r\nItem not found."

# User Interaction
def getLogs(path):
    user = None
    if '?' in path:
        params = path.split('?')[1]
        if params.startswith("user="):
            user = params.split("=")[1]
    if user:
        if user in onlineUsers:
            with lock:  # Ensure thread safety
                return f"HTTP/1.1 200 OK\r\n\r\n{onlineUsers[user]}"
        elif user in offlineUsers:
            with lock:
                return f"HTTP/1.1 200 OK\r\n\r\n{offlineUsers[user]}"
        else: return "HTTP/1.1 404 Not Found\r\n\r\n"
    else: return "HTTP/1.1 400 Bad request\r\n\r\n"

def sendMessage(data):
    recipient = data.get('recipient')
    message = data.get('message')
    sender = data.get('sender')
    inboxMessage = f"Message from {sender}: {message}"
    if recipient in onlineUsers.keys():
        messages[recipient] = []
        messages[recipient].append(inboxMessage)
        return "HTTP/1.1 200 OK\r\n\r\nMessage sent."
    return "HTTP/1.1 404 Not Found\r\n\r\nRecipient not online."

def checkOnline(path):
   conn = initDb()
   cursor = conn.cursor()
   username = None
   if '?' in path:
        params = path.split('?')[1]
        if params.startswith("username="):
            username = params.split("=")[1]
   cursor.execute("SELECT * FROM users WHERE username=?", (username,))
   user = cursor.fetchone()
   if user:
        status = "online" if username in onlineUsers.keys() else "offline"
        return f"HTTP/1.1 200 OK\r\n\r\n{username} is {status}."
   else:
       return "HTTP/1.1 404 Not Found\r\n\r\nUser not found."
   
def inbox(path):
    user = None
    if '?' in path:
        params = path.split('?')[1]
        if params.startswith("username="):
            user = params.split("=")[1]
    if user in messages and messages[user]:
        inboxMessages= "\n".join(messages[user])
        return f"HTTP/1.1 200 OK\r\n\r\n{inboxMessages}"
    else:
        return "HTTP/1.1 404 Not Found\r\n\r\nNo messages in your inbox."

# Server Initialization
def startServer(port):
    initDb()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', port))
    server_socket.listen(5)
    print(f"Server listening on port: {port}")
    while True:
        conn, addr = server_socket.accept()
        client_thread = threading.Thread(target=handleClient, args=(conn, addr))
        client_thread.start()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("To run the server please add a valid port number. (python boutiqueServer.py <port>)")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        startServer(port)
    except ValueError:
        print("Invalid port number. Please provide an integer.")
        sys.exit(1)
