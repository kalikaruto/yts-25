# standard libraries
from machine import Pin, I2C, SPI
import time
import sys

# dependencies
from veml7700 import VEML7700
from max6675 import MAX6675

# setup lux sensor
i2c = I2C(1, scl=Pin(22), sda=Pin(21), freq=10000)
#setup lux sensor with intergartion time 100 ms and gain 1/8
lux = VEML7700(address=0x10, i2c=i2c, it=100, gain=1/8)


# setup temperature sensor
spi = SPI(
    1,
    baudrate=1000000,
    polarity=0,
    phase=0,
    sck=Pin(18),
    miso=Pin(19)
)
cs = Pin(5, Pin.OUT)
temperature = MAX6675(spi, cs)

# setup motor
step = Pin(2, Pin.OUT)
dir = Pin(15, Pin.OUT)
en = Pin(4, Pin.OUT)
en.value(1) # disable for now

# config values
OPEN_THRESHOLD = 10
CLOSE_THRESHOLD = 1700

WINDOW_OPEN = 1
WINDOW_CLOSED = 0
WINDOW_UNKNOWN = -1

LOG_FILE = "readings.csv"
log_counter = 0

# limit switches
open_limit = Pin(23, Pin.IN, Pin.PULL_DOWN)
close_limit = Pin(17, Pin.IN, Pin.PULL_DOWN)

def get_local_time():
    t = time.localtime()

    timestamp_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2],
        t[3], t[4], t[5]
    )
    return timestamp_str

def switch_pressed(pin):
    if pin.value():
        time.sleep_ms(20)
        return pin.value()
    return False

def move_until_limit(limit_pin, delay=500, max_steps=1600):
    en.value(0)

    try:
        steps = 0

        while not switch_pressed(limit_pin):
            step.value(1)
            time.sleep_us(delay)

            step.value(0)
            time.sleep_us(delay)

            steps += 1

            if steps >= max_steps:
                print("ERROR: limit switch not reached")
                print("RESTART")
                sys.exit(0)
                return False

        return True

    finally:
        en.value(1)

def log_readings(temp, lumin):
    global log_counter
    
    if log_counter < 5:
        return
    log_counter = 0
    print(f"window is { 'CLOSED' if window_state==WINDOW_CLOSED else 'OPEN'}")
    ts = get_local_time()

    with open(LOG_FILE, "a") as f:
        f.write("{},{:.2f},{:.2f}\n".format(
            ts,
            temp,
            lumin
        ))
    
def open_window():
    global window_state

    if window_state == WINDOW_OPEN:
        return

    if switch_pressed(open_limit):
        window_state = WINDOW_OPEN
        return

    print("opening")

    dir.value(1)

    success = move_until_limit(open_limit)

    if success:
        window_state = WINDOW_OPEN
        print("fully opened")
    else:
        print("failed to open")


def close_window():
    global window_state

    if window_state == WINDOW_CLOSED:
        return

    if switch_pressed(close_limit):
        window_state = WINDOW_CLOSED
        return

    print("closing")

    dir.value(0)

    success = move_until_limit(close_limit)

    if success:
        window_state = WINDOW_CLOSED
        print("fully closed")
    else:
        print("failed to close")

def logic(temp, lumin):
    global window_state, log_counter

    print(f"Temperature: {temp:.2f} C\tLux: {lumin:.2f}")

    if window_state == WINDOW_CLOSED:
        if lumin < OPEN_THRESHOLD:
            open_window()

    elif window_state == WINDOW_OPEN:
        if lumin > CLOSE_THRESHOLD:
            close_window()
    else:
        print("UNKNOWN STATE")
        sys.exit()

    log_counter+=1
    log_readings(temp, lumin)


try:
    with open(LOG_FILE, "r"):
        pass
except OSError:
    with open(LOG_FILE, "w") as f:
        f.write("timestamp,temp_c,lux\n")

open_pressed = switch_pressed(open_limit)
close_pressed = switch_pressed(close_limit)

if open_pressed and close_pressed:
    print("ERROR: both limit switches active")
    window_state = WINDOW_UNKNOWN

elif open_pressed:
    window_state = WINDOW_OPEN

elif close_pressed:
    window_state = WINDOW_CLOSED

else:
    window_state = WINDOW_UNKNOWN

if window_state == WINDOW_UNKNOWN:
    print("Homing...")
    close_window()

while True:
    try:
        temp = temperature.read()
        lumin = lux.read_lux()

        logic(temp, lumin)

    except Exception as e:
        print("Sensor error:", e)
    
    time.sleep(1)

