# /////////////////////////////////////////////////////////////////// 
# // Student name: Micah McCloy
# // Course: COSC 4653 - Advanced Networks
# // Assignment: Programming Assignment #2 - Interoperable Code
# // File name: mccloy_program2_server.py
# // Program's Purpose: This server uses select to handle multiple clients, accepting scores, max scores
# //                    and calculating various statistics to send back to the client.
# // 
# // Program's Limitations: N/A
# // Development Computer: Lenovo Flex 5
# // Operating System: Windows 10
# // Integrated Development Environment (IDE): Visual Studio Code 
# // Compiler: Python 3.9
# // Program's Operational Status: Functional
# ///////////////////////////////////////////////////////////////////

# IMPORTS
from argparse import _StoreTrueAction
import select
import socket
import datetime

# Necessary Port defs
PORT = 9000

# Class for the handling of sockets by storing and calclating information
class Client:
    def __init__(self, ip, port, sock):
        # Init
        self.ip = ip
        self.port = port
        self.sock = sock
        self.id = (self.ip, self.port)
        self.name = None
    
    def send_data(self, data, error_msg=False):
        if self.name or error_msg:
            self.sock.send(data.encode())

    def set_name(self, n):
        self.name = n


# Create a server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(("", PORT))
server_socket.listen()

# Set up the list of sockets to monitor
sockets_to_monitor = [server_socket]

# Data structures to store details (id, client)
clients = {}
# Data structure stores {"name", ID}
names =  {}

# HELPER GETTER FUNCTIONS

def get_client_by_id(id):
    return clients[id]

def get_client_by_name(name):
    return get_client_by_id(names[name])

# This function handles each socket upon recieving data
def manage_response(s):
    global names
    global clients

    ID = s.getpeername()

    ## ERROR CHECKING
    if ID not in clients:
        print ("Client missed...")
    
    print("wating on client...")
    c = clients[ID]
    try:
        msg = c.sock.recv(1024).decode()
    except ConnectionResetError:
        store = f"{c.ip}:{c.port} -- {c.name} disconnected"
        log(store)
        c.sock.shutdown(socket.SHUT_RD)
        c.sock.close()
        return 1
        
    msg = msg.split("|")
    msg = msg[:-1]
    args = len(msg)

    if args == 0:  # If client sends empty packet, ignore it
        return 0

    ## The following code block ensures that the client is registered with a valid name
    if c.name == None:
        register_user(c, msg)
        return 0

    if args > 3:
        store = f"{c.ip}:{c.port} -- {c.name} had too many arguments"
        log(store)

        c.send_data("ERROR|unkown command|", True)
        return 0

    command = msg[0].upper()

    # The command list
    if command == "SAY" and args == 2:
        store = f"{c.ip}:{c.port} -- {c.name} said {msg[1][:200]}"
        log(store)
        send_all(c.name, f"PUBLIC|{c.name}|{msg[1][:200]}|")

    elif command == "PRIVATE" and args == 3:
        target = msg[1]
        if target not in names.keys():
            store = f"{c.ip}:{c.port} -- {c.name} tried sending a private message to non-existant user {target}. Msg: {msg[2][:200]}"
            log(store)
            c.send_data("PRIVERR|Invalid Recipient|", True)
        else:
            # Get the client with the specified name and send the message
            store = f"{c.ip}:{c.port} -- {c.name} sent a private message to {target}. Msg: {msg[2][:200]}"
            log(store)
            
            target_client = get_client_by_name(target)
            target_client.send_data(f"PRIVATE|{c.name}|{msg[2][:200]}|")
    elif command == "EXIT":
        store = f"{c.ip}:{c.port} -- {c.name} leaving the server"
        log(store)

        send_all(c.name, f"LEFT|{c.name}")
        return 1
    elif command == "LIST":
        store = f"{c.ip}:{c.port} -- {c.name} requested a list of all users"
        log(store)
        c.send_data(f"LIST|{len(names.keys())}|{'|'.join(names.keys())}|")
    elif command == "TIME":
        store = f"{c.ip}:{c.port} -- {c.name} requested the time"
        log(store)
        t = datetime.datetime.now().time()
        c.send_data(f"TIME|{t.hour}:{t.minute}:{t.second}|")
    else:
        store = f"{c.ip}:{c.port} -- {c.name} gave an unkown command: {msg}"
        log(store)
        c.send_data("ERROR|unknown command|", True)

    return 0



## This function handles registering a user (someone without a name)
def register_user(c, msg):
    global names
    global clients

    ## Check to ensure the client is connecting
    if msg[0].upper() != "CONNECT" or len(msg) != 2:

        store = f"{c.ip}:{c.port} -- <not connected> attempted an incorrect command: {msg}"
        log(store)
        
        c.send_data("ERROR|unknown command|", True)
        return
    ## Check valid uname
    elif len(msg[1]) > 50:

        store = f"{c.ip}:{c.port} -- tried connecting with a name over 50 bytes"
        log(store)

        c.send_data(f"REJECTED|{msg[1]}|Name Too Long|", True)

    ## Check unique uname
    elif msg[1] in names.keys():

        store = f"{c.ip}:{c.port} -- tried connecting with a taken name"
        log(store)

        c.send_data(f"REJECTED|{msg[1]}|Name is Taken|", True)
    ## Valid Uname
    else:

        store = f"{c.ip}:{c.port} sucessfully connected as {msg[1]}"
        log(store)

        names[msg[1]]  = c.sock.getpeername()
        c.set_name(msg[1])
        c.send_data(f"CONNECTED|{msg[1]}|")
        # send_all(msg[1], f"JOINED|{msg[1]}|")
        send_all(c.name, f"JOINED|{msg[1]}|")

## Sends a packet to all connected clients except any whose name is the argument
## This method uses the client function send_data, so the msg argument should not be encoded
def send_all(name, msg):
    global clients
    
    client_vals = clients.values()
    for c in client_vals:
        if name != c.name:
            c.send_data(msg)

## Whatever is passed as a parameter is logged within the server logs
def log(msg):
    t = datetime.datetime.now().time()
    msg = f"{t.hour}:{t.minute}:{t.second} | " + msg
    print(msg)
    log_file_name = "mm_log_file.txt"
    with open(log_file_name, "a") as f:
        f.write(msg + "\n")

while True:
    # Call select to monitor the sockets for activity
    read_sockets, _, _ = select.select(sockets_to_monitor, [], [])

    for s in read_sockets:

        # If the server socket is ready, accept the new client connection
        if s == server_socket:
            client_socket, client_address = s.accept()

            clients[client_address] = Client(client_address[0], client_address[1], client_socket)
            client_socket.send("COURSEID".encode())
            sockets_to_monitor.append(client_socket)
            store = f"Client connected: {client_address[0]}:{client_address[1]}"
            log(store)


        # If a client socket is ready, receive data from the client
        else:
            action = manage_response(s)

            if action != 0: # The socket must be closed since the client disconnected
                msg = f"Closing connection with {s.getpeername()[0]}:{s.getpeername()[1]}\n"
                log(store)
                sockets_to_monitor.remove(s)
                clients.pop(s.getpeername(), None)
                names.pop(get_client_by_id(s.getpeername()).name, None)
                s.close()
