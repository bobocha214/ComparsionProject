import time

import serial
ser1 = serial.Serial('COM3', 9600, timeout=0.5)
#命令触发扫码枪
while True:
    try:
        # print(COMGUNNUM)
        if ser1.is_open:
            data = ser1.readline()
            serialdata = data.decode().strip()
            if (serialdata != ''):
                serialdata = data.decode().strip()
                print(serialdata)
            else:
                time.sleep(0.1)
        else:
            ser1.open()
    except:
        pass
    # try:
    #     hexStr = "03 53 80 ff 2a"
    #     # convert hex to bytes
    #     bytes_hex = bytes.fromhex(hexStr)
    #     # device.write(bytes_hex)
    #     # # Alternative method
    #     # device.write(bytearray(bytes_hex))
    #     ser1.write(bytes_hex)
    #     data = ser1.readline()
    #     serialdata = data.decode().strip()
    #     print(serialdata)
    # except:
    #     time.sleep(1)
    # finally:
    #     # Close the serial port
    #     ser1.close()