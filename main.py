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

import uasyncio
import machine 
import network
import utime

from src.http_server import http_server
import src.watchdog as watchdog

ssid = 'thermoset'
password = '1234567890'

onboard_led = machine.Pin("LED", machine.Pin.OUT)

watchdog.watchdog_timer.feed()

print("Initializing...")
onboard_led.on()
ap = network.WLAN(network.AP_IF)
ap.config(ssid = ssid, key = password, security = 4) # 4 = WPA2 (insecure, highest supported)
ap.active(True)
utime.sleep_ms(250)
assert(ap.active())

loop = uasyncio.get_event_loop()
loop.create_task(http_server.run())
print(f'Started webserver at {ap.ifconfig()[0]}')
loop.run_forever()