import serial
import time
import RPi.GPIO as GPIO
import picamera

# Set the GPIO mode to BCM
GPIO.setmode(GPIO.BCM)

# Set pin 18 as output
GPIO.setup(18, GPIO.OUT)

# just so that camera exists
camera = None

# Printer controls - use:
# move(x displacement, y displacement)
# or
# process_wells(---) [modify as you like]
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
                    # Just rolling
                    # time.sleep(10)  # Pause for 10 seconds
                    # LASERS! AND CAMERAS
                    # EDIT THIS!
                    time.sleep(10)
                    camera.start_recording(f"test_{i}_{j}.h264")
                    time.sleep(2)
                    GPIO.output(18, GPIO.HIGH)
                    time.sleep(5)
                    GPIO.output(18, GPIO.LOW)
                    time.sleep(2)
                    camera.stop_recording()

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
    printer = PrinterController(port="/dev/ttyACM0")  # Replace with your port
    camera = picamera.PiCamera()

    X_DISTANCE = 26
    Y_DISTANCE = 26

    # mark wells you want to visit with 'o'
    WELLS = [
        ['v', 'v', 'v', 'o'],
        ['v', 'v', 'o', 'v'],
        ['v', 'o', 'v', 'v']
    ]

    printer.process_wells(WELLS[::-1], X_DISTANCE, Y_DISTANCE)
    camera.close()

