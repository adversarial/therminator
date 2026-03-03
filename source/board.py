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
from uasyncio import Semaphore, CancelledError, create_task
### initialized by config

# 5V relay uses 2-5Vin boost from 2-3xAA batteries, has enable pin that hard shuts off on low->ground
PIN_5V_EXTERNAL_PWR_ENABLE = None

# optocoupler 4 channel relay can be triggered with 3.3V
PIN_RELAY_SWITCH_0 = None
PIN_RELAY_SWITCH_1 = None
PIN_RELAY_SWITCH_2 = None
PIN_RELAY_SWITCH_3 = None

from machine import Pin
onboard_led_pin = Pin("LED", Pin.OUT, value=0)

class onboard_led_controller:
    def __init__(self,
                 led_pin = onboard_led_pin):
        self.led = led_pin
        self.current_task = None
        self.blink_lock = Semaphore(1)

# period_ms: amount of time to blink light, should be lower than TICKS_MAX (undocumented)
# rate_ms: how often to toggle light

    async def _blink_task(self, period_ms, rate_ms):
        try:
            async with self.blink_lock:
                begin_ticks = ticks_ms()
                while ticks_diff(begin_ticks, ticks_ms()) < period_ms:
                    self.led.toggle()
                    await async_sleep_ms(rate_ms)
        except CancelledError as e: 
            raise e
        finally:
            self.led.off()
    
    async def blink_led(self, period_ms = 7500, rate_ms = 750, override = False):
        if override and self.current_task and not self.current_task.done():
            self.current_task.cancel()
    
        self.current_task = await create_task(self._blink_task(period_ms, rate_ms))

onboard_led = onboard_led_controller()

class autopowersaver:
    def __init__(self, timeout=30*60*1000):
        pass
    