from machine import I2C, Pin
import time
import vl53l0x  # Ensure you have the VL53L0X library

#Initialize I2C for VL53L0X
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
sensor = vl53l0x.VL53L0X(i2c)
sensor.start()

#Function to print out the corrected measured height
def print_height(): 
    distance = sensor.read()  # Get distance in mm
    corrected_distance = distance -35  # Apply -35 mm error correction from sensor
    print(corrected_distance,"mm")

try:
    while True:
        print_height()
        time.sleep(0.5)

except KeyboardInterrupt:
    sensor.stop()