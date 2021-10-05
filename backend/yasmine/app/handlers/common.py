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
import os

from tornado.template import Loader

from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.settings import TEMPLATES_DIR


class HomeHandler(BaseHandler):

    SUPPORTED_METHODS = ['POST', 'GET']

    def get(self):
        self.render("index.html")


class HelpHandler(AsyncThreadMixin, BaseHandler):

    SUPPORTED_METHODS = ['POST', 'GET']

    def async_get(self, key, *_, **__):
        loader = Loader(os.path.join(TEMPLATES_DIR, 'help'))
        return {'key': key, 'content': loader.load("%s.html" % key).generate().decode("utf-8")}
