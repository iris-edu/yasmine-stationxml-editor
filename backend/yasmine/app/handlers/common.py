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
# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


# -*- coding: utf-8 -*-
import json
import os

from tornado.template import Loader
from tornado.web import HTTPError

from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.settings import TEMPLATES_DIR
from yasmine.app.utils.build_info import build_info


class HomeHandler(BaseHandler):

    SUPPORTED_METHODS = ['POST', 'GET']

    def get(self):
        info = build_info()
        self.render(
            "index.html",
            build_timestamp_json=json.dumps(info['build_timestamp']),
            commit_revision_json=json.dumps(info['commit_revision']),
        )


class HealthHandler(BaseHandler):

    def get(self):
        self.write({'success': True, 'status': 'ok'})


class BuildInfoHandler(BaseHandler):

    def get(self):
        info = build_info()
        self.write({
            'success': True,
            'data': {
                'build_timestamp': info['build_timestamp'],
                'commit_revision': info['commit_revision'],
            },
        })


class HelpHandler(AsyncThreadMixin, BaseHandler):

    SUPPORTED_METHODS = ['POST', 'GET']

    def async_get(self, key, *_, **__):
        if not key:
            raise HTTPError(404, reason='Help key is required')
        help_dir = os.path.join(TEMPLATES_DIR, 'help')
        template_name = "%s.html" % key
        if not os.path.isfile(os.path.join(help_dir, template_name)):
            raise HTTPError(404, reason="Help page '%s' not found" % key)
        loader = Loader(help_dir)
        return {'key': key, 'content': loader.load(template_name).generate().decode("utf-8")}
