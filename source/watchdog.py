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

from machine import WDT, Timer

# in case of a fault causing all of MCU to hang (like in IRQ) this will reset hardware

# implement https://docs.micropython.org/en/latest/library/machine.WDT.html for pi pico 
# Notes: On the esp8266 a timeout cannot be specified, it is determined by the underlying system. On rp2040 devices, the maximum timeout is 8388 ms.
RP20xx_MAX_WATCHDOG_TIMEOUT = 8388

class dummywdt:
    def __init__(self, id = None, timeout = None):
        pass
    def feed(self):
        pass

class WatchdogTimer:

    def __init__(self, id = 0, timeout = RP20xx_MAX_WATCHDOG_TIMEOUT, feeder_callback = None):
        self._timeout = timeout if timeout in range(0, RP20xx_MAX_WATCHDOG_TIMEOUT) else RP20xx_MAX_WATCHDOG_TIMEOUT
        self._timer = dummywdt()
        self._feeder = feeder_callback
        self._id = id

    def start(self, feeder_callback = None):
        self._timer = WDT(id = self._id, timeout=self._timeout)
        if feeder_callback:
            self.create_feeder(feeder_callback)

    def create_feeder(self, callback):
        autofeeder = Timer(-1)
        autofeeder.init(mode = Timer.PERIODIC, 
                        period = self._timeout >> 2, # timeout/4 to ensure we don't miss
                        callback = callback)

    def feed(self):
        self._timer.feed()

ap_watchdog = WatchdogTimer(id=1)
http_watchdog = WatchdogTimer(id=2)