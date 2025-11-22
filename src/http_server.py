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

from nanoweb.nanoweb import Nanoweb, HttpError, send_file, authenticate
import machine
import json
import utime
import uasyncio


PIN_SW1 = 12
PIN_SW2 = 13
PIN_SW3 = 14
PIN_SW4 = 15

from src.channeler import channels

CREDENTIALS = ('098765432123456', # user
               '123456789098765') # pass

WEB_ASSETS_DIR = './www/'
STORED_LOGS_DIR = './www/logs/'

MAX_REQUEST_HANDLERS = 10
MAX_REQUEST_MS = 100 # we don't need a fast server, and want to prevent rapidfiring of relays

http_server = Nanoweb()
last_request = utime.ticks_ms()
request_semaphore = uasyncio.Semaphore(MAX_REQUEST_HANDLERS)

def HTTP_DOS_Guard(func):
    async def decorator(*args, **kwargs):
        global last_request
        await request_semaphore.acquire()

        while utime.ticks_diff(utime.ticks_ms(), last_request) < MAX_REQUEST_MS:
            await uasyncio.sleep_ms(MAX_REQUEST_MS / 4)

        try:
            result = await func(*args, **kwargs)
            last_request = utime.ticks_ms()
        finally:
            request_semaphore.release()
        
        return result
    return decorator

@HTTP_DOS_Guard
@authenticate(credentials=CREDENTIALS)
@http_server.route("/api/shutdown")
async def api_shutdown(request):
    await request.write("HTTP/1.1 200 OK\r\n")

    if request.method != "POST":
        raise HttpError(request, 501, "Not Implemented")

    print("Shutdown requested")

@HTTP_DOS_Guard
@authenticate(credentials=CREDENTIALS)
@http_server.route("/api/set_relay_pwr")
async def api_set_relay_power(request):
    if request.method != "POST":
        raise HttpError(request, 501, "Not Implemented")
    
    await request.write("HTTP/1.1 200 OK\r\n")

    try:
        content_length = int(request.headers['Content-Length'])
        content_type = request.headers['Content-Type']
    except KeyError:
        raise HttpError(request, 400, "Bad Request")
    
    if 'application/json' not in content_type:
        raise HttpError(request, 501, "Not Implemented")
    
    data = json.loads(await request.read(content_length)).decode()
    if data == ('1',):
        channels.channel_power.enable()
    elif data == ('0',):
        channels.channel_power.disable()
    else:
        raise HttpError(request, 400, "Bad Request")

@HTTP_DOS_Guard
@authenticate(credentials=CREDENTIALS)
@http_server.route("/api/get_relay_pwr")
async def api_query_relay_power(request):
    if request.method != "GET":
        raise HttpError(request, 501, "Not Implemented")
    
    await request.write("HTTP/1.1 200 OK\r\n")
    await request.write("Content-Type: application/json\r\n\r\n")

# Process a request to set channel states
# ie [ {i, 0}, {j, 1}, {k, 1} ]
# -> disable i, enable j, k
# TODO correct processing to iterate [ {,},{,} ] along with {,}
@HTTP_DOS_Guard
@authenticate(credentials=CREDENTIALS)
@http_server.route("/api/set_channel_states")
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
    
    requested_channels = []

    for item in json.loads(data).values():
        # find a better way to determine if it's a sublist to set multiple items
        try: 
            requested_channels.append((item["channel"], item["enable"]))
        except TypeError:
            for subitem in item:
                requested_channels.append((subitem["channel"], subitem["enable"]))
    
    try:
        channels.set(*requested_channels)
    except:
        raise HttpError(request, "500", "Internal Server Error")
        

# Responds to request with json dump of channel ids and states 
# ie [ {i, a}, {j, b},... {y, z} ]
@HTTP_DOS_Guard
@authenticate(credentials=CREDENTIALS)
@http_server.route("/api/get_channel_states")
async def api_get_channel_states(request):
    if request.method != "GET":
        raise HttpError(request, 501, "Not Implemented")
    
    await request.write("HTTP/1.1 200 OK\r\n")
    await request.write("Content-Type: application/json\r\n\r\n")

    # [ 
    #     { channel: 1, enable: 0 }, 
    #     { channel: 0, enable: 1 }, 
    #     { ... } 
    # ]
    channel_status = '[ ' + ', '.join(f'{{"channel": {i}, "enable": {c} }}' for i, c in channels.enumerate()) + ' ]'
    await request.write(channel_status)

@HTTP_DOS_Guard
@http_server.route("/")
async def homepage(request):
    print(request)
    await request.write("HTTP/1.1 200 OK\r\n\r\n")
    await send_file(request, f'{WEB_ASSETS_DIR}/index.html')
    
@HTTP_DOS_Guard 
@http_server.route("/ping")
async def ping(request):
    await request.write("HTTP/1.1 200 OK\r\n\r\n")
    await request.write("pong")
    print("pong")

