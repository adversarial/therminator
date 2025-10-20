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

import asyncio
from nanoweb.nanoweb import Nanoweb, HttpError, send_file, authenticate
import network
import machine

PIN_SW1 = 12
PIN_SW2 = 13
PIN_SW3 = 14
PIN_SW4 = 15

channels = (machine.Pin(PIN_SW1, mode=machine.Pin.OUT),
            machine.Pin(PIN_SW2, mode=machine.Pin.OUT),
            machine.Pin(PIN_SW3, mode=machine.Pin.OUT),
            machine.Pin(PIN_SW4, mode=machine.Pin.OUT))

ssid = 'therminator'
password = '1234567890'

CREDENTIALS = ('098765432123456', # user
               '123456789098765') # pass

WEB_ASSETS_DIR = './www/'
STORED_LOGS_DIR = './www/logs/'

onboard_led = machine.Pin("LED", machine.Pin.OUT)

webserver = Nanoweb()

import json

# Process a request to set channel states
# ie [ {i, 0}, {j, 1}, {k, 1} ]
# -> disable i, enable j, k
# TODO correct processing to iterate [ {,},{,} ] along with {,}
@authenticate(credentials=CREDENTIALS)
@webserver.route("/api/set_channel_states")
async def api_set_channel_states(request):
    await request.write("HTTP/1.1 200 OK\r\n")

    if request.method != "POST":
        raise HttpError(request, 501, "Not Implemented")

    try:
        content_length = int(request.headers['Content-Length'])
        content_type = request.headers['Content-Type']
    except KeyError:
        raise HttpError(request, 400, "Bad Request")

    data = (await request.read(content_length)).decode()
    if 'application/json' not in content_type:
        raise HttpError(request, 501, "Not Implemented")
    
    for item in json.loads(data).values():
        # find a better way to determine if it's a sublist to set multiple items
        try: 
            channels[item["channel"]].value(item["enable"])
        except TypeError:
            for subitem in item:
                channels[subitem["channel"]].value(subitem["enable"])

# Responds to request with json dump of channel ids and states 
# ie [ {i, a}, {j, b},... {y, z} ]
@authenticate(credentials=CREDENTIALS)
@webserver.route("/api/get_channel_states")
async def api_get_channel_states(request):
    if request.method != "GET":
        raise HttpError(request, 501, "Not Implemented")
    
    await request.write("HTTP/1.1 200 OK\r\n")
    await request.write("Content-Type: application/json\r\n\r\n")

    channel_status = '[ ' + ','.join(f'{{"channel": {i}, "enable": {c.value()} }}' for i, c in enumerate(channels)) + ' ]'
    await request.write(channel_status)

@webserver.route("/")
async def homepage(request):
    await request.write("HTTP/1.1 200 OK\r\n\r\n")
    await send_file(request, f'./{WEB_ASSETS_DIR}/index.html')
    print(request)
    
@webserver.route("/ping")
async def ping(request):
    await request.write("HTTP/1.1 200 OK\r\n\r\n")
    await request.write("pong")
    print("pong")
    
print("Initializing...")
onboard_led.on()
ap = network.WLAN(network.AP_IF)
ap.config(ssid = ssid, key = password, security = 4)
ap.active(True)
print(f'Started access point "{ssid}" with password "{password}"')

loop = asyncio.get_event_loop()
loop.create_task(webserver.run())
print("Running webserver")

loop.run_forever()