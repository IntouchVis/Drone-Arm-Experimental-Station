from machine import Pin, PWM
import time

esc_pin = Pin(4, Pin.OUT)  # ESC signal pin connected to GPIO 4
pwm = PWM(esc_pin)
pwm.freq(50)  # ESC expect a frequency of 50Hz

#Function to set the rotation speed of the motor in percentage
def set_speed(percentage): 
    length = (percentage*10) + 1000 # ESC communicates with a pulse range between 1000 and 2000 microseconds
    duty = int((length/20000)* 65535) # Turn percentage into 16-bit duty cycle
    
    #duty = int(((percentage/100)*1671)+4030) # Percentage to duty cycle specifally for this esc
    # 23 = 0 = 4030 74 = 100 = 5701
    
    pwm.duty_u16(duty)

set_speed(0)
time.sleep(6)

while True:
    try:
        user_input = input("Enter PWM duty cycle percentage (0-100): ") # Ask the user for a speed percentage (0-100)
        duty_percentage = int(user_input) # Convert input to integer
        if 0 <= duty_percentage <= 100:
            set_speed(duty_percentage) # Set the speed based on input
        else:
            print("Please enter a value between 0 and 100.")

    except ValueError:
        print("Invalid input. Please enter an integer between 0 and 100.")