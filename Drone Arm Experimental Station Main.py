from picozero import LED, Button
from machine import Pin, I2C, PWM, ADC
import time
import vl53l0x
import ujson 
import sys
import select
import math

# Initialize I2C for VL53L0X
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000) # sda to GPIO 0 and scl to GPIO 1
sensor = vl53l0x.VL53L0X(i2c)

# Initialise Button & LED
button = Button(2) # Button to GPIO 2
led = LED(5) # LED to GPIO 5

# Initialise Motor
motor_pin = Pin(4) # Motor to GPIO 4
pwm = PWM(motor_pin) # Send pwm signals through GPIO 4
pwm.freq(50) # ESC expect a frequency of 50Hz

# Initialise Potentiometer
potentiometer = ADC(Pin(26)) # Potentiometer to GPIO 16

# Global Variables
speed = 0 # Current motor speed in %
out_speed = 0
out_duty = 0
out_rpm = 0
out_height = 0
out_force = 0
target_height = 90 # Taget Height
type = "Manual" # Type of control
poten_value = 0

# Function to set motor speed in % 
def set_speed(per):
    global out_speed, out_duty
    length = (per) + 1000 # ESC communicates with a pulse range between 1000 and 2000 microseconds
    duty = int((length/20000)*65535) # Turn percentage into 16-bit duty cycle
    pwm.duty_u16(duty) # Set motor duty to calculated cuty
    out_speed = per/10
    out_duty = duty

# Function to get current height from the VL53L0X sensor
def get_current_height():
    global out_height
    try:
        sensor.start()
        current_height_mm = sensor.read() # Get distance in mm
        sensor.stop()
        correct_height = current_height_mm + 10 # Apply +10 mm error correction from sensor 
        #print("Height:",correct_height,"mm")
        out_height = correct_height
        return correct_height
    except Exception as e:
        print(f"Error reading from VL53L0X: {e}")
        return None

# Function to get current force
def get_force():
    global speed, out_force
    if speed >= 230 and speed <= 730:
        set = (speed - 230)
        force = set * 1.4 # More information on Equation seen report
        out_force = force
        return out_force
    elif speed < 230:
        out_force = 0
        return 0
    else:
        out_force = 700
        return 700

# Function to get current rpm
def get_rpm():
    global out_force, out_rpm
    set = out_force / 0.0002436 # More information on Equation seen report
    rpm = int(math.sqrt(set))
    out_rpm = rpm
    return rpm

# Function to get potentiometer value
def get_poten_value():
    global poten_value
    read = potentiometer.read_u16() # Read the value from the potentiometer
    value = (potentiometer.read_u16()/65535)*1000 # Convert the value into %
    poten_value = value
    return value
    
# Function to control motor speed using potentiometer value
def Manual_Control():
    global speed
    get_poten_value() # Update potentiometer value
    speed = poten_value 
    set_speed(speed) # Set speed to that value
    get_rpm()
    get_current_height()
    time.sleep(0.1)

# Function to change motor speed depending on current motor position 
def Auto_Control():
    global speed,target_height
    current_height = get_current_height()
    if current_height is None:
        print("Failed to get current height.")
        return

    error = target_height - current_height # Calculate the error (difference between target and current height)

    # Update motor speed based on error
    if error >= 10:  # Move faster when too low
        speed += 0.2
        set_speed(speed)
    elif error <= -10:  # Move slower when too high
        speed -= 0.2
        set_speed(speed)
    else:
        set_speed(speed)
    
    get_rpm()
    get_current_height()
    time.sleep(0.1)

# Set motor to specific height
def Level_Control(num):
    global speed
    while speed >= 500: # Set the motor to the lowest position first
        speed -= 2
        set_speed(speed)
        get_rpm()
        get_current_height()
        return_value()
        led.toggle()
        time.sleep(0.1)
    if num == 1: # Position 1
        speed = 500 # Speed to maintain height
    if num == 2: # Position 2
        target = 150
        stable = False
        while stable == False:
            height = get_current_height()
            dif = target - height
            led.toggle()
            time.sleep(0.1)
            if (dif) > 10:
                speed = 680 # Move to target height
                set_speed(speed)
                get_rpm()
                get_current_height()
                return_value()
            else:
                stable = True
        speed = 640 # Speed to maintain height
        set_speed(speed)
    if num == 3: # Position 3
        target = 235
        stable = False
        while stable == False:
            height = get_current_height()
            dif = target - height
            led.toggle()
            time.sleep(0.1)
            if (dif) > 20:
                speed = 710 # Move to target height
                set_speed(speed)
                get_rpm()
                get_current_height()
                return_value()
            else:
                stable = True
        speed = 680 # Speed to maintain height
    if num == 4: # Position 4 
        speed = 770 # Speed to maintain height
    set_speed(speed)
    get_rpm()
    get_current_height()

