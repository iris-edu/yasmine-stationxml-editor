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
# NRLv2 online support (2026): ASGSR, Alexey Emanov.
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
# 2026-09-26, version 4.4.0-beta: ASGSR, Alexey Emanov
#
# ****************************************************************************/


# -*- coding: utf-8 -*-

from datetime import timedelta
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
from yasmine.app.handlers import common, config, wizard, helper, stationxml_help, xml_ial, xml, user_library
from yasmine.app.handlers import xml_bldr, xml_list, xml_nrl, xml_nrlv2
from yasmine.app.handlers.base import ErrorHandler
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.settings import TORNADO_SETTINGS, TORNADO_PORT, TORNADO_HOST, LOGGING_CONFIG, LOGIING_CONSOLE_CONFIG, \
    NRL_CRON, MEDIA_ROOT, STATIONXML_UPLOAD_MAX_BYTES
from yasmine.app.utils.facade import ProcessMixin
import warnings

# ObsPy warns when response has multiple PolesZerosResponseStage (uses first).
# NRLv2/StationXML can have multiple; behavior is correct, suppress noise.
warnings.filterwarnings(
    'ignore',
    message='More than one PolesZerosResponseStage encountered',
    category=UserWarning
)

logger = logging.getLogger("tornado.application")
app_logger = logging.getLogger(__name__)


