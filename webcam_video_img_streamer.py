import base64
import socket
import cv2
import numpy
import struct
import time 


TCP_IP = 'localhost'  # faster than dedicated ip address https://docs.python.org/3/howto/sockets.html#ipc
TCP_PORT = 5001
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP: ', host_ip)
print('HOST Port: ', TCP_PORT)
print('Address: ', host_ip+':'+str(TCP_PORT)+'/')

# create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(5)  # max 5 connections
    # TODO optimize muxing over multiple client sockets

# setup camera for test
vid = cv2.VideoCapture(0)

# start listening
while True:
    # accept connections
    clientsocket, addr = s.accept()
    print('connection from ', addr)
    if clientsocket:
        while(vid.isOpened()):
            time.sleep(0.03)  # avoid latency buildup over time

            # collect image data
            img, frame = vid.read()
            img, buffer = cv2.imencode('.jpeg', frame)
            base64str = base64.b64encode(buffer)

            # send message(s) to connection
            # prefix message with length of image encoded as an unsigned long long (8 bytes)
            message = struct.pack("Q", len(base64str)) + base64str 
            # print('msg', len(base64str), message[:100])
            clientsocket.sendall(message)
            cv2.imshow('Sending...', frame)
            key = cv2.waitKey(10)
            if key == 13:  # enter key
                break

s.close()
cv2.destroyAllWindows() 