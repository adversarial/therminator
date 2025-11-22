# Therminator - thermostat emulator to test functionality
# Copyright (C) 2025 adversarial

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


import machine
from machine import WDT
import utime
import uasyncio

# in case of a fault causing all of MCU to hang (like in IRQ) this will reset hardware

# implement https://docs.micropython.org/en/latest/library/machine.WDT.html for pi pico 
# Notes: On the esp8266 a timeout cannot be specified, it is determined by the underlying system. On rp2040 devices, the maximum timeout is 8388 ms.
RP20xx_MAX_WATCHDOG_TIMEOUT = 8388

class WatchdogTimer:

    def __init__(self, timeout = RP20xx_MAX_WATCHDOG_TIMEOUT, autofeed = True):
        self._timeout = timeout if timeout in range(0, RP20xx_MAX_WATCHDOG_TIMEOUT) else RP20xx_MAX_WATCHDOG_TIMEOUT
        self._timer = WDT(timeout = self._timeout)
        self.feed()

        if autofeed:
            uasyncio.create_task(create_autofeeder())

    def feed(self):
        self._timer.feed()

watchdog_timer = WatchdogTimer()

async def create_autofeeder():
    global watchdog_timer

    autofeeder = machine.Timer(-1)
    autofeeder.init(mode = machine.Timer.PERIODIC, period = int(watchdog_timer._timeout / 4), callback = autofeeder_callback)

def autofeeder_callback(t: machine.Timer):
    global watchdog_timer

    watchdog_timer.feed()

def Watchdog_Feeder(func):
    def wrapper(*args, **kwargs):
        watchdog_timer.feed()
        result = func(*args, **kwargs)
        watchdog_timer.feed()
        return result
    return wrapper
