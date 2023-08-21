from PIL import Image
from cnstd import CnStd
import cv2
import pandas as pd
import serial.tools.list_ports
import serial
import binascii
import time

# !/usr/bin/env python
# coding=utf-8

# CMD RunAsAdmin , cd folder , py 1.py

import serial

ser = serial.Serial("COM3", 9600, timeout=1)
flag = ser. is_open
# while True:
#     print(ser.isOpen())
#     data = ser.readline()
#     print(data,'data')
#     if data:
#         rec_str = data.decode('utf-8')
#         print(rec_str)


while True:
    print(flag)
    # print(COMGUNNUM)
    data = ser.readline()
    serialdata = data.decode().strip()
    print(serialdata)
# ser.close()

# while True:
#     # print(COMSIGNALNUM)
#     data=ser.readline()
#     print(data)
#     serialdata= binascii.b2a_hex(data).decode().strip()
#     print(serialdata)
#     print(type(serialdata))
