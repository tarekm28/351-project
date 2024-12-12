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
userInfo = {}
lock = threading.Lock()

# Initialize a SQLite database 
def initDb():
    dbConn = sqlite3.connect('auboutique.db')
    cursor = dbConn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        username TEXT UNIQUE,
        password TEXT,
        status TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        owner TEXT,
        description TEXT,
        buyer TEXT,
        status TEXT,
        picture TEXT,
        ETA REAL,
        quantity INTEGER,
        rating REAL,  
        num_ratings INTEGER
    )''')
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
    ip, port = addr
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
                    with lock:
                        userInfo[username] = (ip, port)
                    peerListener(ip, port)
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
            elif path == '/modify_product' and method == 'POST':
                response = modifyProduct(json.loads(body))
                conn.send(response.encode())
            elif path.startswith('/search_product') and method == 'GET':
                response = searchProducts(path)
                conn.send(response.encode())    
            elif path == '/delete_product' and method == 'POST':
                response = deleteProduct(json.loads(body))
                conn.send(response.encode())
            elif path == '/rate_product' and method == 'POST':
                response = rateProduct(json.loads(body))
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
            elif path.startswith('/get_peer_info') and method == 'GET':
                response = getPeerInfo(path)
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
        cursor.execute('UPDATE users SET status="online" WHERE username=?', (data['username'],))
        conn.commit()
        lol = str(userInfo)
        return f"HTTP/1.1 200 OK\r\n\r\nLogin successful!", data['username']
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
    cursor.execute('INSERT INTO products (name, price, owner, description, buyer, status, picture, ETA, quantity, rating, num_ratings) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (data['name'], data['price'], data['owner'], data['description'], None, 'available', data['picture'], data['ETA'], data['quantity'], 0.0, 0))
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
    productList = [{'id': p[0], 'name': p[1], 'price': p[2], 'owner': p[3], 'description': p[4], 'picture': p[7], 'ETA': p[8], 'quantity': p[9], 'average rating': p[10], 'number of ratings': p[11]} for p in products]
    formattedProductList = "\n".join([json.dumps(product) for product in productList])
    return f"HTTP/1.1 200 OK\r\n\r\n{formattedProductList}"

def modifyProduct(data):
    conn = initDb()
    cursor = conn.cursor()
    productID = data['product_id']
    owner = data['owner']
    cursor.execute('SELECT * FROM products WHERE id=? AND owner=?', (productID,owner))
    product = cursor.fetchone()

    if product:
        newName = data.get('new_name')
        newPrice = data.get('new_price')
        newDesc = data.get('new_desc')
        newPic = data.get('new_pic')
        newETA = data.get('new_eta')

        if newName:
            cursor.execute('UPDATE products SET name=? WHERE id=?', (newName, data['product_id']))
            conn.commit()
        elif newPrice:
            cursor.execute('UPDATE products SET price=? WHERE id=?', (newPrice, data['product_id']))
            conn.commit()
        elif newDesc:
            cursor.execute('UPDATE products SET description=? WHERE id=?', (newDesc, data['product_id']))
            conn.commit()
        elif newPic:
            cursor.execute('UPDATE products SET picture=? WHERE id=?', (newPic, data['product_id']))
            conn.commit()
        elif newETA:
            cursor.execute('UPDATE products SET ETA=? WHERE id=?', (newETA, data['product_id']))
            conn.commit()
        return "HTTP/1.1 200 OK\r\n\r\nProduct modified successfully."
    return "HTTP/1.1 401 Unauthorized\r\n\r\nYou cannot modify a product that you haven't listed."

def deleteProduct(data):
    conn = initDb()
    cursor = conn.cursor()
    productID = data['product_id']
    owner = data['owner']
    cursor.execute('SELECT * FROM products WHERE id=? AND owner=?', (productID, owner))
    product = cursor.fetchone()

    if product:
        cursor.execute('DELETE FROM products WHERE id=?', (productID,))
        conn.commit()
        return "HTTP/1.1 200 OK\r\n\r\nProduct deleted successfully."
    return "HTTP/1.1 401 Unauthorized\r\n\r\nYou cannot delete a product that you haven't listed."



def searchProducts(path):
    conn = initDb()
    cursor = conn.cursor()
    search_term = None
    if '?' in path:
        params = path.split('?')[1]
        if params.startswith("product="):
            search_term = params.split("=")[1]
    cursor.execute('SELECT * FROM products WHERE name LIKE ? OR description LIKE ?',
                   ('%' + search_term + '%', '%' + search_term + '%'))
    products = cursor.fetchall()
    productList = [{'id': p[0], 'name': p[1], 'price': p[2], 'owner': p[3], 'description': p[4], 'picture': p[7], 'ETA': p[8], 'quantity': p[9], 'average rating': p[10], 'number of ratings': p[11]} for p in products]
    formattedProductList = "\n".join([json.dumps(product) for product in productList])
    return f"HTTP/1.1 200 OK\r\n\r\n{formattedProductList}"


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
        
        if product[9] <= 0:
            return "HTTP/1.1 403 Forbidden\r\n\r\nItem is out of stock."


        cursor.execute('UPDATE products SET buyer=?, quantity=quantity - 1 WHERE id=?', (data['buyer'], data['id']))
        if product[9] <= 0:
            cursor.execute('UPDATE products SET buyer=?, status="sold" WHERE id=?', (data['buyer'], data['id']))
            conn.commit() 

        conn.commit()

        return f"HTTP/1.1 200 OK\r\n\r\nConfirmation: Collect from AUB Post Office in {product[8]} days."
    return "HTTP/1.1 404 Not Found\r\n\r\nItem not found."

def rateProduct(data):
    conn = initDb()
    cursor = conn.cursor()
    productId = data['product_Id']
    rating = int(data['rating'])
    cursor.execute('SELECT * FROM products WHERE id=?', (productId,))
    product = cursor.fetchone()

    if product:
        currentRating = float(product[10])
        numRatings = int(product[11])
        newAvgRating = ((currentRating * numRatings) + rating) / (numRatings + 1)
        cursor.execute('UPDATE products SET rating=?, num_ratings=? WHERE id=?',
                       (newAvgRating, numRatings + 1, productId))
        conn.commit()
        return "HTTP/1.1 200 OK\r\n\r\nProduct rated successfully."
    return "HTTP/1.1 404 Not Found\r\n\r\nProduct not found."

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

def getPeerInfo(path):
    user = None
    if '?' in path:
        params = path.split('?')[1]
        if params.startswith("username="):
            user = params.split("=")[1]
    
    if user in userInfo and user in onlineUsers:
        ip, port = userInfo[user]
        return f"HTTP/1.1 200 OK\r\n\r\n {ip}:{port}"
    else:
        return "HTTP/1.1 404 Not Found\r\n\r\nUser is offline"

def peerListener(ip, port):
    listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener_socket.bind((ip, port))
    listener_socket.listen(5)

    while True:
        conn, addr = listener_socket.accept()
        print(f"Connected to {addr}")
        threading.Thread(target=handlePeerChat, args=(conn)).start()

def handlePeerChat(conn):
    information = conn.recv(4096).decode()
    print(information)
    username = information.split(" ")[4]
    while True:
        try:
            message = conn.recv(4096).decode()
            if not message:
                break
            if message == "Direct chat ended by peer":
                    print(message)
                    break
            print(f"{username}: {message}")
            response = input("You: ")
            if message.lower() == "exit":
                    print("Ending chat...")
                    conn.send("Direct chat ended by peer".encode())
                    break
            conn.send(response.encode())
        except Exception as e:
            print(f"Connection error with {username}: {e}")
            break
    conn.close()

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
