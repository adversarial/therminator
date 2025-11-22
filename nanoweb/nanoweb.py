# MIT License

# Copyright (c) 2020 Charles R.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# # Nanoweb

# Nanoweb is a full asynchronous web server for micropython created in order to benefit from
# a correct ratio between memory size and features.

# It is thus able to run on an ESP8266, ESP32, Raspberry Pico, etc...

# ## Features

# * Completely asynchronous
# * Declaration of routes via a dictionary or directly by decorator
# * Management of static files (see assets_extensions)
# * Callbacks functions when a new query or an error occurs
# * Extraction of HTML headers
# * User code dense and conci
# * Routing wildcards

# ## Installation

# You just have to copy the `nanoweb.py` file on the target (ESP32, Nano, etc...).

# ## Use

# See the [example.py](example.py) file for an advanced example where you will be able to:

# * Make a JSON response
# * Use pages protected with credentials
# * Upload file
# * Use `DELETE` method
# * Read `POST` data

# And this is a simpler example:

# ```Python
# import uasyncio
# from nanoweb import Nanoweb

# naw = Nanoweb()

# async def api_status(request):
#     """API status endpoint"""
#     await request.write("HTTP/1.1 200 OK\r\n")
#     await request.write("Content-Type: application/json\r\n\r\n")
#     await request.write('{"status": "running"}')

# # You can declare route from the Nanoweb routes dict...
# naw.routes = {
#     '/api/status': api_status,
# }

# # ... or declare route directly from the Nanoweb route decorator
# @naw.route("/ping")
# async def ping(request):
#     await request.write("HTTP/1.1 200 OK\r\n\r\n")
#     await request.write("pong")

# loop = asyncio.get_event_loop()
# loop.create_task(naw.run())
# loop.run_forever()
# ```

# ## Contribute

# * Your code must respects `flake8` and `isort` tools
# * Format your commits with `Commit Conventional` (https://www.conventionalcommits.org/en/v1.0.0/)


import uasyncio as asyncio
import uerrno


__version__ = '1.0.0'


class HttpError(Exception):
    pass


class Request:
    url = ""
    method = ""
    headers = {}
    route = ""
    read = None
    write = None
    close = None

    def __init__(self):
        self.url = ""
        self.method = ""
        self.headers = {}
        self.route = ""
        self.read = None
        self.write = None
        self.close = None


async def write(request, data):
    await request.write(
        data.encode('ISO-8859-1') if type(data) == str else data
    )


async def error(request, code, reason):
    await request.write("HTTP/1.1 %s %s\r\n\r\n" % (code, reason))
    await request.write("<h1>%s</h1>" % (reason))



class Nanoweb:

    extract_headers = ('Authorization', 'Content-Length', 'Content-Type')
    headers = {}

    routes = {}
    assets_extensions = ('html', 'css', 'js')

    callback_request = None
    callback_error = staticmethod(error)

    STATIC_DIR = './'
    INDEX_FILE = STATIC_DIR + 'index.html'

    def __init__(self, port=80, address='0.0.0.0'):
        self.port = port
        self.address = address

    def route(self, route):
        """Route decorator"""
        def decorator(func):
            self.routes[route] = func
            return func
        return decorator

    async def generate_output(self, request, handler):
        """Generate output from handler

        `handler` can be :
         * dict representing the template context
         * string, considered as a path to a file
         * tuple where the first item is filename and the second
           is the template context
         * callable, the output of which is sent to the client
        """
        while True:
            if isinstance(handler, dict):
                handler = (request.url, handler)

            if isinstance(handler, str):
                await write(request, "HTTP/1.1 200 OK\r\n\r\n")
                await send_file(request, handler)
            elif isinstance(handler, tuple):
                await write(request, "HTTP/1.1 200 OK\r\n\r\n")
                filename, context = handler
                context = context() if callable(context) else context
                try:
                    with open(filename, "r") as f:
                        for l in f:
                            await write(request, l.format(**context))
                except OSError as e:
                    if e.args[0] != uerrno.ENOENT:
                        raise
                    raise HttpError(request, 404, "File Not Found")
            else:
                handler = await handler(request)
                if handler:
                    # handler can returns data that can be fed back
                    # to the input of the function
                    continue
            break

    async def handle(self, reader, writer):
        items = await reader.readline()
        items = items.decode('ascii').split()
        if len(items) != 3:
            return

        request = Request()
        request.read = reader.read
        request.write = writer.awrite
        request.close = writer.aclose

        request.method, request.url, version = items

        try:
            try:
                if version not in ("HTTP/1.0", "HTTP/1.1"):
                    raise HttpError(request, 505, "Version Not Supported")

                while True:
                    items = await reader.readline()
                    items = items.decode('ascii').split(":", 1)

                    if len(items) == 2:
                        header, value = items
                        value = value.strip()

                        if header in self.extract_headers:
                            request.headers[header] = value
                    elif len(items) == 1:
                        break

                if self.callback_request:
                    self.callback_request(request)

                if request.url in self.routes:
                    # 1. If current url exists in routes
                    request.route = request.url
                    await self.generate_output(request,
                                               self.routes[request.url])
                else:
                    # 2. Search url in routes with wildcard
                    for route, handler in self.routes.items():
                        if route == request.url \
                            or (route[-1] == '*' and
                                request.url.startswith(route[:-1])):
                            request.route = route
                            await self.generate_output(request, handler)
                            break
                    else:
                        # 3. Try to load index file
                        if request.url in ('', '/'):
                            await send_file(request, self.INDEX_FILE)
                        else:
                            # 4. Current url have an assets extension ?
                            for extension in self.assets_extensions:
                                if request.url.endswith('.' + extension):
                                    await send_file(
                                        request,
                                        '%s/%s' % (
                                            self.STATIC_DIR,
                                            request.url,
                                        ),
                                        binary=True,
                                    )
                                    break
                            else:
                                raise HttpError(request, 404, "File Not Found")
            except HttpError as e:
                request, code, message = e.args
                await self.callback_error(request, code, message)
        except OSError as e:
            # Skip ECONNRESET error (client abort request)
            if e.args[0] != uerrno.ECONNRESET:
                raise
        finally:
            await writer.aclose()

    async def run(self):
        return await asyncio.start_server(self.handle, self.address, self.port)
    

async def send_file(request, filename, segment=64, binary=False):
    try:
        with open(filename, 'rb' if binary else 'r') as f:
            while True:
                data = f.read(segment)
                if not data:
                    break
                await request.write(data)
    except OSError as e:
        if e.args[0] != uerrno.ENOENT:
            raise
        raise HttpError(request, 404, "File Not Found")


from ubinascii import a2b_base64 as base64_decode

def authenticate(credentials):
    async def fail(request):
        await request.write("HTTP/1.1 401 Unauthorized\r\n")
        await request.write('WWW-Authenticate: Basic realm="Restricted"\r\n\r\n')
        await request.write("<h1>Unauthorized</h1>")

    def decorator(func):
        async def wrapper(request):
            header = request.headers.get('Authorization', None)
            if header is None:
                return await fail(request)

            # Authorization: Basic XXX
            kind, authorization = header.strip().split(' ', 1)
            if kind != "Basic":
                return await fail(request)

            authorization = base64_decode(authorization.strip()) \
                .decode('ascii') \
                .split(':')

            if list(credentials) != list(authorization):
                return await fail(request)

            return await func(request)
        return wrapper
    return decorator