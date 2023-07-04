"""
quickstart manual
1. Turn on pi
2. On pi use `raspivid -t 1000000` to aim the camera at the center of bottom left well (bottom refers to closest physically to user)
3. Turn on the printer (physical switch)
4. Set up the wells you'd like to image (WELLS variable in code)
5. Run desired script - `python3 script_name.py`
"""

import serial
import time
import RPi.GPIO as GPIO
import picamera
from datetime import datetime

# Set the GPIO mode to BCM
GPIO.setmode(GPIO.BCM)

# Set pin 18 as output
GPIO.setup(18, GPIO.OUT)

# just so that camera exists
camera = None

# Parameters
X_DISTANCE = 26 # do not change
Y_DISTANCE = 26 # do not change
LASER_ON_GPIO_PIN = 18 # do not change
PORT = "/dev/ttyACM0"  # Replace with your port
VIDEO_NAME = "test"  # Replace with your desired video name; can be a path to an arbitrary folder

# Time parameters
PRE_PROCESS_TIME = 10 # do not set below 7 - needed to let camera finish movement
START_RECORDING_TIME = 2 # time before laser
LASER_ON_TIME = 5 # how long laser should be on
POST_PROCESS_TIME = 2 # how long to image for after laser turns off

# mark wells you want to visit with 'o'
WELLS = [
    ['v', 'v', 'v', 'o'],
    ['v', 'v', 'o', 'v'],
    ['v', 'o', 'v', 'v']
]

class PrinterController:
    def __init__(self, port, baudrate=250000):
        self.serial = serial.Serial(port, baudrate)
        time.sleep(2)  # Give time for printer to initialize

    def send_command(self, command):
        self.serial.write((command + '\n').encode())
        time.sleep(0.1)  # Give printer time to process command
        while self.serial.inWaiting():
            print(self.serial.readline().strip().decode('utf-8', 'ignore'))  # Print printer's response

    def move(self, x=None, y=None):
        command = "G91"  # Set to relative positioning
        self.send_command(command)

        move_command = "G1"  # Linear move command
        if x is not None:
            move_command += " X{}".format(x)
        if y is not None:
            move_command += " Y{}".format(y)

        self.send_command(move_command)

        command = "G90"  # Set back to absolute positioning
        self.send_command(command)

    def process_wells(self, wells, x_distance, y_distance):
        # These are needed to home the printer after scanning all wells
        total_x_dist = 0
        total_y_dist = 0

        # Run through wells
        for i, row in enumerate(wells):
            for j, well in enumerate(row):
                if well == 'o':
                    print(f"Processing well at ({j}, {i})")
                    # activate camera
                    camera = picamera.PiCamera()
                    time.sleep(PRE_PROCESS_TIME)
                    # Roll the tape
                    dt = datetime.now().strftime('%d-%m-%Y-%H-%M-%S')
                    camera.start_recording(f"{VIDEO_NAME}_{dt}_{i}_{j}.h264")
                    time.sleep(START_RECORDING_TIME)
                    # Turn laser on
                    GPIO.output(LASER_ON_GPIO_PIN, GPIO.HIGH)
                    camera.annotate_text = "*"  # Add asterisk
                    time.sleep(LASER_ON_TIME)
                    # Turn laser off
                    GPIO.output(LASER_ON_GPIO_PIN, GPIO.LOW)
                    camera.annotate_text = ""  # Remove asterisk
                    time.sleep(POST_PROCESS_TIME)
                    # Turn camera off
                    camera.stop_recording()
                    camera.close()

                # Move to the next well in the row unless it's the last well
                if j != len(row) - 1:
                    self.move(x=x_distance)
                    total_x_dist += x_distance

            # Move to the next row unless it's the last row
            if i != len(wells) - 1:
                self.move(y=y_distance)
                total_y_dist += y_distance

            # If it's not the last row, move back to the start of the row
            if i != len(wells) - 1:
                self.move(x=-x_distance * (len(row) - 1))

        # Home -> move to first well
        self.move(x=-total_x_dist, y=-total_y_dist)

if __name__ == "__main__":
    printer = PrinterController(port=PORT)
    printer.process_wells(WELLS[::-1], X_DISTANCE, Y_DISTANCE)
