import socket
import json
import requests

APIKEY = "89cd9e589023eac2448f7f02"
EXCHANGERATEURL = "https://v6.exchangerate-api.com/v6/{}/latest/{}"
currency = "USD"

def sendRequest(request):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 1237)) 

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
    if response and ("successful" not in response):
        print("Login failed!")
    else:
        print(response)
        menuAfterLogin(username)

def logoutUser(username):
    data = json.dumps({"username": username})
    request = f"POST /logout HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
    response = sendRequest(request)
    if response and "Logout successful" in response:
        print("Logged out successfully.")
    else:
        print("Logout failed.")

def menuAfterLogin(username):
    currency="USD"
    while True:
        print("\n1. View All Products\n2. View Products by Owner\n3. Change currency\n4. Add Product\n5. Modify Your Product\n6. Search for a Product\n7. Buy Product\n8. Rate Product\n9. Check Logs\n10. Send Message\n11. Check Online Status\n12. Check Inbox\n13. Log Out")
        choice = input("Choose an option: ")
        if choice == '1':
            viewProducts(None, currency)
        elif choice == '2':
            owner = input("Enter owner username: ")
            viewProducts(owner, currency)
        elif choice == '3':
            currency = input("Enter preffered currency for prices: ")
        elif choice == '4':
            addProduct(username)
        elif choice == '5':
            modifyproduct(username)
        elif choice == '6':
            searchProduct()    
        elif choice == '7':
            buyProduct(username)
        elif choice == '8':
            rateProduct()
        elif choice == '9':    
            checkLogs()
        elif choice == '10':
            sendMessage(username)
        elif choice == '11':
            checkOnline()
        elif choice == '12':
            checkInbox(username)
        elif choice == '13':
            logoutUser(username)
            username = None
            return


def getExchangeRates(base_currency="USD"):
    try:
        response = requests.get(EXCHANGERATEURL.format(APIKEY, base_currency))
        if response.status_code == 200:
            return response.json().get("conversion_rates", {})
        else:
            print(f"Error fetching exchange rates: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
        return {}

def convertCurrency(amount, oldCurrency, newCurrency):
    rates = getExchangeRates(oldCurrency)
    if rates and newCurrency in rates:
        return round(amount * rates[newCurrency], 2)
    print(f"Conversion failed. Rates not available for {newCurrency}")
    return None

def viewProducts(owner, currency):
    request = f"GET /products{'?owner=' + owner if owner else ''} HTTP/1.1\r\n\r\n"
    response = sendRequest(request)
    if response and currency != "USD":
        try:
            jsonStart = response.find("\r\n\r\n") + 4
            jsonBody = response[jsonStart:]
            productList = json.loads(jsonBody)
            for product in productList:
                usdPrice = product['price']
                newPrice = convertCurrency(usdPrice, "USD", currency)
                product['price'] = f"{newPrice}" if newPrice else "N/A"
            print("[" + ", \n".join([json.dumps(product) for product in productList]) +']')
        except Exception as e:
            print(f"Error displaying products: {e}")
    elif response and currency == "USD":
        print(response)
    else:
        print("Failed to fetch products.")

def addProduct(owner):
    name = input("Enter product name: ")
    price = input("Enter product price: ")
    description = input("Enter product description: ")
    picture = input("Enter product picture URL: ") 
    eta = input("Enter ETA in days: ")
    quantity = input("Enter quantity of product: ") 
    data = json.dumps({"name": name, "price": price, "owner": owner, "description": description, "picture": picture, "ETA": eta, "quantity": quantity}) 
    request = f"POST /add_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}" 
    print(sendRequest(request))

def modifyproduct(username):
    viewProducts(username, currency)
    productId = input("Enter the ID of the product you'd like to modify: ")
    print("\n1. Change the name of your product\n2. Change the price of your product\n3. Change the description of your product\n4. Change your product's picture\n5. Change the ETA of your product\n6. Remove your product")
    choice = input("Choose an option: ")
    while choice != '6':
        if choice == '1':
                newName = input("Enter a new name for your product:")
                data = json.dumps({"new_name": newName, "product_id": productId, "owner": username})
        elif choice == '2':
            newPrice = input("Enter a new price for your product: ")
            data = json.dumps({"new_price": newPrice, "product_id": productId, "owner": username})
        elif choice == '3':
            newDesc = input("Enter a new description for your product: ")
            data = json.dumps({"new_desc": newDesc, "product_id": productId, "owner": username})
        elif choice == '4':
            newPic = input("Enter a new URL for your product's picture: ")
            data = json.dumps({"new_pic": newPic, "product_id": productId, "owner": username})
        elif choice == '5':
            newETA = input("Enter a new ETA for your product: ")
            data = json.dumps({"new_eta": newETA, "product_id": productId, "owner": username}) 
        
        request = f"POST /modify_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}" 
        print(sendRequest(request))
        break
    
    if choice == '6':
        deleteData = (username, productId)
        deleteProduct(deleteData)

def searchProduct():
    product = input("Enter product name to search: ")
    request = f"GET /search_products?product={product} HTTP/1.1\r\n\r\n"
    response = sendRequest(request)
    print(response)

def buyProduct(buyer): 
    productId = int(input("Enter product ID to buy: ")) 
    data = json.dumps({"id": productId, "buyer": buyer}) 
    request = f"POST /buy_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
    
    response = sendRequest(request)
    print(response)

def rateProduct():
    productId = input("Enter product ID to rate: ")
    rating = input("Enter rating (1-10): ")
    data = json.dumps({"product_Id": productId, "rating": rating})
    request = f"POST /rate_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
    print(sendRequest(request))

def deleteProduct(deleteData):
    data = json.dumps({"product_id": deleteData[1], "owner": deleteData[0]})
    request = f"POST /delete_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
    print(sendRequest(request))


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

def getPeerInfo(username):
    request = f"GET /get_peer_info?username={username} HTTP/1.1\r\n\r\n"
    response = sendRequest(request)
    if "200 OK" in response:
        return response.split("\r\n\r\n")[1]

def directChat(recipient, username): 
    peerInfo = getPeerInfo(recipient)
    if peerInfo:
        ip, port = peerInfo.split(":")
        port = int(port)
        print(ip, port)
        peerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peerSocket.connect((ip, port))
        print(f"You are now chatting with {recipient}, type 'exit' to end the chat.")
        peerSocket.send(f"You are now chatting with {username}, type 'exit' to end chat.")
        while True:
            try:
                message = input(f"{username}: ")
                if message.lower() == "exit":
                        print("Ending chat...")
                        peerSocket.send("Direct chat ended by peer".encode())
                        break
                peerSocket.send(message.encode())
                response = peerSocket.recv(4096).decode()
                if response == "Direct chat ended by peer":
                    print(response)
                    break
                print(f"{recipient}: {response}")
            except Exception as e:
                print(f"Connection error with {username}: {e}")
                break
        peerSocket.close()


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
