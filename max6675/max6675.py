from machine import Pin, SPI
import time

class MAX6675:
    def __init__(self, spi, cs):
        self.spi = spi
        self.cs = cs
        self.cs.value(1)

    def read(self):
        buf = bytearray(2)

        self.cs.value(0)
        self.spi.readinto(buf)
        self.cs.value(1)

        value = (buf[0] << 8) | buf[1]

        if value & 0x04:
            raise Exception("Thermocouple not connected")

        return ((value >> 3) & 0x0FFF) * 0.25
