import time

import serial
ser1 = serial.Serial('com4', 9600, timeout=0.5)
if ser1.is_open:
    print(ser1.is_open)
    ser1.close()
    print(ser1.is_open)
    ser1.open()
    print(ser1.is_open)
    # hexStr = "03 53 80 ff 2a"
    # hexStr = "16 54 0D"
    # bytes_hex = bytes.fromhex(hexStr)
    # ser1.write(bytes_hex)
else:
    ser1.open()
# while True:
#     if ser1.is_open:
#         data = ser1.readline()
#         serialdata = data.decode().strip()
#         if (serialdata != ''):
#             serialdata = data.decode().strip()
#             # print(serialdata,'serialdata')
#             print(serialdata,'serialdata1')
#         else:
#             time.sleep(0.1)

