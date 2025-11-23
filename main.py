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

import source.config as config
from source.access import access_point
from source.http_server import http_server
from source.board import onboard_led

onboard_led.on()
print("Initializing...")
config.parse_config()

loop = uasyncio.get_event_loop()
loop.create_task(access_point.run())
loop.create_task(http_server.run())
print(f'Started webserver at {access_point.ap().ifconfig()[0]}')
loop.run_forever()