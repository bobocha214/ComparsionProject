import serial

ser1 = serial.Serial('com3', 9600, timeout=0.5)
if ser1.is_open:
    hexStr = "03 53 80 ff 2a"
    # hexStr = "16 54 0D"
    bytes_hex = bytes.fromhex(hexStr)
    ser1.write(bytes_hex)
else:
    ser1.open()