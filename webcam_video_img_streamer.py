import base64
import socket
import cv2
import numpy
import struct
import time 
import threading
import os

# setup networking
TCP_IP = 'localhost'  # faster than dedicated ip address https://docs.python.org/3/howto/sockets.html#ipc
message = 'this should be overwritten by encoded image'
TCP_PORT = 5001
host_name = socket.gethostname()
host_ip = socket.gethostbyname(host_name)
print('HOST IP: ', host_ip)
print('HOST Port: ', TCP_PORT)
print('Address: ', host_ip+':'+str(TCP_PORT)+'/')

# manage threads
threads = []
RUN_BACKGROUND_THREADS = True  # kill flag
def initThread(t):
    t.daemon = True  # enable threads to be killed via ctrl+c
    t.start()
    threads.append(t)

def killAllThreads():
    # set flag for threads to die piecefully
    RUN_BACKGROUND_THREADS = False  # kill threads

    # raising exception isn't working (and is violent)
    # for t in threads:
    #     t.raise_exception()

# create socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(5)  # max 5 connections
    # TODO optimize muxing over multiple client sockets
s.settimeout(0.1)  # prevent code from hanging on `s.accept()`

def saveFrames(vid):
    global message
    global RUN_BACKGROUND_THREADS

    print('init cam')
    while RUN_BACKGROUND_THREADS:
        if vid.isOpened():
            # collect image data
            img, frame = vid.read()
            img, buffer = cv2.imencode('.jpeg', frame)
            base64str = base64.b64encode(buffer)

            # send message(s) to connection
            # prefix message with length of image encoded as an unsigned long long (8 bytes)
            message = struct.pack("Q", len(base64str)) + base64str 
            # print('msg', len(base64str), message[:100])
            cv2.imshow('Sending...', frame)
            key = cv2.waitKey(10)
            if key == 13:  # enter key
                break
        else:
            print('no cam')

# setup camera for test
vid = cv2.VideoCapture(0)

# create video thread
tv = threading.Thread(target=saveFrames, args=(vid,))
initThread(tv)

def on_new_client(clientsocket,addr):
    global message
    global RUN_BACKGROUND_THREADS

    print('init client')
    while RUN_BACKGROUND_THREADS:
        time.sleep(0.05)  # avoid latency caused by tcp traffic

        if clientsocket and len(message) > 100:
            # print('sending', message)
            clientsocket.sendall(message)


def server_listen():
    # start listening
    # accept connections
    try:
        clientsocket, addr = s.accept()
    except Exception as e:
        # s.accept() timed out so try again
        # part of a hack to keep s.accept() from blocking thread
        if str(e) == 'timed out': 
            return  # try again 
    if clientsocket:
        tc = threading.Thread(target=on_new_client, args=(clientsocket, addr,))
        initThread(tc)

if __name__ == "__main__":
    try:
        while True:
            server_listen()
    except KeyboardInterrupt:
        print('exception triggered')
        killAllThreads()
    except Exception as e:
        print('error in main loop:', e)
    s.close()
    cv2.destroyAllWindows() 
    os._exit('error')
