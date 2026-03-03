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

from configparser import ConfigParser

import argparse

def parse_config():
    parser = argparse.ArgumentParser(prog='therminator',
                                    description='Thermostat emulator')
    parser.add_argument('cfg', nargs = '?', default = 'config.ini', help = 'Specify an optional config file.')
    args = parser.parse_args()

    configfile = ConfigParser()
    configfile.read(args.configfilename)

    import source.log as log
    log.ENABLE_ERROR_LOGGING = configfile.getboolean('debug', 'enable_logging')
    log.LOG_FILE_PATH = configfile['debug']['log_file_path']

    import source.board as board
    # 5V relay uses 2-5Vin boost from 2-3xAA batteries, has enable pin that hard shuts off on low->ground
    board.PIN_5V_EXTERNAL_PWR_ENABLE = int(configfile['board']['PIN_5V_EXTERNAL_PWR_ENABLE'])

    # optocoupler 4 channel >27V AC relay triggered with 3.3V
    board.PIN_RELAY_SWITCH_0 = int(configfile['board']['PIN_RELAY_SWITCH_0'])
    board.PIN_RELAY_SWITCH_1 = int(configfile['board']['PIN_RELAY_SWITCH_1'])
    board.PIN_RELAY_SWITCH_2 = int(configfile['board']['PIN_RELAY_SWITCH_2'])
    board.PIN_RELAY_SWITCH_3 = int(configfile['board']['PIN_RELAY_SWITCH_3'])

    import source.access_point as access_point
    access_point.DEFAULT_SOFT_AP_SSID = configfile['access']['access_point_name']
    access_point.DEFAULT_SOFT_AP_KEY = configfile['access']['access_point_key']
    access_point.ENABLE_WATCHDOG = configfile.getboolean('access', 'enable_watchdog')
    
    import source.http_page as http_page
    http_page.WEB_ASSETS_DIR = configfile['webserver']['assets_directory']
    http_page.STORED_LOGS_DIR = configfile['webserver']['logs_directory']
    http_page.ENABLE_WATCHDOG = configfile.getboolean('webserver', 'enable_watchdog')
    http_page.API_CREDENTIALS = (configfile['api']['api_user'],
                                   configfile['api']['api_key'])