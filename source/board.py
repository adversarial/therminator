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

from uasyncio import sleep_ms as async_sleep_ms
from utime import ticks_ms, ticks_diff
from uasyncio import Lock, CancelledError, create_task
### initialized by config

# 5V relay uses 2-5Vin boost from 2-3xAA batteries, has enable pin that hard shuts off on low->ground
PIN_5V_EXTERNAL_PWR_ENABLE = None

# optocoupler 4 channel relay can be triggered with 3.3V
PIN_RELAY_SWITCH_0 = None
PIN_RELAY_SWITCH_1 = None
PIN_RELAY_SWITCH_2 = None
PIN_RELAY_SWITCH_3 = None


import collections
import uasyncio as asyncio
from utime import ticks_ms, ticks_diff
from machine import Pin

from source.flutter import flutter

onboard_led = flutter()