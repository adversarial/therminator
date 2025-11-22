

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
        self.pin.value(1)
        self.timer.init(mode = machine.Timer.ONE_SHOT, 
                        period = self.timeout, 
                        callback = channel_timeout_callback)

    def disable(self):
        self.pin.value(0)
        self.timer.deinit()

class channel:
    def __init__(self, pin, initial_value = None, id = None):
        self.gpio_id = pin
        self.value = None
        self.id = id
        self.last_triggered = utime.ticks_ms()

        if initial_value:
            self.set_value(initial_value)

    def set_value(self, value):
        self.last_triggered = utime.ticks_ms()
        return machine.Pin(self.gpio_id).value(value)

    def get_value(self):
        return machine.Pin(self.gpio_id).value()
    
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
        return [(channel.gpio_id, channel.get_value()) for channel in self.channels]   

    def get_channel_by_id(self, id) -> channel:
        return next(filter(lambda c: c.id.lower() == id.lower(), self.channels))

    def set(self, channels, values):
        for channel, value in zip(channels, values):
            if channel.id == 'R' and value:
                self.channel_power.enable()
            self.get_channel_by_id(channel).set_value(value)

    def disable_all(self):
        for channel in self.channels:
            channel.set_value(0)

channels = channel_manager(pins = (PIN_SW1, PIN_SW2, PIN_SW3, PIN_SW4),
                           initial_values = (0, 0, 0, 0),
                           ids = ('R', 'W', 'W2', 'G'))

def channel_timeout_callback(t: machine.Timer):
    for channel in channels.channels:
        channel.set_value(0)
    channels.channel_power.disable()
    t.deinit()

