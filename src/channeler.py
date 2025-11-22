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
import utime

PIN_SW1 = 12
PIN_SW2 = 13
PIN_SW3 = 14
PIN_SW4 = 15

PIN_EXT_PWR_ENABLE = 22

cooling_ids = ('R', 'Y', 'Y2', 'O/B/G')
heating_ids = ('R', 'W', 'W2', 'G')

class external_power_manager:
    def __init__(self, gpio_id = PIN_EXT_PWR_ENABLE, enabled = False, timeout = 30*60*1000):

        self.gpio_id = gpio_id
        self.pin = machine.Pin(gpio_id, 
                               mode = machine.Pin.OUT, 
                               value = True if enabled else False)
        self.timeout = timeout
        self.timer = machine.Timer(-1)

    def enable(self):
        if self.pin.value() > 0:
            return
        
        self.pin.value(1)
        self.timer.init(mode = machine.Timer.ONE_SHOT, 
                        period = self.timeout, 
                        callback = channel_timeout_callback)

    def disable(self):
        if self.pin.value == 0:
            return 
        
        self.pin.value(0)
        self.timer.deinit()

class channel:
    def __init__(self, pin, initial_value = None, id = None):
        self.gpio_id = pin
        self.pin = machine.Pin(self.gpio_id)
        self.value = None
        self.id = id
        self.last_triggered = utime.ticks_ms()

        if initial_value:
            self.set_value(initial_value)

    def set_value(self, value):
        self.last_triggered = utime.ticks_ms()
        return self.pin.value(value)

    def get_value(self):
        return self.pin.value()
    
    def get_gpio_id(self):
        return self.gpio_id

    def get_last_trigger(self):
        return self.last_triggered

class channel_manager:
    def __init__(self, pins, initial_values = (None,), ids = (None,)):
        self.pins = pins
        self.ids = ids
        self.channels = []
        self.channel_power = external_power_manager()

        for pin, value, id in zip(pins, initial_values, ids):
            self.add_channel(pin, value, id)
        
    def add_channel(self, pin, initital_value, id = "x"):
        self.channels.append(channel(pin, initital_value, id))

    def enumerate(self):
        return [ (channel.get_gpio_id(), channel.get_value()) for channel in self.channels ]   

    def get_channel_by_id(self, id) -> channel:
        return next(filter(lambda c: c.id.lower() == id.lower(), self.channels))

    def set(self, channels, values):
        for channel, value in zip(channels, values):
            self.get_channel_by_id(channel).set_value(value)

    def disable_all(self):
        for channel in self.channels:
            channel.set_value(0)
        self.channel_power.disable()

channels = channel_manager(pins = (PIN_SW1, PIN_SW2, PIN_SW3, PIN_SW4),
                           initial_values = (0, 0, 0, 0),
                           ids = ('R', 'W', 'W2', 'G'))

def channel_timeout_callback(t: machine.Timer):
    for channel in channels.channels:
        channel.pin.value(0)
    channels.channel_power.pin.value(0)