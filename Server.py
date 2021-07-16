import random
import threading
import socket
import re
import time
import sys
from collections import defaultdict


class users:  # create a class record information about each user
    Userstate = 0
    countWrong = 0  # record the number of wrong password times of user
    Username = None
    UsertempID = None
    block_time = None
    start_time = None
    expiry_time = None

    def __init__(self, Uname, duration):
        self.Username = Uname
        self.block_time = duration

    def unblock(self):
        time.sleep(self.block_time)
        self.countWrong = 0

    def LogState(self):
        if self.Userstate == "block":
            return "blocking"
        if self.Userstate == "logout":
            return "logout"

    def unblocking(self):
        unblock = threading.Thread(target=self.unblock)
        unblock.start()


class Server:
    Server_socket = None
    Username = None
    Password = None
    LogState = 0
    user_credentials_dict = defaultdict(str)  # record every username and its password
    user_information_dict = defaultdict(str)  # save the user's information, and key is username
    key_tempIp_user = defaultdict(str)    # save the username, start time, expiry time, and key is tempID
    block_time = 0
    Server_port = 0

    def __init__(self, server_port, duration):
        self.block_time = duration
        self.Server_port = server_port
        self.Server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Server_socket.bind(("127.0.0.1", self.Server_port))
        with open("credentials.txt", "r") as f:
            for line in f.readlines():
                line = line.replace("\n", "").split(" ")
                self.user_credentials_dict[line[0]] = line[1]  # record every username and its password
                self.user_information_dict[line[0]] = users(line[0], duration)  # save the user's information, and key is username
        open("tempIDs.txt", "w")  # when run the Server.py successfully,
                                # then create a file named tempIDs.txt used to save tempID and its start time and expiry time

    def ckeckloging(self, Message):  # check if user can login with correct username and password
        Message = Message.split("-")
        username = Message[1]
        password = Message[2]
        if username in self.user_credentials_dict.keys():
            if password == self.user_credentials_dict[username]:
                if self.user_information_dict[username].Userstate == 1:  # check if user is log in state
                    new_message = "Havelogged"
                    return new_message
                if self.user_information_dict[username].countWrong >= 3:  # check if user is in blocking state
                    new_message = "blocking"
                    return new_message
                new_message = "LoginSuccess"
                self.user_information_dict[username].Userstate = 1
                self.user_information_dict[username].countWrong = 0
                return new_message
            else:
                self.user_information_dict[username].countWrong += 1  # if input wrong password, then add one
                if self.user_information_dict[username].countWrong == 3:  # third wrong input, will block
                    new_message = "blocked"
                    self.user_information_dict[username].Userstate = "block"
                    self.user_information_dict[username].unblocking()
                    return new_message
                elif self.user_information_dict[username].countWrong > 3:
                    new_message = "blocking"
                    return new_message
                elif self.user_information_dict[username].countWrong < 3:
                    new_message = "Wrongpassword"
                    return new_message
        else:
            new_message = "InvalidUsername"  # no such username in credential.txt
            return new_message

    def create_tempID(self):  # create a random 20-bytes tempID
        num_list = list(str(random.randint(0, 9)) for i in range(20))
        tempID_num = ''.join(num_list)
        return tempID_num

    def sendtempID(self, Message):
        Username = Message[6:]  # get the username
        tempID = self.create_tempID()  # create a 20 bytes tempID
        start_time_second = time.time()  # get the start time
        self.user_information_dict[Username].UsertempID = tempID  # record the username in user_information
        start_time = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(start_time_second))
        self.user_information_dict[Username].start_time = start_time
        expiry_time = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(start_time_second + 15 * 60 - 1))
        self.user_information_dict[Username].expiry_time = expiry_time
        feedback = self.user_information_dict[Username].UsertempID + "-" + start_time + "-" + expiry_time
        self.key_tempIp_user[tempID] = [Username, start_time, expiry_time]  # dictionary whose key is tempID,
        with open("tempIDs.txt", "a") as fp:  # and value is Username,start time and expiry time
            fp.write(Username + " " + tempID + " " + start_time + " " + expiry_time + "\n")
        return feedback

    def receivefromClient(self, Client):
        while True:
            try:
                receiveMessage = Client.recv(1024)
            except:
                print("Connection Error")
                Client.close()
                break
            Message = receiveMessage.decode()
            if Message[:2] == "in":  # response to login command from client
                Feedback = self.ckeckloging(Message)
                Client.sendall(Feedback.encode())
            elif Message[:3] == "out":  # respone to logout command from client
                Username = Message[3:]
                if self.user_information_dict[Username].Userstate == 1:
                    self.user_information_dict[Username].Userstate = 0
                    self.user_information_dict[Username].countWrong = 0
                    self.user_information_dict[Username].UsertempID = None
                    outMessage = "outsuccess"
                    Client.sendall(outMessage.encode())
                    print(Username, "logout")
            elif Message[:6] == "tempID":  # response to Download_tempID command from client
                print("user: " + Message[6:])
                Feedback = self.sendtempID(Message)
                Client.sendall(Feedback.encode())
                print("TempID:\n" + Feedback[:20])
            elif Message[:6] == "Upload":  # response to Upload_contactlog command from client
                Message = Message.split("-")
                length_of_message = len(Message)
                print("received contact log from " + Message[1])
                if length_of_message == 2:
                    print("No contact person")
                else:
                    for index in range(2, length_of_message):
                        print(Message[index] + ",")
                        print(self.key_tempIp_user[Message[index]][1] + ",")
                        print(self.key_tempIp_user[Message[index]][2] + ";")
                    print("Contact log checking")
                    for index in range(2, length_of_message):
                        print(self.key_tempIp_user[Message[index]][0] + ",")
                        print(self.key_tempIp_user[Message[index]][1] + ",")
                        print(self.key_tempIp_user[Message[index]][2] + ";")

    def start(self):
        self.Server_socket.listen(10)  # server is in listen state
        while True:
            client, address = self.Server_socket.accept()
            Serverthread = threading.Thread(target=self.receivefromClient, args=[client])
            Serverthread.setDaemon(True)
            Serverthread.start()


if __name__ == "__main__":
    server_port = int(sys.argv[1])
    duration = int(sys.argv[2])
    server_start = Server(server_port, duration)
    server_start.start()
