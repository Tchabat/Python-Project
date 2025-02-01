import socket
import threading

class GameServer:
    def __init__(self, host="0.0.0.0", port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.messages = []

    def broadcast(self, message, sender_socket=None):
        for client in self.clients:
            if client != sender_socket:
                try:
                    client.send(message.encode("utf-8"))
                except:
                    self.clients.remove(client)

    def handle_client(self, client_socket, address):
        print(f"[NEW CONNECTION] {address} connected.")
        self.clients.append(client_socket)

        while True:
            try:
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    break
                print(f"[{address}] {data}")
                self.messages.append(data)  # Add to the server's message queue
                self.broadcast(data, client_socket)
            except:
                break
        print(f"[DISCONNECTED] {address} disconnected.")
        self.clients.remove(client_socket)
        client_socket.close()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()
        print(f"[SERVER STARTED] Listening on {self.host}:{self.port}")

        while True:
            client_socket, address = server.accept()
            thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
            thread.start()

class GameClient:
    def __init__(self, server_ip, port=12345):
        self.server_ip = server_ip
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.messages = []

    def connect(self):
        try:
            self.client_socket.connect((self.server_ip, self.port))
            print("[CONNECTED] Connected to the server.")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except:
            print("[ERROR] Unable to connect to the server.")

    def receive_messages(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode("utf-8")
                if data:
                    self.messages.append(data)  # Add to the client's message queue
            except:
                print("[ERROR] Disconnected from the server.")
                self.client_socket.close()
                break

    def send_message(self, message):
        try:
            self.client_socket.send(message.encode("utf-8"))
        except:
            print("[ERROR] Unable to send the message.")
