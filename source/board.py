

# 5V relay uses 2-5Vin boost from 2-3xAA batteries, has enable pin that hard shuts off on low->ground
PIN_5V_EXTERNAL_PWR_ENABLE = None

# optocoupler 4 channel relay can be triggered with 3.3V
PIN_RELAY_SWITCH_0 = None
PIN_RELAY_SWITCH_1 = None
PIN_RELAY_SWITCH_2 = None
PIN_RELAY_SWITCH_3 = None

from machine import Pin
onboard_led = Pin("LED", Pin.OUT, value=0)
