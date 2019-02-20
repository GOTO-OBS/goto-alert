#!/usr/bin/env python
"""GOTO-alert module parameters."""

import os
import sys

import configobj

import pkg_resources

import validate

from .version import __version__


# Load configspec file for default configuration
if os.path.exists('gotoalert/data/configspec.ini'):
    # We are running in install dir, during installation
    CONFIGSPEC_FILE = 'gotoalert/data/configspec.ini'
else:
    # We are being imported, find pkg_resources
    CONFIGSPEC_FILE = pkg_resources.resource_filename('gotoalert', 'data/configspec.ini')

# Try to find .gotoalert.conf file, look in the home directory and
# anywhere specified by GOTOALERT_CONF environment variable
paths = [os.path.expanduser("~")]
if "GOTOALERT_CONF" in os.environ:
    GOTOALERT_CONF_PATH = os.environ["GOTOALERT_CONF"]
    paths.append(GOTOALERT_CONF_PATH)
else:
    GOTOALERT_CONF_PATH = None

# Load the config file as a ConfigObj
config = configobj.ConfigObj({}, configspec=CONFIGSPEC_FILE)
CONFIG_FILE_PATH = None
for loc in paths:
    try:
        with open(os.path.join(loc, ".gotoalert.conf")) as source:
            config = configobj.ConfigObj(source, configspec=CONFIGSPEC_FILE)
            CONFIG_FILE_PATH = loc
    except IOError:
        pass

# Validate ConfigObj, filling defaults from configspec if missing from config file
validator = validate.Validator()
result = config.validate(validator)
if result is not True:
    print('Config file validation failed')
    print([k for k in result if not result[k]])
    sys.exit(1)

############################################################
# Module parameters
VERSION = __version__

# HTML webpage path
HTML_PATH = config['HTML_PATH']

# Filter parameters
IGNORE_ROLES = config['IGNORE_ROLES']
MIN_GALACTIC_LATITUDE = config['MIN_GALACTIC_LATITUDE']
MIN_GALACTIC_DISTANCE = config['MIN_GALACTIC_DISTANCE']

# Database parameters
ON_GRID = config['ON_GRID']
GRID_FOV = config['GRID_FOV']
GRID_OVERLAP = config['GRID_OVERLAP']
MIN_TILE_PROB = config['MIN_TILE_PROB']
MAX_TILES = config['MAX_TILES']
VALID_DAYS = config['VALID_DAYS']