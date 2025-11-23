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

from machine import Timer
from network import WLAN, AP_IF
from uasyncio import sleep as async_sleep

from source.watchdog import ap_watchdog

DEFAULT_SOFT_AP_SSID = None
DEFAULT_SOFT_AP_KEY = None
ENABLE_WATCHDOG = False

class soft_ap:
    def __init__(self, ssid = None, key = None):
        self._ssid = ssid
        self._key = key
        self._ap = WLAN(AP_IF)
    
    async def run(self, watchdog_enable = False):
        self._ap.config(ssid = self._ssid if self._ssid else DEFAULT_SOFT_AP_SSID,
                        key = self._key if self._key else DEFAULT_SOFT_AP_KEY, 
                        security = 4) # 4 = WPA2 (insecure, highest supported)
        self._ap.active(True)

        await async_sleep(1) # hotspot can take time to start
        assert self._ap.active()
        if ENABLE_WATCHDOG:
            ap_watchdog.start(check_ap) # this cannot be stopped; but this module asserts wifi is active entire time
        return True

    def ap(self):
        assert(self._ap.active())
        return self._ap
    
    def active(self):
        return self._ap.active()
    
    def name(self): 
        return self._ssid if self._ssid else DEFAULT_SOFT_AP_SSID
    
    def key(self):
        return self._key if self._key else DEFAULT_SOFT_AP_KEY

    
access_point = soft_ap()

def check_ap(t):
    if access_point.active():
        ap_watchdog.feed()