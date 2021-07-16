import threading
from socket import *
import re
import time
import sys


class Client:
    Server_socket = None
    Server_socket_connect_state = 0  # check the socket connection state with Server
    Client_socket = None
    Client_socket_connect_state = 0  # check if client socket still open
    Log_state = 0  # Log_state=0 means not logged. Conversely, Log_state=1 means have already logged
    local_host = "127.0.0.1"
    username = None
    start_time = None
    expiry_time = None
    tempID = None

    def __init__(self, Server_address, Server_port, client_port):
        try:
            self.Server_socket = socket()
            self.Server_socket.connect((Server_address, Server_port))  # try to connect server socket
            self.Server_socket_connect_state = 1
        except:
            print("Wrong connection with Server")
            exit()
        try:
            self.Client_socket = socket(AF_INET, SOCK_DGRAM)
            self.Client_socket.bind((self.local_host, client_port))  # start UDP socket port
            self.Client_socket_connect_state = 1
        except:
            print("Wrong connection with Client")
            exit()

    def delete_contactlog(self, message):
        time.sleep(60)
        lines = []
        with open("z5290495_contactlog.txt", "r") as fp:
            for line in fp.readlines():
                if line != message:
                    lines.append(line)
        with open("z5290495_contactlog.txt", "w") as fp:
            for line in lines:
                fp.write(line)

    def thread_delete(self, message):
        thread_delete = threading.Thread(target=self.delete_contactlog, args=(message,))
        thread_delete.start()

    def receiveFromClient(self):
        while True:
            recvMessage, fromaddress = self.Client_socket.recvfrom(1024)
            current_time = time.time()
            recvMessage = recvMessage.decode()
            recvMessage = recvMessage.split("-")
            recvtempID = recvMessage[0]
            recv_starttime = recvMessage[1]
            recv_expirytime = recvMessage[2]
            Current_time = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(current_time))
            print("received beacon:")
            print(recvtempID + ",\n" + recv_starttime + ",\n" + recv_expirytime + ".")
            print("Current time is:")
            print(Current_time)
            recvstart_second = time.mktime(time.strptime(recv_starttime, "%d/%m/%Y %H:%M:%S"))
            recvexpiry_second = time.mktime(time.strptime(recv_expirytime, "%d/%m/%Y %H:%M:%S"))
            if recvstart_second <= current_time <= recvexpiry_second:
                contact_message = recvtempID + " " + recv_starttime + " " + recv_expirytime + "\n"
                with open("z5290495_contactlog.txt", "a") as fp:
                    fp.write(contact_message)
                self.thread_delete(str(contact_message))
                print("The beacon is valid.")
            else:
                print("The beacon is invalid.")

    def start(self):
        client_recv_thread = threading.Thread(target=self.receiveFromClient)
        client_recv_thread.setDaemon(True)
        client_recv_thread.start()
        while True:
            while self.Log_state == 0 and self.Server_socket_connect_state==1:  # detect login state
                Username = input("Username: ")
                Password = input("Password: ")
                self.Server_socket.send(("in" + "-" + Username + "-" + Password).encode())  # send command symbol, username and password to server
                recvMessage = self.Server_socket.recv(1024).decode()  # get response from server
                if recvMessage == "LoginSuccess":
                    self.Log_state = 1  # change the login state if log in successfully
                    self.username = Username  # save the username which has already logged in
                    print("Welcome to the BlueTraces Simulator!")
                    contact_log_name = "z5290495_contactlog.txt"
                    open(contact_log_name, "w")  # if you log in, then  will create a txt file named zID_contactlog.txt
                elif recvMessage == "Havelogged":
                    print("This user has already logged in.")
                elif recvMessage == "Wrongpassword":
                    print("Invalid Password. Please try again.")
                elif recvMessage == "blocked":
                    print("Invalid Password. Your account has been blocked. Please try again later")
                elif recvMessage == "blocking":
                    print("Your account is blocked due to multiple login failures. Please try again later")
                else:
                    print("Invalid username.")
            Command = input()
            if Command == "Download_tempID" and self.Server_socket_connect_state == 1:
                message = "tempID" + self.username
                self.Server_socket.send(message.encode())  # send tempID and username to server
                recvMessage = self.Server_socket.recv(1024).decode()  # get the recv message
                recvMessage = recvMessage.split("-")  # split the recvmessage
                self.tempID = recvMessage[0]
                self.start_time = recvMessage[1]
                self.expiry_time = recvMessage[2]
                print("TempID:\n" + self.tempID)
            elif Command == "logout" and self.Server_socket_connect_state == 1:
                if self.Log_state == 0:
                    print("Your have not logged in.")
                message = "out" + self.username
                self.Server_socket.send(message.encode())
                recvMessage = self.Server_socket.recv(1024).decode()
                if recvMessage == "outsuccess":
                    self.Log_state = 0
                    self.tempID = None
                    self.start_time = None
                    self.expiry_time = None
                    self.Server_socket.close()
                    self.Server_socket_connect_state = 0
            elif Command[:6] == "Beacon":
                if self.tempID==None:
                    print("Must download tempID first.")
                else:
                    send_message = self.tempID + "-" + self.start_time + "-" + self.expiry_time
                    newCommand = Command.split(" ")
                    address = (newCommand[1], int(newCommand[2]))
                    try:
                        self.Client_socket.sendto(send_message.encode(), address)
                        print(self.tempID + ",\n" + self.start_time + ",\n" + self.expiry_time + ".")
                    except ConnectionResetError:
                        print("Wrong socket connection with other clients.")
            elif Command == "Upload_contact_log" and self.Server_socket_connect_state == 1:
                send_message = "Upload" + "-" + self.username
                with open("z5290495_contactlog.txt", "r") as fp:
                    for line in fp.readlines():
                        print(line[:20] + ",\n" + line[21:40] + ",\n" + line[41:60] + ";")
                        send_message = send_message + "-" + line.split(" ")[0]

                self.Server_socket.send(send_message.encode())
            else:
                print("Error. Invalid command")


if __name__ == "__main__":
    ServerAddress = sys.argv[1]
    ServerPort = int(sys.argv[2])
    ClientPort = int(sys.argv[3])
    client_i = Client(ServerAddress, ServerPort, ClientPort)
    client_i.start()
