from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QMessageBox, QInputDialog, QTextEdit, QDialog,
)
import sys
import socket
import json
import requests


APIKEY = "89cd9e589023eac2448f7f02"
EXCHANGERATEURL = "https://v6.exchangerate-api.com/v6/{}/latest/{}"

class AUBoutiqueClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUBoutique Client")
        self.setGeometry(100, 100, 600, 400)
        self.current_user = None
        self.currency = "USD"
        self.init_login_ui()

    def init_login_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.label = QLabel("Welcome to AUBoutique", self)
        self.layout.addWidget(self.label)

        self.register_button = QPushButton("Register", self)
        self.register_button.clicked.connect(self.register)
        self.layout.addWidget(self.register_button)

        self.login_button = QPushButton("Login", self)
        self.login_button.clicked.connect(self.login)
        self.layout.addWidget(self.login_button)

    def init_main_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.label = QLabel(f"Welcome, {self.current_user}", self)
        self.layout.addWidget(self.label)

        self.view_products_button = QPushButton("View All Products", self)
        self.view_products_button.clicked.connect(self.view_products)
        self.layout.addWidget(self.view_products_button)

        self.view_owner_products_button = QPushButton("View Products by Owner", self)
        self.view_owner_products_button.clicked.connect(self.view_products_by_owner)
        self.layout.addWidget(self.view_owner_products_button)

        self.change_currency_button = QPushButton("Change Currency", self)
        self.change_currency_button.clicked.connect(self.change_currency)
        self.layout.addWidget(self.change_currency_button)

        self.add_product_button = QPushButton("Add Product", self)
        self.add_product_button.clicked.connect(self.add_product)
        self.layout.addWidget(self.add_product_button)

        self.modify_product_button = QPushButton("Modify Your Product", self)
        self.modify_product_button.clicked.connect(self.modify_product)
        self.layout.addWidget(self.modify_product_button)

        self.search_product_button = QPushButton("Search for a Product", self)
        self.search_product_button.clicked.connect(self.search_product)
        self.layout.addWidget(self.search_product_button)

        self.buy_product_button = QPushButton("Buy Product", self)
        self.buy_product_button.clicked.connect(self.buy_product)
        self.layout.addWidget(self.buy_product_button)

        self.rate_product_button = QPushButton("Rate Product", self)
        self.rate_product_button.clicked.connect(self.rate_product)
        self.layout.addWidget(self.rate_product_button)

        self.check_logs_button = QPushButton("Check Logs", self)
        self.check_logs_button.clicked.connect(self.check_logs)
        self.layout.addWidget(self.check_logs_button)

        self.send_message_button = QPushButton("Send Message", self)
        self.send_message_button.clicked.connect(self.send_message)
        self.layout.addWidget(self.send_message_button)

        self.check_online_button = QPushButton("Check Online Status", self)
        self.check_online_button.clicked.connect(self.check_online_status)
        self.layout.addWidget(self.check_online_button)

        self.check_inbox_button = QPushButton("Check Inbox", self)
        self.check_inbox_button.clicked.connect(self.check_inbox)
        self.layout.addWidget(self.check_inbox_button)

        self.direct_chat_button = QPushButton("Direct Chat (P2P)", self)
        self.direct_chat_button.clicked.connect(self.show_direct_chat_message)
        self.layout.addWidget(self.direct_chat_button)

        self.logout_button = QPushButton("Log Out", self)
        self.logout_button.clicked.connect(self.logout)
        self.layout.addWidget(self.logout_button)

    def switch_to_main_ui(self):
        self.init_main_ui()

    def send_request(self, request):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', 1237)) 
            client_socket.send(request.encode())
            response = client_socket.recv(4096).decode()
            client_socket.close()
            return response
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect to server: {e}")
            return None

    def register(self):
        name, ok = QInputDialog.getText(self, "Register", "Enter your name:")
        if not ok or not name:
            return
        
        email, ok = QInputDialog.getText(self, "Register", "Enter your email:")
        if not ok or not email:
            return

        username, ok = QInputDialog.getText(self, "Register", "Choose a username:")
        if not ok or not username:
            return

        password, ok = QInputDialog.getText(self, "Register", "Choose a password:")
        if not ok or not password:
            return

        data = json.dumps({"name": name, "email": email, "username": username, "password": password})
        request = f"POST /register HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
        response = self.send_request(request)
        QMessageBox.information(self, "Register", response or "No response from server")

    def login(self):
        username, ok = QInputDialog.getText(self, "Login", "Enter your username:")
        if not ok or not username:
            return

        password, ok = QInputDialog.getText(self, "Login", "Enter your password:")
        if not ok or not password:
            return

        data = json.dumps({"username": username, "password": password})
        request = f"POST /login HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
        response = self.send_request(request)

        if response and "Login successful" in response:
            QMessageBox.information(self, "Login", "Login successful!")
            self.current_user = username
            self.switch_to_main_ui()
        else:
            QMessageBox.warning(self, "Login", "Login failed. Please try again.")

    def view_products(self):
        request = "GET /products HTTP/1.1\r\n\r\n"
        response = self.send_request(request)

        if response:
            try:
                json_start = response.find("\r\n\r\n") + 4
                json_body = response[json_start:]
                products = json.loads(json_body)

                # Convert product prices to the selected currency
                for product in products:
                    if self.currency != "USD":
                        usd_price = float(product["price"])
                        new_price = self.convert_currency(usd_price, "USD", self.currency)
                        product["price"] = str(new_price) if new_price else "N/A"

                # Show products in a dialog
                products_dialog = QDialog(self)
                products_dialog.setWindowTitle("All Products")
                products_dialog.setGeometry(150, 150, 600, 400)

                layout = QVBoxLayout(products_dialog)

                products_list = QTextEdit(products_dialog)
                products_list.setReadOnly(True)
                layout.addWidget(products_list)

                for product in products:
                    products_list.append(str(product))

                products_dialog.exec_()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to parse products: {e}")

    def view_products_by_owner(self):
        owner, ok = QInputDialog.getText(self, "View Products by Owner", "Enter owner username:")
        if not ok or not owner:
            return
        request = f"GET /products?owner={owner} HTTP/1.1\r\n\r\n"
        response = self.send_request(request)
        QMessageBox.information(self, "Products by Owner", response or "No response from server")

    def convert_currency(self, amount, old_currency, new_currency):
        try:
            response = requests.get(EXCHANGERATEURL.format(APIKEY, old_currency))
            if response.status_code == 200:
                conversion_rates = response.json().get("conversion_rates", {})
                if new_currency in conversion_rates:
                    return round(amount * conversion_rates[new_currency], 2)
            else:
                print("Failed to fetch exchange rates.")
        except Exception as e:
            print(f"Error in currency conversion: {e}")
        return None

    def change_currency(self):
        currency, ok = QInputDialog.getText(self, "Change Currency", "Enter preferred currency:")
        if not ok or not currency:
            return

        self.currency = currency
        QMessageBox.information(self, "Currency Changed", f"Currency set to {currency}")
        
    def add_product(self):
        name, ok = QInputDialog.getText(self, "Add Product", "Enter product name:")
        if not ok or not name:
            return

        price, ok = QInputDialog.getText(self, "Add Product", "Enter product price in USD:")
        if not ok or not price:
            return

        description, ok = QInputDialog.getText(self, "Add Product", "Enter product description:")
        if not ok or not description:
            return

        picture, ok = QInputDialog.getText(self, "Add Product", "Enter product picture URL:")
        if not ok or not picture:
            return

        eta, ok = QInputDialog.getText(self, "Add Product", "Enter ETA in days:")
        if not ok or not eta:
            return

        quantity, ok = QInputDialog.getText(self, "Add Product", "Enter quantity of product:")
        if not ok or not quantity:
            return

        data = json.dumps({
            "name": name,
            "price": price,
            "description": description,
            "picture": picture,
            "ETA": eta,
            "quantity": quantity,
            "owner": self.current_user
        })
        request = f"POST /add_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
        response = self.send_request(request)
        QMessageBox.information(self, "Add Product", response or "No response from server")

    def modify_product(self):
        # Step 1: Get all products owned by the user
        request = f"GET /products?owner={self.current_user} HTTP/1.1\r\n\r\n"
        response = self.send_request(request)

        if not response:
            QMessageBox.warning(self, "Modify Product", "No response from server.")
            return

        try:
            json_start = response.find("\r\n\r\n") + 4
            json_body = response[json_start:]
            products = json.loads(json_body)

            if not products:
                QMessageBox.warning(self, "Modify Product", "You have no products to modify.")
                return

            # Step 2: Show the products in a dialog and let the user select one to modify
            product_names = [product["name"] for product in products]
            product_name, ok = QInputDialog.getItem(self, "Select Product", "Choose a product to modify:", product_names, 0, False)

            if not ok or not product_name:
                return

            selected_product = next(product for product in products if product["name"] == product_name)
            product_id = selected_product["id"]

            # Step 3: Display options to modify the selected product
            self._modify_product_dialog(selected_product)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {e}")

    def _modify_product_dialog(self, product):
        # Step 4: Dialog to modify product details
        modify_dialog = QDialog(self)
        modify_dialog.setWindowTitle("Modify Product")
        modify_dialog.setGeometry(150, 150, 400, 300)
        
        layout = QVBoxLayout(modify_dialog)
        
        # Display current product details
        product_info = QTextEdit(modify_dialog)
        product_info.setText(f"Name: {product['name']}\nPrice: {product['price']}\nDescription: {product['description']}\nPicture: {product['picture']}\nETA: {product['ETA']}")
        product_info.setReadOnly(True)
        layout.addWidget(product_info)

        # Options to modify product
        modify_layout = QVBoxLayout()

        buttons = [
            ("Change Name", self._change_product_name),
            ("Change Price", self._change_product_price),
            ("Change Description", self._change_product_description),
            ("Change Picture URL", self._change_product_picture),
            ("Change ETA", self._change_product_eta),
            ("Delete Product", self._delete_product)
        ]
        
        for button_text, handler in buttons:
            button = QPushButton(button_text, modify_dialog)
            button.clicked.connect(lambda _, handler=handler: handler(product['id']))
            modify_layout.addWidget(button)
        
        layout.addLayout(modify_layout)

        modify_dialog.exec_()

    def _change_product_name(self, product_id):
        new_name, ok = QInputDialog.getText(self, "Change Name", "Enter new product name:")
        if ok and new_name:
            data = json.dumps({"new_name": new_name, "product_id": product_id, "owner": self.current_user})
            request = f"POST /modify_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
            response = self.send_request(request)
            QMessageBox.information(self, "Modify Product", response or "No response from server")

    def _change_product_price(self, product_id):
        new_price, ok = QInputDialog.getText(self, "Change Price", "Enter new product price in USD:")
        if ok and new_price:
            data = json.dumps({"new_price": new_price, "product_id": product_id, "owner": self.current_user})
            request = f"POST /modify_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
            response = self.send_request(request)
            QMessageBox.information(self, "Modify Product", response or "No response from server")

    def _change_product_description(self, product_id):
        new_desc, ok = QInputDialog.getText(self, "Change Description", "Enter new product description:")
        if ok and new_desc:
            data = json.dumps({"new_desc": new_desc, "product_id": product_id, "owner": self.current_user})
            request = f"POST /modify_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
            response = self.send_request(request)
            QMessageBox.information(self, "Modify Product", response or "No response from server")

    def _change_product_picture(self, product_id):
        new_pic, ok = QInputDialog.getText(self, "Change Picture URL", "Enter new product picture URL:")
        if ok and new_pic:
            data = json.dumps({"new_pic": new_pic, "product_id": product_id, "owner": self.current_user})
            request = f"POST /modify_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
            response = self.send_request(request)
            QMessageBox.information(self, "Modify Product", response or "No response from server")

    def _change_product_eta(self, product_id):
        new_eta, ok = QInputDialog.getText(self, "Change ETA", "Enter new ETA in days:")
        if ok and new_eta:
            data = json.dumps({"new_eta": new_eta, "product_id": product_id, "owner": self.current_user})
            request = f"POST /modify_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
            response = self.send_request(request)
            QMessageBox.information(self, "Modify Product", response or "No response from server")

    def _delete_product(self, product_id):
        confirm = QMessageBox.question(self, "Delete Product", "Are you sure you want to delete this product?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            data = json.dumps({"product_id": product_id, "owner": self.current_user})
            request = f"POST /delete_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
            response = self.send_request(request)
            QMessageBox.information(self, "Modify Product", response or "No response from server")

    def search_product(self):
        search_term, ok = QInputDialog.getText(self, "Search Product", "Enter product name to search:")
        if not ok or not search_term:
            return

        request = f"GET /search_products?product={search_term} HTTP/1.1\r\n\r\n"
        response = self.send_request(request)
        QMessageBox.information(self, "Search Product", response or "No response from server")

    def buy_product(self):
        product_id, ok = QInputDialog.getText(self, "Buy Product", "Enter product ID to buy:")
        if not ok or not product_id:
            return

        data = json.dumps({"id": product_id, "buyer": self.current_user})
        request = f"POST /buy_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
        response = self.send_request(request)
        QMessageBox.information(self, "Buy Product", response or "No response from server")

    def rate_product(self):
        product_id, ok = QInputDialog.getText(self, "Rate Product", "Enter product ID to rate:")
        if not ok or not product_id:
            return

        rating, ok = QInputDialog.getText(self, "Rate Product", "Enter rating (1-10):")
        if not ok or not rating:
            return

        data = json.dumps({"product_Id": product_id, "rating": rating})
        request = f"POST /rate_product HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
        response = self.send_request(request)
        QMessageBox.information(self, "Rate Product", response or "No response from server")

    def check_logs(self):
        username, ok = QInputDialog.getText(self, "Check Logs", "Enter username:")
        if not ok or not username:
            return

        request = f"GET /get_logs?user={username} HTTP/1.1\r\n\r\n"
        response = self.send_request(request)
        QMessageBox.information(self, "Check Logs", response or "No response from server")

    def send_message(self):
        recipient, ok = QInputDialog.getText(self, "Send Message", "Enter recipient username:")
        if not ok or not recipient:
            return

        message, ok = QInputDialog.getText(self, "Send Message", "Enter your message:")
        if not ok or not message:
            return

        data = json.dumps({"recipient": recipient, "message": message, "sender": self.current_user})
        request = f"POST /message HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
        response = self.send_request(request)
        QMessageBox.information(self, "Send Message", response or "No response from server")

    def check_online_status(self):
        username, ok = QInputDialog.getText(self, "Check Online Status", "Enter username:")
        if not ok or not username:
            return
        request = f"GET /check_online?username={username} HTTP/1.1\r\n\r\n"
        response = self.send_request(request)
        QMessageBox.information(self, "Online Status", response or "No response from server")

    def check_inbox(self):
        request = f"GET /check_inbox?username={self.current_user} HTTP/1.1\r\n\r\n"
        response = self.send_request(request)
        QMessageBox.information(self, "Inbox", response or "No response from server")

    def show_direct_chat_message(self):
        QMessageBox.information(self, "Direct Chat (P2P)", "This feature is not yet implemented.")

    def logout(self):
        if not self.current_user:
            return

        data = json.dumps({"username": self.current_user})
        request = f"POST /logout HTTP/1.1\r\nContent-Length: {len(data)}\r\n\r\n{data}"
        response = self.send_request(request)

        if response and "Logout successful" in response:
            QMessageBox.information(self, "Logout", "Logout successful!")
            self.current_user = None
            self.init_login_ui()
        else:
            QMessageBox.warning(self, "Logout", "Logout failed. Please try again.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = AUBoutiqueClientGUI()
    main_window.show()
    sys.exit(app.exec_())
