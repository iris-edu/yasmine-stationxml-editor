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

from _datetime import timedelta
from datetime import datetime
from logging.config import dictConfig
import logging
import os

from apscheduler.schedulers.tornado import TornadoScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
import tornado.web
from apscheduler.triggers.interval import IntervalTrigger

from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.handlers import common, config, wizard, helper, xml_ial, xml, user_library
from yasmine.app.handlers import xml_bldr, xml_list, xml_nrl
from yasmine.app.handlers.base import ErrorHandler
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.settings import TORNADO_SETTINGS, TORNADO_PORT, TORNADO_HOST, LOGGING_CONFIG, LOGIING_CONSOLE_CONFIG, \
    NRL_CRON, MEDIA_ROOT
from yasmine.app.utils.facade import ProcessMixin

logger = logging.getLogger("tornado.application")


class Application(tornado.web.Application, ProcessMixin):

    def __init__(self, debug=False):
        TORNADO_SETTINGS['debug'] = debug
        if debug:
            LOGIING_CONSOLE_CONFIG['level'] = logging.DEBUG
        dictConfig(LOGGING_CONFIG)

        tornado.web.Application.__init__(self, [
            (r"/", common.HomeHandler),

            (r"/api/user-library/(?P<db_id>[\d\_]+)?/*", user_library.GridHandler),
            (r"/api/user-library/node/", user_library.NodeHandler),
            (r"/api/user-library/node/(?P<library_id>[\d\_]+)/(?P<node_type>[\d\_]+)/(?P<node_inst_id>[\d\_]+)?",
             user_library.NodeHandler),

            (r"/api/xml/(?P<db_id>[\d\_]+)?/*", xml_list.XmlGridHandler),
            (r"/api/xml/ie/(?P<db_id>[\d\_]+)?", xml_list.XmlImpExpHandler),

            (r"/api/xml/similar-channel/", xml_bldr.XmlSimilarChannelHandler),
            (r"/api/xml/node-path/", xml_bldr.XmlNodePathHandler),

            (r"/api/xml/validate/(?P<xml_id>[\d\_]+)?/", xml_bldr.XmlValidationHandler),
            (r"/api/xml/tree/(?P<xml_id>[\d\_]+)/(?P<node_id>[\d\_]+)?", xml_bldr.XmlNodeHandler),
            (r"/api/xml/attr/(?P<db_id>[\d\_]+)?", xml_bldr.XmlNodeAttrHandler),
            (r"/api/xml/attr/available/(?P<node_id>[\d\_]+)/?", xml_bldr.XmlNodeAvailableAttrHandler),
            (r"/api/xml/attr/validate/", xml_bldr.XmlNodeAttrValidateHandler),
            (r"/api/xml/epoch/(?P<xml_id>[\d\_]+)/*", xml_bldr.XmlEpochHandler),

            (r"/api/nrl/sensors/(?P<key>[^/]+)?", xml_nrl.XmlSensorsHandler),
            (r"/api/nrl/sensor/response/", xml_nrl.XmlSensorRespHandler),
            (r"/api/nrl/dataloggers/(?P<key>[^/]+)?", xml_nrl.XmlDataloggersHandler),
            (r"/api/nrl/datalogger/response/", xml_nrl.XmlDataloggerRespHandler),
            (r"/api/nrl/channel/response/preview/", xml_nrl.XmlChannelRespHandler),

            (r"/api/arol/sensor/key/", xml_ial.XmlSensorKeyHandler),
            (r"/api/arol/sensor/response/", xml_ial.XmlSensorRespHandler),
            (r"/api/arol/datalogger/key/", xml_ial.XmlDataloggerKeyHandler),
            (r"/api/arol/datalogger/response/", xml_ial.XmlDataloggerRespHandler),
            (r"/api/arol/channel/response/preview/", xml_ial.XmlChannelRespHandler),

            (r"/api/diff/(.*)", tornado.web.StaticFileHandler, {'path': os.path.join(MEDIA_ROOT, 'diffs')}),
            (r"/api/channel/response/plots/(.*)", tornado.web.StaticFileHandler, {'path': MEDIA_ROOT}),
            (r"/api/channel/response/plot-url/(?P<instance_node_id>[\d\_]+)?", xml.XmlChannelResponsePlotHandler),
            (r"/api/channel/response-difference/plot-url/", xml.XmlChannelResponseDifferencePlotHandler),
            (r"/api/channel/response/xml/(?P<response_attr_id>[\d\_]+)?", xml.XmlChannelResponseXmlHandler),

            (r"/api/wizard/network/*", wizard.CreateNetworkHandler),
            (r"/api/wizard/station/*", wizard.CreateStationHandler),
            (r"/api/wizard/channel/(?P<station_node_id>[\d\_]+)?/*", wizard.CreateChannelHandler),
            (r"/api/wizard/new-channel/*", wizard.CreateChannelHandler),
            (r"/api/wizard/guess/code/", wizard.CreateGuessCodeHandler),

            (r"/api/help/(?P<key>[\w\_]+)?/*", common.HelpHandler, None, 'HelpHandler'),

            (r"/api/cfg/(?P<db_id>[\d\_]+)?/*", config.ConfigHandler),
            (r"/api/attr/(?P<node_id>[\d\_]+)?/*", config.AttributeHandler),

            (r"/api/helper/(?P<node_id>[\d\_]+)/(?P<attr_id>[\d\_]+)?", helper.HelperHandler),
            (r"/api/helper/url-user-library/", helper.ImportUrlUserLibraryHandler),
            (r"/api/helper/zip-user-library/(?P<db_id>[\d\_]+)?", helper.ImportZipUserLibraryHandler),
        ], default_handler_class=ErrorHandler, **TORNADO_SETTINGS)

        self.scheduler = TornadoScheduler()
        self.scheduler.start()
        # start sync nrl job
        trigger = OrTrigger([
            IntervalTrigger(minutes=10),
            DateTrigger(run_date=datetime.now() + timedelta(seconds=10)),
            # CronTrigger(**NRL_CRON)
        ])

        self.nrl_sync_job = self.scheduler.add_job(self.sync_nrl, trigger)
        self.ial_sync_job = self.scheduler.add_job(self.sync_ial, trigger)

        ProcessMixin.__init__(self)

    def sync_nrl(self):
        self.sync_nrl_started = True
        try:
            library_helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
            library_helper.sync()
        except:  # @IgnorePep8
            self.sync_nrl_started = False

    def sync_ial(self):
        self.sync_ial_started = True
        try:
            library_helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.AROL)
            library_helper.sync()
        except:  # @IgnorePep8
            self.sync_ial_started = False


def runserver(debug, host=TORNADO_HOST, port=TORNADO_PORT):
    app = Application(debug)
    app.listen(port=port, address=host)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
