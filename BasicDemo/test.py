from PIL import Image
from cnstd import CnStd
import cv2
import pandas as pd
import serial.tools.list_ports
import serial
import binascii
import time
from cnocr import CnOcr
# !/usr/bin/env python
# coding=utf-8

# CMD RunAsAdmin , cd folder , py 1.py

import serial

# ser = serial.Serial("COM3", 9600, timeout=1)
# flag = ser. is_open
# while True:
#     print(ser.isOpen())
#     data = ser.readline()
#     print(data,'data')
#     if data:
#         rec_str = data.decode('utf-8')
#         print(rec_str)
# while True:
#     print(flag)
#     # print(COMGUNNUM)
#     data = ser.readline()
#     serialdata = data.decode().strip()
#     print(serialdata)
ocr = CnOcr()  # 所有参数都使用默认值
res = ocr.ocr('C:/pycharm/pythonProject/ComparsionProject/BasicDemo/img/2023.8.21/trainAPPOES56K3-5.jpg')
print(res)
sub = 'SN:'
nub = 'PN:'
serachnum = 'N:'
SnCode = ''
position = ''
if (res):
    max_length_dict = None
    for i in res:
        if sub in i['text'] or nub in i['text'] and len(i['text']) >= 17:
            if sub in i['text'] and len(i['text']) <= 20:
                firstSnCode = i['text']
                tempcode = ''.join(str(firstSnCode).split())
                SnCode = tempcode[3:].replace(" ", "")
                position = i['position']
                print(SnCode,'subsubsubsubsub')
                print(len(SnCode))
            else:
                try:
                    second_coourenceN = i['text'].index(serachnum, i['text'].index(serachnum) + 1)
                    SnCode = str(i['text'][second_coourenceN + len(serachnum):]).replace(" ", "")
                    position = i['position']
                    print(SnCode,'trytrytrytrytry')
                except:
                    firstSnCode = i['text']
                    tempcode = ''.join(str(firstSnCode).split())
                    SnCode = tempcode[3:].replace(" ", "")
                    position = i['position']
                    print(SnCode,'exceptexceptexceptexcept')
        else:
            pass
# ser.close()

# while True:
#     # print(COMSIGNALNUM)
#     data=ser.readline()
#     print(data)
#     serialdata= binascii.b2a_hex(data).decode().strip()
#     print(serialdata)
#     print(type(serialdata))
