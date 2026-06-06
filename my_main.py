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

# config values
OPEN_THRESHOLD = 10
CLOSE_THRESHOLD = 1700

WINDOW_OPEN = 1
WINDOW_CLOSED = 0
WINDOW_UNKNOWN = -1

LOG_FILE = "readings.csv"
log_counter = 0

def get_local_time():
    t = time.localtime()

    timestamp_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2],
        t[3], t[4], t[5]
    )
    return timestamp_str

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

def logic(temp, lumin):
    global window_state, log_counter

    print(f"Temperature: {temp:.2f} C\tLux: {lumin:.2f}")

    if lumin < OPEN_THRESHOLD:
        print("OPENING WINDOW")

    if lumin > CLOSE_THRESHOLD:
        print("CLOSING WINDOW")

    log_counter+=1
    log_readings(temp, lumin)


try:
    with open(LOG_FILE, "r"):
        pass
except OSError:
    with open(LOG_FILE, "w") as f:
        f.write("timestamp,temp_c,lux\n")

while True:
    try:
        temp = temperature.read()
        lumin = lux.read_lux()

        logic(temp, lumin)

    except Exception as e:
        print("Sensor error:", e)
    
    time.sleep(1)