class Application(tornado.web.Application, ProcessMixin):

    def __init__(self, debug=False, enable_scheduler=True):
        TORNADO_SETTINGS['debug'] = debug
        TORNADO_SETTINGS['transforms'] = [tornado.web.GZipContentEncoding]
        if debug:
            LOGIING_CONSOLE_CONFIG['level'] = logging.DEBUG
        dictConfig(LOGGING_CONFIG)

        tornado.web.Application.__init__(self, [
            (r"/", common.HomeHandler),
            (r"/healthz/?", common.HealthHandler),
            (r"/api/build/?", common.BuildInfoHandler),

            (r"/api/user-library/ie/(?P<db_id>[\d\_]+)?", user_library.ImpExpHandler),
            (r"/api/user-library/(?P<db_id>[\d\_]+)?/*", user_library.GridHandler),
            (r"/api/user-library/node/", user_library.NodeHandler),
            (r"/api/user-library/node/(?P<library_id>[\d\_]+)/(?P<node_type>[\d\_]+)/(?P<node_inst_id>[\d\_]+)?",
             user_library.NodeHandler),
            (r"/api/user-library/extensions/(?P<library_id>[\d\_]+)/(?P<node_id>[\d\_]+)/?",
             user_library.ExtensionsHandler),

            (r"/api/xml/map/(?P<xml_id>[\d\_]+)/?", xml_bldr.XmlMapHandler),
            (r"/api/map/tiles/(?P<source>osm|opentopomap)/(?P<z>\d+)/(?P<x>\d+)/(?P<y>\d+)",
             xml_bldr.MapTileHandler),
            (r"/api/xml/(?P<db_id>[\d\_]+)?/*", xml_list.XmlGridHandler),
            (r"/api/xml/ie/(?P<db_id>[\d\_]+)?", xml_list.XmlImpExpHandler),

            (r"/api/xml/similar-channel/", xml_bldr.XmlSimilarChannelHandler),
            (r"/api/xml/node-path/", xml_bldr.XmlNodePathHandler),

            (r"/api/xml/validate-strict/job/(?P<job_id>[0-9a-fA-F]+)/",
             xml_bldr.XmlStrictValidationProgressHandler),
            (r"/api/xml/validate-strict/(?P<xml_id>[\d\_]+)?/", xml_bldr.XmlStrictValidationHandler),
            (r"/api/xml/validate/(?P<xml_id>[\d\_]+)?/", xml_bldr.XmlValidationHandler),
            (r"/api/xml/tree/(?P<xml_id>[\d\_]+)/(?P<node_id>[\d\_]+)?", xml_bldr.XmlNodeHandler),
            (r"/api/xml/extensions/(?P<xml_id>[\d\_]+)/(?P<node_id>[\d\_]+)/?",
             xml_bldr.XmlNodeExtensionsHandler),
            (r"/api/xml/attr/(?P<db_id>[\d\_]+)?", xml_bldr.XmlNodeAttrHandler),
            (r"/api/xml/attr/available/(?P<node_id>[\d\_]+)/?", xml_bldr.XmlNodeAvailableAttrHandler),
            (r"/api/xml/attr/validate/", xml_bldr.XmlNodeAttrValidateHandler),
            (r"/api/xml/epoch/(?P<xml_id>[\d\_]+)/*", xml_bldr.XmlEpochHandler),

            (r"/api/nrl/sensors/(?P<key>[^/]+)?", xml_nrl.XmlSensorsHandler),
            (r"/api/nrl/sensor/response/", xml_nrl.XmlSensorRespHandler),
            (r"/api/nrl/dataloggers/(?P<key>[^/]+)?", xml_nrl.XmlDataloggersHandler),
            (r"/api/nrl/datalogger/response/", xml_nrl.XmlDataloggerRespHandler),
            (r"/api/nrl/channel/response/preview/", xml_nrl.XmlChannelRespHandler),
            (r"/api/nrl/(?P<element>integrated|soh)/response/preview/", xml_nrl.XmlElementPreviewHandler),
            (r"/api/nrl/(?P<element>integrated|soh)/response/", xml_nrl.XmlElementRespHandler),
            (r"/api/nrl/(?P<element>integrated|soh)/(?P<key>[^/]+)?", xml_nrl.XmlElementKeysHandler),

            (r"/api/nrlv2/health", xml_nrlv2.Nrlv2HealthHandler),
            (r"/api/nrlv2/catalog", xml_nrlv2.Nrlv2CatalogHandler),
            (r"/api/nrlv2/combine", xml_nrlv2.Nrlv2CombineHandler),
            (r"/api/nrlv2/sensor/configurations/?", xml_nrlv2.Nrlv2SensorConfigsHandler),
            (r"/api/nrlv2/sensor/response/", xml_nrlv2.Nrlv2SensorRespHandler),
            (r"/api/nrlv2/sensors/(?P<path>.*)", xml_nrlv2.Nrlv2SensorsHandler),
            (r"/api/nrlv2/datalogger/configurations/?", xml_nrlv2.Nrlv2DataloggerConfigsHandler),
            (r"/api/nrlv2/dataloggers/(?P<path>.*)", xml_nrlv2.Nrlv2DataloggersHandler),
            (r"/api/nrlv2/datalogger/response/", xml_nrlv2.Nrlv2DataloggerRespHandler),
            (r"/api/nrlv2/channel/response/preview/", xml_nrlv2.Nrlv2ChannelRespHandler),
            (r"/api/nrlv2/(?P<element>integrated|soh)/configurations/?", xml_nrlv2.Nrlv2ElementConfigsHandler),
            (r"/api/nrlv2/(?P<element>integrated|soh)/response/", xml_nrlv2.Nrlv2ElementRespHandler),
            (r"/api/nrlv2/(?P<element>integrated|soh)/(?P<path>.*)", xml_nrlv2.Nrlv2ElementTreeHandler),

            (r"/api/arol/sensor/key/", xml_ial.XmlSensorKeyHandler),
            (r"/api/arol/sensor/response/", xml_ial.XmlSensorRespHandler),
            (r"/api/arol/datalogger/key/", xml_ial.XmlDataloggerKeyHandler),
            (r"/api/arol/datalogger/response/", xml_ial.XmlDataloggerRespHandler),
            (r"/api/arol/channel/response/preview/", xml_ial.XmlChannelRespHandler),

            (r"/api/diff/(.*)", tornado.web.StaticFileHandler, {'path': os.path.join(MEDIA_ROOT, 'diffs')}),
            (r"/api/channel/response/plots/(.*)", tornado.web.StaticFileHandler, {'path': MEDIA_ROOT}),
            (r"/api/channel/response/plot-url/(?P<instance_node_id>[\d\_]+)?", xml.XmlChannelResponsePlotHandler),
            (r"/api/channel/response-difference/plot-url/", xml.XmlChannelResponseDifferencePlotHandler),
            (r"/api/channel/response/schema/?", xml.XmlChannelResponseSchemaHandler),
            (r"/api/channel/response/validate/?", xml.XmlChannelResponseValidateHandler),
            (r"/api/channel/response/xml/(?P<response_attr_id>[\d\_]+)?", xml.XmlChannelResponseXmlHandler),
            (r"/api/channel/response/recalculate-sensitivity/", xml.XmlChannelResponseRecalculateSensitivityHandler),
            (r"/api/channel/response/recalculate-sensitivity-options/", xml.XmlChannelResponseRecalculateSensitivityOptionsHandler),
            (r"/api/channel/response/import-resp/", xml.XmlChannelResponseImportRespHandler),

            (r"/api/wizard/network/*", wizard.CreateNetworkHandler),
            (r"/api/wizard/station/(?P<network_node_id>[\d\_]+)?/*", wizard.CreateStationHandler),
            (r"/api/wizard/channel/(?P<station_node_id>[\d\_]+)?/*", wizard.CreateChannelHandler),
            (r"/api/wizard/new-channel/*", wizard.CreateChannelHandler),
            (r"/api/wizard/guess/code/", wizard.CreateGuessCodeHandler),
            (r"/api/wizard/guess/soh-code/", wizard.GuessSohCodeHandler),
            (r"/api/wizard/guess/prefix/", wizard.GuessChannelPrefixHandler),

            (r"/api/stationxml/help/1.2/?", stationxml_help.StationXmlHelpHandler),
            (r"/api/help/(?P<key>[\w\_]+)?/*", common.HelpHandler, None, 'HelpHandler'),

            (r"/api/cfg/(?P<db_id>[\d\_]+)?/*", config.ConfigHandler),
            (r"/api/attr/(?P<node_id>[\d\_]+)?/*", config.AttributeHandler),

            (r"/api/helper/(?P<node_id>[\d\_]+)/(?P<attr_id>[\d\_]+)?", helper.HelperHandler),
            (r"/api/helper/url-user-library/", helper.ImportUrlUserLibraryHandler),
            (r"/api/helper/zip-user-library/(?P<db_id>[\d\_]+)?", helper.ImportZipUserLibraryHandler),
        ], default_handler_class=ErrorHandler, **TORNADO_SETTINGS)

        self.scheduler = None
        if enable_scheduler:
            self.scheduler = TornadoScheduler()
            self.scheduler.start()
            trigger = OrTrigger([
                DateTrigger(run_date=datetime.now() + timedelta(seconds=10)),
                CronTrigger(**NRL_CRON)
            ])
            self.nrl_sync_job = self.scheduler.add_job(self.sync_nrl, trigger)
            self.ial_sync_job = self.scheduler.add_job(self.sync_ial, trigger)

        ProcessMixin.__init__(self)

    def _run_sync_job(self, func):
        try:
            tornado.ioloop.IOLoop.current().run_in_executor(None, func)
        except RuntimeError:
            func()

    def sync_nrl(self):
        self._run_sync_job(self._sync_nrl_blocking)

    def _sync_nrl_blocking(self):
        if not self.config.get('nrl', 'nrl_enabled'):
            app_logger.info('NRL sync skipped')
            return
        self.sync_nrl_started = True
        try:
            library_helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRL)
            if library_helper.sync():
                app_logger.info('NRL sync finished')
            else:
                self.sync_nrl_started = False
                app_logger.info('NRL sync failed')
        except Exception:
            self.sync_nrl_started = False
            app_logger.exception(
                'NRL archive download/update failed'
            )
            app_logger.info('NRL sync failed')

    def sync_ial(self):
        self._run_sync_job(self._sync_ial_blocking)

    def _sync_ial_blocking(self):
        self.sync_ial_started = True
        try:
            library_helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.AROL)
            library_helper.sync()
            app_logger.info('AROL sync finished')
        except Exception:
            self.sync_ial_started = False
            app_logger.exception('AROL library sync failed')
            app_logger.info('AROL sync failed')


def runserver(debug, host=TORNADO_HOST, port=TORNADO_PORT):
    app = Application(debug)
    app.listen(
        port=port,
        address=host,
        max_body_size=STATIONXML_UPLOAD_MAX_BYTES,
        max_buffer_size=STATIONXML_UPLOAD_MAX_BYTES,
    )
    shown_host = host or '0.0.0.0'
    app_logger.info(
        'HTTP listening on %s:%s; the interface can be opened',
        shown_host,
        port,
    )
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
