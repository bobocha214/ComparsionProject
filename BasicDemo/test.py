from PIL import Image
from cnstd import CnStd
import cv2
import pandas as pd
import serial.tools.list_ports
import serial
import binascii
import time
#!/usr/bin/env python
#coding=utf-8

# CMD RunAsAdmin , cd folder , py 1.py
 
import clr
import time
clr.AddReference("C:\vscodeprojects\openhardwaremonitor-v0.9.6\OpenHardwareMonitor\OpenHardwareMonitorLib.dll") #加载C#的库这个库网上可以下载
 

from OpenHardwareMonitor.Hardware import Computer
 
computer_tmp = Computer() #实例这这个类
 
computer_tmp.CPUEnabled = True #获取CPU温度时用
computer_tmp.GPUEnabled = True #获取GPU温度时用
computer_tmp.HDDEnabled = True #获取HDD温度时用 
computer_tmp.RAMEnabled = True #获取RAM温度时用
 
computer_tmp.Open()
 
print (computer_tmp.Hardware[0].Identifier)  # 0 CPU 
print (computer_tmp.Hardware[1].Identifier)  # 1 Ram 
print (computer_tmp.Hardware[2].Identifier)  # 2 GPU
print (computer_tmp.Hardware[3].Identifier)  # 3 HDD

print (len(computer_tmp.Hardware[0].Sensors))  # 25
print (len(computer_tmp.Hardware[1].Sensors))  # 3
print (len(computer_tmp.Hardware[2].Sensors))  # 17
print (len(computer_tmp.Hardware[3].Sensors))  # 6

while True:
    for a in range(0, len(computer_tmp.Hardware[0].Sensors)):
        print (computer_tmp.Hardware[0].Sensors[a].Identifier ,computer_tmp.Hardware[0].Sensors[a].Value)      

    for b in range(0, len(computer_tmp.Hardware[1].Sensors)):
        print (computer_tmp.Hardware[1].Sensors[b].Identifier ,computer_tmp.Hardware[1].Sensors[b].Value)      

    for c in range(0, len(computer_tmp.Hardware[2].Sensors)):
        print (computer_tmp.Hardware[2].Sensors[c].Identifier ,computer_tmp.Hardware[2].Sensors[c].Value)      
      
    for d in range(0, len(computer_tmp.Hardware[3].Sensors)):
        print (computer_tmp.Hardware[3].Sensors[d].Identifier ,computer_tmp.Hardware[3].Sensors[d].Value)      

    computer_tmp.Hardware[0].Update()
    computer_tmp.Hardware[1].Update()
    computer_tmp.Hardware[2].Update()
    computer_tmp.Hardware[3].Update()
    
    
    time.sleep(10)
    print ()
    


# w = wmi.WMI(namespace="root\wmi")
# temperature_info = w.MSAcpi_ThermalZoneTemperature()[0]
# now_temp=temperature_info.CurrentTemperature/10-273.15
# print(now_temp)

# all_comports = serial.tools.list_ports.comports()

# for comport in all_comports:
#     print(comport.device, comport.name, comport.description, comport.interface)

# all_comports = serial.tools.list_ports.comports()
# available_ports = []

# for comport in all_comports:
#     available_ports.append(comport.device)

# print(available_ports)




# ser=serial.Serial('COM3', 9600)
# print(ser.portstr)
# command = "1564 0D"
# ser.write(command.encode('utf-8'))
# print(command.encode('utf-8'))

# ser.close()

# while True:
#     # print(COMSIGNALNUM)
#     data=ser.read(9)
#     # print(data)
#     serialdata= binascii.b2a_hex(data).decode().strip()
#     print(serialdata)
#     print(type(serialdata))
