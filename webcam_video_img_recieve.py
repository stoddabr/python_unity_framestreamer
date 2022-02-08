import base64
import socket
import cv2
import numpy as np
import struct

# See
# * https://docs.python.org/3/howto/sockets.html
# * https://medium.com/nerd-for-tech/developing-a-live-video-streaming-application-using-socket-programming-with-python-6bc24e522f19 


TCP_IP = 'localhost'  # faster than dedicated ip address https://docs.python.org/3/howto/sockets.html#ipc
TCP_PORT = 5001

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
data = b""  # 'b' or 'B' indicates a bytestring instead of str
payload_size = struct.calcsize("Q")

while True:
    # recieve image length from the message(s)
    while len(data) < payload_size:
        packet = s.recv(4*1024)
        if not packet:
            break
        data += packet

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack('Q', packed_msg_size)[0]

    # recieve image data from second half of message(s)
    while len(data) < msg_size:
        data += s.recv(4*1024)
    
    frame_data = data[:msg_size]
    data = data[msg_size:]

    frame_binary = base64.b64decode(frame_data) 
    print('frame_data', frame_data[:20])
    print('data', data[:20])
    print('binary', frame_binary[:20])
    frame_np = np.frombuffer(frame_binary, dtype=np.uint8)  # todo deserialize
    frame = cv2.imdecode(frame_np, flags=1)
    if len(frame):
        cv2.imshow('Recieving...', frame)
        key = cv2.waitKey(10)
        if key == 13:
            break
    else:
        print('no img!!!!!!')

s.close()
