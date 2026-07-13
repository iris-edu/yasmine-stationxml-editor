# ****************************************************************************
#
# This file is part of the yasmine editing tool.
#
# yasmine (Yet Another Station Metadata INformation Editor), a tool to
# create and edit station metadata information in FDSN stationXML format,
# is a common development of IRIS and RESIF.
#
# NRLv2 online support (2026): ASGSR, Alexey Emanov.
#
# ****************************************************************************/

import io
import re
import sys
from random import random

from yasmine.app.handlers.base import AsyncThreadMixin, BaseHandler
from yasmine.app.helpers.nrl.nrlv2_online import Nrlv2OnlineHelper, Nrlv2OnlineError
from yasmine.app.helpers.utils.utils import ChannelUtils
from yasmine.app.settings import MEDIA_ROOT
from yasmine.app.utils.response_plot import polynomial_or_polezero_response, detect_plot_output

_RE_STRIP_FILE_LINE = re.compile(r'^.+?\.py:\d+:?\s*')


def _get_nrlv2_helper(application):
    """Get Nrlv2OnlineHelper if NRLv2 online is enabled."""
    cfg = application.config
    if not cfg.get('nrlv2', 'nrlv2_online_enabled'):
        return None, 'NRLV2_DISABLED'
    base_url = cfg.get('nrlv2', 'nrlv2_base_url') or ''
    if not base_url:
        return None, 'NRLV2_BAD_REQUEST'
    try:
        return Nrlv2OnlineHelper(base_url=base_url), None
    except Nrlv2OnlineError as e:
        return None, e.code


class Nrlv2HealthHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/nrlv2/health - Test NRLv2 service availability.
    Optional ?url= param overrides config URL for testing before save."""

    def async_get(self, *_, **__):
        url_override = self.get_argument('url', None)
        if url_override:
            try:
                helper = Nrlv2OnlineHelper(base_url=url_override)
            except Nrlv2OnlineError as e:
                return {'success': False, 'errorCode': e.code, 'message': e.message}
        else:
            helper, err = _get_nrlv2_helper(self.application)
            if err:
                return {'success': False, 'errorCode': err, 'message': err}
        try:
            helper.catalog(level='element')
            return {'success': True, 'message': 'OK'}
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}


class Nrlv2CatalogHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/nrlv2/catalog - Proxy to NRLv2 catalog."""

    def async_get(self, *_, **__):
        helper, err = _get_nrlv2_helper(self.application)
        if err:
            return {'success': False, 'errorCode': err, 'message': err}
        element = self.get_argument('element', None)
        manufacturer = self.get_argument('manufacturer', None)
        model = self.get_argument('model', None)
        level = self.get_argument('level', 'configuration')
        updatedsince = self.get_argument('updatedsince', None)
        try:
            data = helper.catalog(
                element=element,
                manufacturer=manufacturer,
                model=model,
                level=level,
                updatedsince=updatedsince
            )
            return {'success': True, 'data': data}
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}


class Nrlv2CombineHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/nrlv2/combine - Proxy to NRLv2 combine (returns XML/RESP)."""

    def async_get(self, *_, **__):
        helper, err = _get_nrlv2_helper(self.application)
        if err:
            return {'success': False, 'errorCode': err, 'message': err}
        instconfig = self.get_argument('instconfig', None)
        if not instconfig:
            return {'success': False, 'errorCode': 'NRLV2_BAD_REQUEST', 'message': 'instconfig required'}
        fmt = self.get_argument('format', 'stationxml-resp')
        source = self.get_argument('source', None)
        try:
            content = helper.combine(
                instconfig=instconfig,
                fmt=fmt,
                net=self.get_argument('net', None),
                sta=self.get_argument('sta', None),
                loc=self.get_argument('loc', None),
                cha=self.get_argument('cha', None),
                starttime=self.get_argument('starttime', None),
                endtime=self.get_argument('endtime', None),
                source=source,
            )
            self.set_header('Content-Type', 'application/xml' if 'xml' in fmt else 'text/plain')
            return content
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}


class Nrlv2SensorsHandler(AsyncThreadMixin, BaseHandler):
    """GET/POST /api/nrlv2/sensors/ or /api/nrlv2/sensors/path - Tree for sensors (lazy)."""

    def _handle_request(self, path=''):
        helper, err = _get_nrlv2_helper(self.application)
        if err:
            return {'success': False, 'errorCode': err, 'message': err}
        path = (path or self.get_argument('node', '') or '').strip('/')
        if path in ('0', '', 'root'):
            path = None
        try:
            tree = helper.get_sensors_keys(path=path or None)
            return {'data': tree}
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}

    def async_get(self, path='', **__):
        return self._handle_request(path)

    def async_post(self, path='', **__):
        return self._handle_request(path)


class Nrlv2SensorConfigsHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/nrlv2/sensor/configurations/?manufacturer=X&model=Y - Configurations with parameters for modifier UI."""

    def async_get(self, *_, **__):
        helper, err = _get_nrlv2_helper(self.application)
        if err:
            return {'success': False, 'errorCode': err, 'message': err}
        manufacturer = self.get_argument('manufacturer', None)
        model = self.get_argument('model', None)
        if not manufacturer or not model:
            return {'success': False, 'errorCode': 'NRLV2_BAD_REQUEST', 'message': 'manufacturer and model required'}
        try:
            data = helper.get_sensor_configurations(manufacturer, model)
            return {'success': True, 'data': data}
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}


