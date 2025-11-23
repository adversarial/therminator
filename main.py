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
from machine import reset

import source.config as config
from source.access import access_point
from source.board import onboard_led
from source.http_server import http_server

onboard_led.on()
print("Initializing...")
config.parse_config()
print("Starting services...")
try:
    assert uasyncio.run(access_point.run())
    assert uasyncio.run(http_server.run())
except Exception as e:
    print(e)
    reset()

print(f'Started access point {access_point.name()} with key {access_point.key()} with webpage at http://{access_point.ap().ifconfig()[0]}')
loop = uasyncio.get_event_loop()
loop.run_forever()