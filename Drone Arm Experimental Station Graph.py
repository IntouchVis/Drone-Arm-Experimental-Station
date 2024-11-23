import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import serial
import threading
import json  # To parse dictionary data from Pico
import time

# Global Variables
out_speed = 0
out_duty = 0
out_rpm = 0
out_height = 0
out_force = 0
last_dict_update_time = time.time()

# Serial Port Configuration
ser = serial.Serial('COM3', 115200)  # Replace 'COMx' with the correct port
ser.timeout = 1  # Optional timeout for reading

# Matplotlib Setup
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(8, 8), sharex=True)

x_data = []  # To store time values (x-axis)
y_rpm = []  # To store RPM values (y-axis)
y_height = []  # To store height values (y-axis)
y_force = []  # To store force values (y-axis)

line_rpm, = ax1.plot([], [], 'r-', label='RPM')
ax1.set_xlim(0, 10)  # x-axis range
ax1.set_ylim(0, 1700)  # y-axis range for RPM
ax1.set_title("Real-Time RPM Plot")
ax1.set_ylabel("RPM")
ax1.grid(True)

line_height, = ax2.plot([], [], 'b-', label='Height')
ax2.set_xlim(0, 10)  # x-axis range 
ax2.set_ylim(0, 350)  # y-axis range for height
ax2.set_title("Real-Time Height Plot")
ax2.set_ylabel("Height (mm)")
ax2.grid(True)

line_force, = ax3.plot([], [], 'g-', label='Force')
ax3.set_xlim(0, 10)  # x-axis range
ax3.set_ylim(0, 1000)  # y-axis range for force
ax3.set_title("Real-Time Force Plot")
ax3.set_xlabel("Time (seconds)")
ax3.set_ylabel("Force (grams)")
ax3.grid(True)

# Matplotlib Initialization 
def init():
    line_rpm.set_data([], [])
    line_height.set_data([], [])
    line_force.set_data([], [])
    return line_rpm, line_height, line_force

# Update Function for Animation
def update(frame):
    x_data.append(frame)
    y_rpm.append(out_rpm)
    y_height.append(out_height)
    y_force.append(out_force)

    line_rpm.set_data(x_data, y_rpm)
    line_height.set_data(x_data, y_height)
    line_force.set_data(x_data, y_force)

    # Adjust the x-axis range dynamically
    if frame > 10:
        ax1.set_xlim(frame - 10, frame)
        ax2.set_xlim(frame - 10, frame)
        ax3.set_xlim(frame - 10, frame)

    return line_rpm, line_height, line_force

# Serial Data Reception
def receive_data():
    global out_speed, out_duty, out_rpm, out_height, out_force, last_dict_update_time
    while True:
        try:
            # Check if data is waiting to be read from the serial port
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').strip()  # Read incoming data
                try:
                    # Parse the data as JSON
                    parsed_data = json.loads(raw_data)
                    if isinstance(parsed_data, dict):
                        print("Received Data:", parsed_data)
                        out_speed = parsed_data.get("speed", out_speed)
                        out_duty = parsed_data.get("duty", out_duty)
                        out_rpm = parsed_data.get("rpm", out_rpm)
                        out_height = parsed_data.get("height", out_height)
                        out_force = parsed_data.get("force", out_force)
                except json.JSONDecodeError:
                    print(f"Error parsing JSON: {raw_data}")
        except Exception as e:
            print(f"Error: {e}")
            break

# --- Start Serial Thread ---
serial_thread = threading.Thread(target=receive_data, daemon=True)
serial_thread.start()

# --- Start Animation ---
ani = FuncAnimation(fig, update, frames=np.linspace(0, 50, 500), init_func=init, blit=True, interval=100)
plt.tight_layout()  # Adjust the layout to avoid overlap
plt.show()
