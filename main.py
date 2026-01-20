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
import source.board as board
from source.access_point import access_point
from source.http_page import http_server

uasyncio.create_task(board.blink_led(period_ms=1000, rate_ms=200))
print("Initializing...")
config.parse_config()
print("Starting services...")

try:
    uasyncio.run(access_point.run())
    uasyncio.run(http_server.run())
except Exception as e:
    print(e)
    reset()
    
print(f'Started access point {access_point.name()} with key {access_point.key()}')
print(f'Started webpage at http://{access_point.ap().ifconfig()[0]}')
uasyncio.create_task(board.blink_led(period_ms=10000, rate_ms=1000))

loop = uasyncio.get_event_loop()
loop.run_forever()