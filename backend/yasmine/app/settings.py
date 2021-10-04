# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
# Development and addition of new features is shared and agreed between * IRIS and RESIF.
#
#
# Version 1.0 of the software was funded by SAGE, a major facility fully
# funded by the National Science Foundation (EAR-1261681-SAGE),
# development done by ISTI and led by IRIS Data Services.
# Version 2.0 of the software was funded by CNRS and development led by * RESIF.
#
# This program is free software; you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version. *
# This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License (GNU-LGPL) for more details. *
# You should have received a copy of the GNU Lesser General Public
# License along with this software. If not, see
# <https://www.gnu.org/licenses/>
#
#
# 2019/10/07 : version 2.0.0 initial commit
#
# ****************************************************************************/


# -*- coding: utf-8 -*-
import logging
import os
from yasmine.app.utils.op_sys import is_windows

ROOT_DIR = os.path.join(os.path.dirname(__file__), '..')

if is_windows():
    APP_DIR = os.path.join('c:', os.sep, 'YASMINE')
else:
    APP_DIR = os.path.join(os.sep, 'opt', 'YASMINE')

RUN_ROOT = os.path.join(APP_DIR, '_run')

RESOURCES_SCHEMA_AROL = os.path.join(ROOT_DIR, 'resources', 'schemas', 'arol')
RESOURCES_SCHEMA_GATITO = os.path.join(ROOT_DIR, 'resources', 'schemas', 'gatito')

TEMPLATES_DIR = os.path.join(ROOT_DIR, 'templates')

TORNADO_SETTINGS = {  # @UnusedVariable
    'debug': True,
    'autoreload': True,
    'compiled_template_cache': False,
    'static_hash_cache': False,
    'serve_traceback': True,
    'static_path': os.path.join(ROOT_DIR, 'static'),
    'template_path': TEMPLATES_DIR,
    'cookie_secret': 'AC<rz+K.t_[.]z-MH!e99SH'
}

DB_NAME = 'db.sqlite'
DB_FILE = os.path.join(RUN_ROOT, DB_NAME)
DB_CONNECTION = ('sqlite:///%s' % DB_FILE)  # @UnusedVariable

TORNADO_HOST = ''  # @UnusedVariable
TORNADO_PORT = 80  # @UnusedVariable

DATE_FORMAT_SYSTEM = '%d/%m/%Y %H:%M:%S'  # @UnusedVariable

try:
    from yasmine.settings.dev import *
except:  # @IgnorePep8
    pass

MEDIA_ROOT = os.path.join(APP_DIR, '_media')  # @UnusedVariable

LOGGING_ROOT = os.path.join(APP_DIR, '_logs')  # @UnusedVariable
TMP_ROOT = os.path.join(APP_DIR, '_tmp')  # @UnusedVariable
NRL_ROOT = os.path.join(MEDIA_ROOT, 'nrl')  # @UnusedVariable
IAL_ROOT = os.path.join(MEDIA_ROOT, 'ial')

NRL_CRON = {'hour': 23, 'minute': 0, 'second': 0}
NRL_URL = 'http://ds.iris.edu/NRL/IRIS.zip'
IAL_FOLDER = 'arol-isti_mandatory_filters'  # arol-master
IAL_URL = f'https://gitlab.com/resif/arol/-/archive/isti_mandatory_filters/arol-isti_mandatory_filters.zip'

LOGIING_CONSOLE_CONFIG = {
    'class': 'logging.StreamHandler',
    'level': logging.ERROR,
    'formatter': 'default',
    'stream': 'ext://sys.stdout'
}

LOGGING_CONFIG = dict(
    version=1,
    formatters={
        'default': {
            'format': '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
        }
    },
    handlers={
        'access_default': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': logging.ERROR,
            'formatter': 'default',
            'maxBytes': 10485760,
            'filename': os.path.join(LOGGING_ROOT, 'access.log'),
            'backupCount': 20,
            'encoding': 'utf8'
        },
        'application_default': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': logging.ERROR,
            'formatter': 'default',
            'filename': os.path.join(LOGGING_ROOT, 'application.log'),
            'maxBytes': 10485760,
            'backupCount': 20,
            'encoding': 'utf8'
        },
        'general_default': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': logging.ERROR,
            'formatter': 'default',
            'maxBytes': 10485760,
            'filename': os.path.join(LOGGING_ROOT, 'general.log'),
            'backupCount': 20,
            'encoding': 'utf8'
        },
        'console': LOGIING_CONSOLE_CONFIG
    },
    loggers={
        'tornado.access': {
            'handlers': ['access_default', 'console'],
            'level': logging.DEBUG
        },
        'tornado.application': {
            'handlers': ['application_default', 'console'],
            'level': logging.DEBUG
        },
        'tornado.general': {
            'handlers': ['general_default', 'console'],
            'level': logging.DEBUG
        }
    }
)
