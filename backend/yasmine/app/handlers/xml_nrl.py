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
# 2026-09-24, version 4.3.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory


class LibraryHandler(BaseHandler):
    def __init__(self, *_, **__):
        self.helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
        super(LibraryHandler, self).__init__(*_, **__)


class XmlSensorsHandler(AsyncThreadMixin, LibraryHandler):
    def async_get(self, *_, **__):
        return self.helper.get_sensors_keys()


class XmlDataloggersHandler(AsyncThreadMixin, LibraryHandler):
    def async_get(self, *_, **__):
        return self.helper.get_dataloggers_keys()


class XmlDataloggerRespHandler(AsyncThreadMixin, LibraryHandler):
    def async_get(self, *_, **__):
        return self.helper.get_datalogger_response_str(self.get_arguments('keys'))


class XmlSensorRespHandler(AsyncThreadMixin, LibraryHandler):
    def async_get(self, *_, **__):
        return self.helper.get_sensor_response_str(self.get_arguments('keys'))


class XmlChannelRespHandler(AsyncThreadMixin, LibraryHandler):
    def async_get(self, *_, **__):
        return self.helper.get_sensor_response_and_plot(
            self.get_arguments('sensorKeys'),
            self.get_arguments('dataloggerKeys'),
            self.get_argument('min'),
            self.get_argument('max'),
            start_stage=self.get_argument('start_stage', None),
            end_stage=self.get_argument('end_stage', None),
        )


class XmlElementKeysHandler(AsyncThreadMixin, LibraryHandler):
    """GET /api/nrl/integrated/ or /api/nrl/soh/ — offline RESP tree."""

    def async_get(self, element, **__):
        return self.helper.get_element_keys(element)


class XmlElementRespHandler(AsyncThreadMixin, LibraryHandler):
    """GET /api/nrl/<element>/response/?keys= — RESP text for one instrument."""

    def async_get(self, element, **__):
        return self.helper.get_element_response_str(element, self.get_arguments('keys'))


class XmlElementPreviewHandler(AsyncThreadMixin, LibraryHandler):
    """GET /api/nrl/<element>/response/preview/ — plot for one RESP file."""

    def async_get(self, element, **__):
        return self.helper.get_element_response_and_plot(
            element,
            self.get_arguments('keys'),
            self.get_argument('min', None),
            self.get_argument('max', None),
            start_stage=self.get_argument('start_stage', None),
            end_stage=self.get_argument('end_stage', None),
        )
