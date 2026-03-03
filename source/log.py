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

### initialized by config
ENABLE_ERROR_LOGGING = False
LOG_FILE_PATH = None
###

DEFAULT_LOG_PATH = './log.dat'

def log(msg, severity = 'Error'):
    if not ENABLE_ERROR_LOGGING:
        print(msg)
    else:
        with open(LOG_FILE_PATH or DEFAULT_LOG_PATH, 'a+') as error_log:
            error_log.write(f'{severity}: "{msg}"')

def clear_log():
    error_log = open(LOG_FILE_PATH or DEFAULT_LOG_PATH, 'w')
    error_log.close()