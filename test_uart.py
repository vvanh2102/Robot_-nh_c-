import serial
import time

# Mở cổng serial
ser = serial.Serial(port='COM4', baudrate=9600, timeout = 1)  # Thay COM3 bằng cổng của bạn

while True:
    data = input("Nhập dữ liệu để gửi: ")  # Nhập dữ liệu từ bàn phím
    ser.write(data.encode())  # Gửi dữ liệu (chuyển thành bytes)
    time.sleep(0.5)
    received_data = ser.readline().decode().strip()  # Đọc dữ liệu
    print(f"Đã nhận: {received_data}")
