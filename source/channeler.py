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

import source.board as board

DEFAULT_COOLING_IDS = ('R', 'Y', 'Y2', 'O/B/G')
DEFAULT_HEATING_IDS = ('R', 'W', 'W2', 'G')

MAX_RELAY_POWER_TIMEOUT_MS = 60*60*1000 # one hour in ms

class external_power_manager:
    def __init__(self, gpio_id, enabled = False, timeout = MAX_RELAY_POWER_TIMEOUT_MS):

        self._gpio_id = gpio_id
        self._pin = machine.Pin(gpio_id, 
                               mode = machine.Pin.OUT, 
                               value = 1 if enabled else 0)
        self._timeout = timeout
        self._timer = machine.Timer(-1)

        if enabled:
            self.enable()

    def enable(self):
        if self._pin.value() > 0:
            return
        
        self._pin.value(1)
        self._timer.init(mode = machine.Timer.ONE_SHOT, 
                        period = self._timeout, 
                        callback = channel_timeout_callback)

    def disable(self):
        if self._pin.value() == 0:
            return 
        
        self._pin.value(0)
        self._timer.deinit()

    def query(self):
        return self._pin.value()

class channel:
    def __init__(self, pin, initial_value = None, id = None):
        self._gpio_id = pin
        self._pin = machine.Pin(self._gpio_id)
        self._id = id
        self._last_triggered = utime.ticks_ms()

        if initial_value:
            self.set(initial_value)

    def set(self, enabled):
        self._last_triggered = utime.ticks_ms()
        return self._pin.value(1 if enabled else 0)

    def get(self):
        return self._pin.value()
    
    def get_id(self):
        return self._id
    
    def get_gpio_id(self):
        return self._gpio_id

    def get_last_trigger(self):
        return self._last_triggered

class channel_manager:
    def __init__(self, pins, initial_values = (None,), ids = (None,)):
        self._pins = pins
        self._ids = ids
        self._channels = []
        self.channel_power = external_power_manager(gpio_id=board.PIN_5V_EXTERNAL_PWR_ENABLE)

        for pin, value, id in zip(pins, initial_values, ids):
            if id not in self:
                self.add_channel(pin, value, id)
            else:
                raise KeyError(f'Duplicate IDs provided to channel manager: "{id}" already exists.')

    def __contains__(self, id):
        return any(filter(lambda c: c.get_id().lower() == id.lower(), self._channels))
        
    def add_channel(self, pin, initital_value, id = "x"):
        self._channels.append(channel(pin, initital_value, id))

    def enumerate(self):
        return [ (channel.get_gpio_id(), channel.get_value()) for channel in self._channels ]   

    def get_channel_by_id(self, id) -> channel:
        return next(filter(lambda c: c.get_id().lower() == id.lower(), self._channels))

    def set(self, channels, values):
        for channel, value in zip(channels, values):
            self.get_channel_by_id(channel).set(value)

    def disable_all(self):
        for channel in self._channels:
            channel.set_value(0)
        self.channel_power.disable()

channels = channel_manager(pins = (board.PIN_RELAY_SWITCH_0, board.PIN_RELAY_SWITCH_1, board.PIN_RELAY_SWITCH_2, board.PIN_RELAY_SWITCH_3),
                           initial_values = (0, 0, 0, 0),
                           ids = DEFAULT_HEATING_IDS)

def channel_timeout_callback(t: machine.Timer):
    for channel in channels._channels:
        channel.pin.value(0)
    channels.channel_power._pin.value(0)