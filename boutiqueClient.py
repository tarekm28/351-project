import socket
import json

def sendRequest(request):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 12345)) 

        client_socket.send(request.encode())
        response = client_socket.recv(4096).decode()
        client_socket.close()
        return response
    except Exception as e:
        print(f"Error during request: {e}")
        return None

def register():
    name = input("Enter your name: ")
    email = input("Enter your email: ")
    username = input("Choose a username: ")
    password = input("Choose a password: ")
    data = json.dumps({"name": name, "email": email, "username": username, "password": password})
    request = f"POST /register HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
    print(sendRequest(request))

def login():
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    data = json.dumps({"username": username, "password": password})
    request = f"POST /login HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
    response = sendRequest(request)
    if response and "200 OK" in response:
        print("Login successful!")
        menuAfterLogin(username)
    else:
        print("Login failed!")

def logoutUser(username):
    data = json.dumps({"username": username})
    request = f"POST /logout HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
    response = sendRequest(request)
    if response and "Logout successful" in response:
        print("Logged out successfully.")
    else:
        print("Logout failed.")

def menuAfterLogin(username):
    while True:
        print("\n1. View All Products\n2. View Products by Owner\n3. Add Product\n4. Buy Product\n5. Check Logs\n6. Send Message\n7. Check Online Status\n8. Check Inbox\n9. Log Out")
        choice = input("Choose an option: ")
        if choice == '1':
            viewProducts()
        elif choice == '2':
            owner = input("Enter owner username: ")
            viewProducts(owner)
        elif choice == '3':
            addProduct(username)
        elif choice == '4':
            buyProduct(username)
        elif choice == '5':
            checkLogs()
        elif choice == '6':
            sendMessage(username)
        elif choice == '7':
            checkOnline()
        elif choice == '8':
            checkInbox(username)
        elif choice == '9':
            logoutUser(username)
            username = None
            return

def viewProducts(owner=None):
    request = f"GET /products{'?owner=' + owner if owner else ''} HTTP/1.1\r\n\r\n"
    response = sendRequest(request)
    print(response)

def addProduct(owner):
    name = input("Enter product name: ")
    price = input("Enter product price: ")
    description = input("Enter product description: ")
    picture = input("Enter product picture URL: ") 
    eta = input("Enter ETA in days: ") 
    data = json.dumps({"name": name, "price": price, "owner": owner, "description": description, "picture": picture, "ETA": eta}) 
    request = f"POST /add_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}" 
    print(sendRequest(request))

def buyProduct(buyer): 
    productId = int(input("Enter product ID to buy: ")) 
    data = json.dumps({"id": productId, "buyer": buyer}) 
    request = f"POST /buy_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
    
    response = sendRequest(request)
    print(response)

def checkLogs():
    username = input("Enter username: ")
    request = f"GET /get_logs?user={username} HTTP/1.1\r\n\r\n"
    response = sendRequest(request)
    print(response)


def sendMessage(username): 
    sender = username
    recipient = input("Enter recipient username: ") 
    message = input("Enter your message: ") 
    data = json.dumps({"recipient": recipient, "message": message, "sender": sender}) 
    request = f"POST /message HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}" 
    print(sendRequest(request))

def checkOnline():
    username = input("Enter username to check status: ")
    request = f"GET /check_online?username={username} HTTP/1.1\r\n\r\n"
    response = sendRequest(request)
    print(response)

def checkInbox(username):
    request = f"GET /check_inbox?username={username} HTTP/1.1\r\n\r\n"
    response = sendRequest(request)
    print(response)

def mainMenu(): 
    while True: 
        print("\n1. Register\n2. Login\n3. Exit") 
        choice = input("Choose an option: ") 
        if choice == '1':
            register() 
        elif choice == '2':
            login() 
        elif choice == '3':
            break

if __name__ == "__main__":
    mainMenu()
