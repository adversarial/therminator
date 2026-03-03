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

from watchdog import http_watchdog
from source.channeler import channels

import json
import utime
import uasyncio

### initialized by config
WEB_ASSETS_DIR = None
STORED_LOGS_DIR = None
ENABLE_WATCHDOG = False
API_CREDENTIALS = (None, # user
                   None) # pass
###

MAX_API_REQUEST_HANDLERS = 4 # the webpage is very static
MAX_API_REQUEST_MS = 50 # we don't need a fast server, and want to prevent rapidfiring of relays

last_request = utime.ticks_ms()
request_semaphore = uasyncio.Semaphore(MAX_API_REQUEST_HANDLERS)

# Nanoweb discards the underlying asyncio.server() created by .run() which can check status for watchdog
class tNanoweb(Nanoweb):
    def __init__(self, port=80, address='0.0.0.0'):
        return super().__init__(port, address)
    
    async def run(self):
        self.server = await super().run()
        if ENABLE_WATCHDOG:
            http_watchdog.start(check_webserver)
        return self.server
    
    async def is_serving(self): # yas
        return self.server.is_serving()

http_server = tNanoweb()

#watchdog check timer event
async def check_webserver(t):
    if http_server.is_serving():
        http_watchdog.feed()

def API_DOS_Guard(func):
    async def decorator(*args, **kwargs):
        global last_request
        await request_semaphore.acquire()

        while utime.ticks_diff(utime.ticks_ms(), last_request) < MAX_API_REQUEST_MS:
            await uasyncio.sleep_ms(MAX_API_REQUEST_MS / MAX_API_REQUEST_HANDLERS)

        try:
            result = await func(*args, **kwargs)
            last_request = utime.ticks_ms()
        finally:
            request_semaphore.release()
        
        return result
    return decorator

@API_DOS_Guard
@authenticate(credentials=API_CREDENTIALS)
@http_server.route("/api/shutdown")
async def api_shutdown(request):
    await request.write("HTTP/1.1 200 OK\r\n")

    if request.method != "POST":
        raise HttpError(request, 501, "Not Implemented")

    print("Shutdown requested")

@API_DOS_Guard
@authenticate(credentials=API_CREDENTIALS)
@http_server.route("/api/set_relay_pwr")
async def api_set_relay_power(request):
    if request.method != "POST":
        await request.error(request, 501, "Not Implemented")
        return
    try:
        content_length = int(request.headers['Content-Length'])
        content_type = request.headers['Content-Type']
    except KeyError:
        await request.error(request, request, 400, "Bad Request")
        return
    
    if 'application/json' not in content_type:
        await request.error(request, 501, "Not Implemented")
        return

    await request.write("HTTP/1.1 200 OK\r\n")
    
    data = json.loads(await request.read(content_length)).decode()
    print(data)
    if data.value == ('1',):
        channels.channel_power.enable()
    elif data.value == ('0',):
        channels.channel_power.disable()
    else:
        await request.error(request, 400, "Bad Request")
        raise HttpError(request, 400, "Bad Request")
    

@API_DOS_Guard
@authenticate(credentials=API_CREDENTIALS)
@http_server.route("/api/get_relay_pwr")
async def api_query_relay_power(request):
    if request.method != "GET":
        await request.error(request, 501, "Not Implemented")
        raise HttpError(request, 501, "Not Implemented")
    
    response = json.dumps({ "value": f'{channels.channel_power.query()}' })

    headers = ( "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response)}\r\n\r\n"
    )
    
#    relay_pwr_status = '[ ' + f'{{ "value": {channels.channel_power.query()} }}' + ' ]'
    print(response)
    await request.write(headers + response)

# Process a request to set channel states
# ie [ {i, 0}, {j, 1}, {k, 1} ]
# -> disable i, enable j, k
# TODO correct processing to iterate [ {,},{,} ] along with {,}
@API_DOS_Guard
@authenticate(credentials=API_CREDENTIALS)
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
@API_DOS_Guard
@authenticate(credentials=API_CREDENTIALS)
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
    #for channel, value in channels.enumerate():
    #    pass
    channel_status = '[ ' + ', '.join(f'{{"channel": {i}, "enable": {c} }}' for i, c in channels.enumerate()) + ' ]'
    response = channel_status

    headers = ( "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(response)}\r\n\r\n"
    )
    
    await request.write(channel_status)

@http_server.route("/")
async def homepage(request):
    print(request)
    await request.write("HTTP/1.1 200 OK\r\n\r\n")
    await send_file(request, f'{WEB_ASSETS_DIR}/index.html')
    
@http_server.route("/ping")
async def ping(request):
    await request.write("HTTP/1.1 200 OK\r\n\r\n")
    await request.write("pong")
    print("pong")