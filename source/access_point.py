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

from network import WLAN, AP_IF
from uasyncio import sleep as async_sleep

from source.watchdog import ap_watchdog

### initialized by config
DEFAULT_SOFT_AP_SSID = None
DEFAULT_SOFT_AP_KEY = None
ENABLE_WATCHDOG = False
###

STARTUP_RETRY_COUNT = 5
STARTUP_RETRY_DELAY_SEC = 1.0

class SoftAPError(Exception):
    def __init__(self, ssid, err, msg):
        self.ssid = ssid
        self.err = err
        self.msg = msg
        super().__init__(self.msg)

    def __str__(self):
        return f'Error starting AP "{self.ssid}" error: "{self.err}" {self.msg}.'

class soft_ap:
    def __init__(self, ssid = None, key = None):
        self._ssid = ssid
        self._key = key
        self._ap = WLAN(AP_IF)
    
    async def run(self):
        self._ap.config(ssid = self._ssid if self._ssid else DEFAULT_SOFT_AP_SSID,
                        key = self._key if self._key else DEFAULT_SOFT_AP_KEY, 
                        security = 4) # 4 = WPA2 (insecure, highest supported)
        self._ap.active(True)

        await async_sleep(1) # hotspot can take time to start, this is very generous
        
        for i in range(STARTUP_RETRY_COUNT):
            if not self.active():
                print('Web server not started yet, retrying.')
                self._ap.active(True)
                await async_sleep(STARTUP_RETRY_DELAY_SEC)
            else:
                break

        if not self._ap.active():
            raise SoftAPError(self._ssid, self._ap.status(), "Unable to create access point")
        
        if ENABLE_WATCHDOG:
            ap_watchdog.start(check_ap) 
        return True

    def ap(self):
        return self._ap
    
    def active(self):
        return self._ap.active()
    
    def name(self): 
        return self._ssid if self._ssid else DEFAULT_SOFT_AP_SSID
    
    def key(self):
        return self._key if self._key else DEFAULT_SOFT_AP_KEY
    
# exports
access_point = soft_ap()

def check_ap(t):
    if access_point.active():
        ap_watchdog.feed()