class Nrlv2SensorRespHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/nrlv2/sensor/response/?instconfig= - Sensor response text."""

    def async_get(self, *_, **__):
        helper, err = _get_nrlv2_helper(self.application)
        if err:
            return {'success': False, 'errorCode': err, 'message': err}
        instconfig = self.get_argument('instconfig', None)
        if not instconfig:
            return {'success': False, 'errorCode': 'NRLV2_BAD_REQUEST', 'message': 'instconfig required'}
        source = self.get_argument('source', None)
        try:
            text = helper.get_sensor_response_str(instconfig, source=source)
            self.set_header('Content-Type', 'text/plain')
            return text
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}


class Nrlv2DataloggersHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/nrlv2/dataloggers/ or /api/nrlv2/dataloggers/path - Tree for dataloggers (lazy)."""

    def async_get(self, path='', **__):
        helper, err = _get_nrlv2_helper(self.application)
        if err:
            return {'success': False, 'errorCode': err, 'message': err}
        path = (path or self.get_argument('node', '') or '').strip('/')
        if path in ('0', '', 'root'):
            path = None
        try:
            tree = helper.get_dataloggers_keys(path=path or None)
            return {'data': tree}
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}


class Nrlv2DataloggerConfigsHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/nrlv2/datalogger/configurations/?manufacturer=X&model=Y - Configurations with parameters for modifier UI."""

    def async_get(self, *_, **__):
        helper, err = _get_nrlv2_helper(self.application)
        if err:
            return {'success': False, 'errorCode': err, 'message': err}
        manufacturer = self.get_argument('manufacturer', None)
        model = self.get_argument('model', None)
        if not manufacturer or not model:
            return {'success': False, 'errorCode': 'NRLV2_BAD_REQUEST', 'message': 'manufacturer and model required'}
        try:
            data = helper.get_datalogger_configurations(manufacturer, model)
            return {'success': True, 'data': data}
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}


class Nrlv2DataloggerRespHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/nrlv2/datalogger/response/?instconfig= - Datalogger response text."""

    def async_get(self, *_, **__):
        helper, err = _get_nrlv2_helper(self.application)
        if err:
            return {'success': False, 'errorCode': err, 'message': err}
        instconfig = self.get_argument('instconfig', None)
        if not instconfig:
            return {'success': False, 'errorCode': 'NRLV2_BAD_REQUEST', 'message': 'instconfig required'}
        source = self.get_argument('source', None)
        try:
            text = helper.get_datalogger_response_str(instconfig, source=source)
            self.set_header('Content-Type', 'text/plain')
            return text
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}


class Nrlv2ChannelRespHandler(AsyncThreadMixin, BaseHandler):
    """GET /api/nrlv2/channel/response/preview/ - Response preview and plot for instconfig."""

    def async_get(self, *_, **__):
        helper, err = _get_nrlv2_helper(self.application)
        if err:
            return {'success': False, 'errorCode': err, 'message': err}
        instconfig = self.get_argument('instconfig', None)
        if not instconfig:
            return {'success': False, 'errorCode': 'NRLV2_BAD_REQUEST', 'message': 'instconfig required'}
        source = self.get_argument('source', None)
        min_fq = self.get_argument('min', None)
        max_fq = self.get_argument('max', None)
        try:
            response = helper.get_channel_response_obj(instconfig, source=source)
            response_str = polynomial_or_polezero_response(response)
        except Nrlv2OnlineError as e:
            return {'success': False, 'errorCode': e.code, 'message': e.message}
        except Exception as e:
            return {'success': False, 'message': f'Cannot build channel response.<br> {e}'}
        stderr_capture = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = stderr_capture
        try:
            plot_folder = MEDIA_ROOT + '/plots'
            file_name = instconfig.replace('/', '_').replace(':', '_')
            plot_file = ChannelUtils.create_response_plot(
                response,
                plot_folder,
                file_name,
                float(min_fq) if min_fq else None,
                float(max_fq) if max_fq else None,
                instconfig=instconfig,
            )
            csv_file = ChannelUtils.create_response_csv(
                response,
                plot_folder,
                file_name,
                float(min_fq) if min_fq else None,
                float(max_fq) if max_fq else None,
                instconfig=instconfig,
            )
            plot_output = detect_plot_output(response, instconfig)
            return {
                'success': True,
                'text': response_str,
                'plot_output': plot_output,
                'plot_url': f'/api/channel/response/plots/plots/{plot_file}?_dc={random()}',
                'csv_url': f'/api/channel/response/plots/plots/{csv_file}?_dc={random()}'
            }
        except Exception as err:
            err_str = str(err).lower()
            if 'units mismatch' in err_str or 'check_channel' in err_str or 'illegal resp format' in err_str:
                msg = (
                    'Cannot generate plot: units mismatch between sensor and datalogger stages. '
                    'This may indicate an incompatible combination. '
                    'The response data is available and can still be added.'
                )
            else:
                err_str = _RE_STRIP_FILE_LINE.sub('', str(err)).strip() or str(err)
                stderr_output = stderr_capture.getvalue()
                lines = [f'Cannot generate plot. {err_str}']
                if stderr_output:
                    for line in stderr_output.strip().split('\n'):
                        s = _RE_STRIP_FILE_LINE.sub('', line.strip()).strip()
                        if s and any(kw in s for kw in (
                            'EVRESP', 'units mismatch', 'sampling rate', 'UserWarning',
                            'inconsistent', 'check_channel', 'skipping'
                        )):
                            lines.append(s)
                msg = '\n'.join(lines)
            return {'success': True, 'text': response_str, 'message': msg, 'plot_failed': True}
        finally:
            sys.stderr = old_stderr
