import tkinter as tk
from tkinter import ttk
import serial
import threading
import ujson
import json
import time
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import ssl

# Global Variables
out_speed = 0
out_duty = 0
out_rpm = 0
out_height = 0
out_force = 0
sensor_data = {"Force": 0, "Duty": 0, "Speed": 0, "Rpm": 0, "Height": 0} # Set dict for data update

port = 1883
Server_ip = "broker.netpie.io" 

Subscribe_Topic = "@msg/LED"
Publish_Topic = "@shadow/data/update"

# Get your own ID, Token and Secret from NETPIE
Client_ID = "Your ID"
Token = "Your Token"
Secret = "Your Secret"

MqttUser_Pass = {"username":Token,"password":Secret}

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(Subscribe_Topic)

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global LED_Status
    print(msg.topic+" "+str(msg.payload))
    data_receive = msg.payload.decode("UTF-8")
    LED_Status = data_receive

client = mqtt.Client(protocol=mqtt.MQTTv311,client_id=Client_ID, clean_session=True)
client.on_connect = on_connect
client.on_message = on_message

client.subscribe(Subscribe_Topic)
client.username_pw_set(Token,Secret)
client.connect(Server_ip, port)

# Initialize serial connection
ser = serial.Serial('COMx', ????)  # Replace 'COMx' with the correct port
ser.timeout = 1  # Optional timeout for reading

# Global variable to store the last update time for dictionary values
last_dict_update_time = 0

# Function to handle sending "0" to Pico
def send_stop_command():
    ser.write(b'0\n')  # Send 0 to stop Pico
    log_text("Select Mode of Control")

# Function to handle sending integer input to Pico
def send_integer_input():
    user_input = input_entry.get()
    if user_input.isdigit():
        ser.write((user_input + '\n').encode('utf-8'))  # Send input to Pico
        log_text(f"Sent: {user_input}")
        input_entry.delete(0, tk.END)  # Clear input field
    else:
        log_text("Error: Input must be an integer.")

# Function to log text to the GUI's output display
def log_text(message):
    output_display.config(state=tk.NORMAL)  # Enable editing
    output_display.insert(tk.END, message + "\n")
    output_display.config(state=tk.DISABLED)  # Disable editing
    output_display.see(tk.END)  # Scroll to the bottom

# Thread to handle receiving data from Pico
def receive_data():
    global last_dict_update_time, out_speed, out_duty, out_rpm, out_height, out_force
    while True:
        try:
            if ser.in_waiting > 0:
                raw_data = ser.readline().decode('utf-8').strip()  # Read incoming data
                try:
                    # Try to parse the data as JSON
                    parsed_data = ujson.loads(raw_data)
                    if isinstance(parsed_data, dict):
                        # Update dictionary values every 0.5 seconds
                        current_time = time.time()
                        if current_time - last_dict_update_time >= 0.5:
                            log_text("Received Data:")
                            for key, value in parsed_data.items():
                                log_text(f"  {key}: {value}")
                                if key == "speed":
                                    out_speed = value
                                elif key == "duty":
                                    out_duty = value
                                elif key == "rpm":
                                    out_rpm = value
                                elif key == "height":
                                    out_height = value
                                elif key == "force":
                                    out_force = value
                            last_dict_update_time = current_time
                            sensor_data["Force"] = out_force
                            sensor_data["Duty"] = out_duty
                            sensor_data["Speed"] = out_speed
                            sensor_data["Rpm"] = out_rpm
                            sensor_data["Height"] = out_height
                            data_out=json.dumps({"data": sensor_data}) # encode object to JSON
                            print(data_out)
                            client.publish(Publish_Topic, data_out, retain= True)
                            print ("Publish.....")
                    else:
                        log_text(f"Received unknown JSON format: {parsed_data}")
                except ValueError:
                    # If parsing fails, treat as a plain string
                    log_text(f"{raw_data}")
        except Exception as e:
            log_text(f"Error: {e}")
            break

# Set up the GUI
root = tk.Tk()
root.title("Pico Communication Interface")

# Set window size
root.geometry("800x600")

# Stop Button
stop_button = ttk.Button(root, text="Mode Select", command=send_stop_command)
stop_button.pack(pady=5)

# Input Section
input_frame = ttk.Frame(root)
input_frame.pack(pady=5)

input_label = ttk.Label(input_frame, text="Enter Integer:")
input_label.pack(side=tk.LEFT, padx=5)

input_entry = ttk.Entry(input_frame, width=10)
input_entry.pack(side=tk.LEFT, padx=5)

send_button = ttk.Button(input_frame, text="Send", command=send_integer_input)
send_button.pack(side=tk.LEFT, padx=5)

# Output Display
output_display = tk.Text(root, height=25, width=80, state=tk.DISABLED, wrap=tk.WORD)
output_display.pack(pady=10)

# Start the thread to receive data
receive_thread = threading.Thread(target=receive_data, daemon=True)
receive_thread.start()

# Run the GUI
root.mainloop()
client.loop_start()