def return_value():
    global out_speed, out_duty, out_rpm, out_force, out_height # Output variables
    get_current_height() # Update value
    get_force() # Update value
    get_rpm() # Update value
    values = dict(speed = out_speed, duty = out_duty, rpm = out_rpm, force = out_force, height = out_height) # Put values in ditionary
    json_data = ujson.dumps(values)
    sys.stdout.write(json_data + '\n') # Send data out

# Starting Point
get_current_height()
led.off()
set_speed(0)
return_value()
time.sleep(6) # Giving time for the motor to startup

sending = False # Prevent control overlap
local = False # Prevent control overlap

while True:
    # Have LED blink to indicate motor spinning
    if speed >= 240:
        led.toggle()
    else:
        led.on()
    # Hold button down to change type of control 
    if button.is_pressed:
        sending = False
        local = True
        if local == True:
            while True: # Check for invalid input
                user_select = input("Select Mode - Manual 1, Auto 2, Levels 3: ")
                if int(user_select) == 1 or int(user_select) == 2 or int(user_select) == 3:
                    # User choose auto control
                    if int(user_select) == 2: 
                        while True: # Check for invalid input
                            target_height = int(input("Enter Target Height in mm: ")) # User input becomes new target height
                            if target_height > 100 and target_height < 300:
                                Auto_Control()
                                if speed < 550: # Set starting speed immediatly
                                    speed = 550
                                break
                            else:
                                print("Height should be between 100 and 300 mms")
                        local = False
                        type = "Auto" # Set type to auto
                    # User choose level control
                    elif int(user_select) == 3:
                        while True: # Check for invalid input
                            select_level = input("Select height level 1-4: ")
                            if int(select_level) == 1 or int(select_level) == 2 or int(select_level) == 3 or int(select_level) == 4:
                                if int(select_level) == 1:
                                    Level_Control(1)
                                elif int(select_level) == 2:
                                    Level_Control(2)
                                elif int(select_level) == 3:
                                    Level_Control(3)
                                elif int(select_level) == 4:
                                    Level_Control(4)
                                break
                            else:
                                print("Select level 1-4")
                        local = False
                        type = "Level" # Set type to level
                    # User choose manual control
                    else:
                        local = False
                        type = "Manual"
                    break
                else:
                    print("Please enter valid number")
                    
        # Execute control function
    else:
        if type == "Manual":
            if sending == False:
                Manual_Control()
                return_value()
            else:
                set_speed(speed)
                get_rpm()
                return_value()
                time.sleep(0.1)
        elif type == "Auto":
            Auto_Control()
            return_value()
        elif type == "Level":
            get_current_height()
            get_rpm()
            return_value()
            time.sleep(0.1)
    
    
    # Code to continuously try to retrieve data from interface with similar code to above
    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:  # Non-blocking check
        control_input = sys.stdin.readline().strip()
        if control_input == '0':  # Stop sending data
            sending = True
            local = False
            if sending == True:
                while True:
                    sys.stdout.write("Select Mode - Manual 1, Auto 2, Levels 3: ")
                    user_input = sys.stdin.readline().strip()
                    if user_input == '1':
                        while True:
                            sys.stdout.write("Select Manual Type - Slide 1, Number Input 2: ")
                            manual_type = int(sys.stdin.readline().strip())
                            if manual_type == 2:
                                sys.stdout.write("Enter Target Speed in 0-100%: ")
                                target_speed = int(sys.stdin.readline().strip())
                                if target_speed <= 100 and target_speed >= 0:
                                    speed = target_speed * 10
                                    break
                                else:
                                    sys.stdout.write("Speed should be between 0 and 100 %")
                            else:
                                sending = False
                                break
                        type = "Manual"
                        break  # Exit the input loop and resume sending data
                    elif user_input == '2':
                        while True:
                            sys.stdout.write("Enter Target Height in mm: ")
                            target_height = int(sys.stdin.readline().strip())
                            if target_height > 100 and target_height < 300:
                                Auto_Control()
                                if speed < 550: # Set starting speed immediatly
                                    speed = 550
                                break
                            else:
                                sys.stdout.write("Height should be between 100 and 300 mms")
                        type = "Auto"
                        break  # Exit the input loop and resume sending data
                    elif user_input == '3':
                        while True:
                            sys.stdout.write("Select height level 1-4: ")
                            select_level = sys.stdin.readline().strip()
                            if int(select_level) == 1 or int(select_level) == 2 or int(select_level) == 3 or int(select_level) == 4:
                                if int(select_level) == 1:
                                    Level_Control(1)
                                elif int(select_level) == 2:
                                    Level_Control(2)
                                elif int(select_level) == 3:
                                    Level_Control(3)
                                elif int(select_level) == 4:
                                    Level_Control(4)
                                break
                            else:
                                sys.stdout.write("Select level 1-4")
                        type = "Level"
                        break  # Exit the input loop and resume sending data
                    else:
                        sys.stdout.write("Manual 1, Auto 2, Levels 3: ")
            else:
                sys.stdout.write("Invalid input. Please enter 0 to stop.\n")
