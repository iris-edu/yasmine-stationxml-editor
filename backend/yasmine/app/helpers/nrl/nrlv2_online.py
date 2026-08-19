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
import logging
import re
import time
from urllib.parse import urlparse, urljoin

import requests  # type: ignore[reportMissingImports]
from obspy import read_inventory  # type: ignore[reportMissingImports]
from obspy.core.inventory.util import Equipment  # type: ignore[reportMissingImports]

from yasmine.app.helpers.base_helper import _normalize_response_units
from yasmine.app.settings import NRLV2_DEFAULT_URL

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30
MAX_RETRIES = 2
BACKOFF_FACTOR = 1.0

# SSRF: block private/local addresses
BLOCKED_HOSTS = re.compile(
    r'^(localhost|127\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|'
    r'::1|fe80:|169\.254\.)',
    re.IGNORECASE
)


class Nrlv2OnlineError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def _validate_url(base_url):
    """SSRF protection: only allow http/https to non-private hosts."""
    if not base_url or not isinstance(base_url, str):
        raise Nrlv2OnlineError('NRLV2_BAD_REQUEST', 'Invalid URL')
    base_url = base_url.strip().rstrip('/')
    parsed = urlparse(base_url)
    if parsed.scheme not in ('http', 'https'):
        raise Nrlv2OnlineError('NRLV2_BAD_REQUEST', 'Only http/https allowed')
    host = (parsed.hostname or '').lower()
    if BLOCKED_HOSTS.match(host):
        raise Nrlv2OnlineError('NRLV2_BAD_REQUEST', 'Private/local URLs not allowed')


def _parse_instconfig_equipment(instconfig):
    """Extract manufacturer and model from instconfig for Equipment."""
    # Format: sensor_Manufacturer_Model_Config... or datalogger_Manufacturer_Model_Config...
    parts = instconfig.split('_', 2)  # element, manufacturer, rest
    if len(parts) < 3:
        return Equipment(manufacturer='', model=instconfig, description=instconfig)
    element, manufacturer, rest = parts
    model_parts = rest.split('_')
    model = model_parts[0] if model_parts else rest
    return Equipment(
        manufacturer=manufacturer,
        model=model,
        description=instconfig
    )


class Nrlv2OnlineHelper:
    """Client for EarthScope/IRIS NRL Web Service (NRLv2 online)."""

    def __init__(self, base_url=None):
        self.base_url = (base_url or NRLV2_DEFAULT_URL).strip().rstrip('/') + '/'
        self.logger = logging.getLogger(__name__)
        _validate_url(self.base_url)

    def _request(self, path, params=None, stream=False):
        url = urljoin(self.base_url, path.lstrip('/'))
        params = params or {}
        params.setdefault('nodata', '404')
        start = time.time()
        last_err = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                r = requests.get(
                    url,
                    params=params,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                    stream=stream
                )
                elapsed = time.time() - start
                size = len(r.content) if not stream else 0
                self.logger.info(
                    'NRLv2 %s %s status=%s size=%s elapsed=%.2fs',
                    path, params, r.status_code, size, elapsed
                )
                if r.status_code == 404:
                    raise Nrlv2OnlineError('NRLV2_EMPTY_RESULT', 'No data found')
                if r.status_code >= 400:
                    raise Nrlv2OnlineError(
                        'NRLV2_BAD_REQUEST',
                        f'HTTP {r.status_code}: {r.text[:200] if r.text else "No content"}'
                    )
                return r
            except requests.exceptions.Timeout as e:
                last_err = Nrlv2OnlineError('NRLV2_TIMEOUT', str(e))
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_FACTOR * (attempt + 1))
            except requests.exceptions.ConnectionError as e:
                last_err = Nrlv2OnlineError('NRLV2_UNREACHABLE', str(e))
                if attempt < MAX_RETRIES:
                    time.sleep(BACKOFF_FACTOR * (attempt + 1))
            except Nrlv2OnlineError:
                raise
        raise last_err

    def catalog(self, element=None, manufacturer=None, model=None,
                level='configuration', updatedsince=None):
        """Fetch catalog from /catalog. Returns JSON dict."""
        params = {'format': 'json', 'level': level}
        if element:
            params['element'] = element
        if manufacturer:
            params['manufacturer'] = manufacturer
        if model:
            params['model'] = model
        if updatedsince:
            params['updatedsince'] = updatedsince
        r = self._request('catalog', params=params)
        return r.json()

    def combine(self, instconfig, fmt='stationxml-resp', net=None, sta=None,
                loc=None, cha=None, starttime=None, endtime=None, source=None):
        """Fetch response from /combine. Returns bytes (XML or RESP text).
        source: optional (auto|iris|asgsr) for NRLaggregator-style backends."""
        params = {'instconfig': instconfig, 'format': fmt}
        if net:
            params['net'] = net
        if sta:
            params['sta'] = sta
        if loc:
            params['loc'] = loc
        if cha:
            params['cha'] = cha
        if starttime:
            params['starttime'] = starttime
        if endtime:
            params['endtime'] = endtime
        if source:
            params['source'] = source
        r = self._request('combine', params=params)
        return r.content

    def get_channel_response_obj(self, instconfig, source=None):
        """Get ObsPy Response object from instconfig (single or cascade)."""
        xml_bytes = self.combine(instconfig, fmt='stationxml', source=source)
        inv = read_inventory(io.BytesIO(xml_bytes), format='STATIONXML')
        for network in inv.networks:
            for station in network.stations:
                for channel in station.channels:
                    if channel.response:
                        return _normalize_response_units(channel.response)
        raise Nrlv2OnlineError('NRLV2_EMPTY_RESULT', 'No response in result')

    def get_sensor_equipment(self, instconfig):
        """Parse instconfig and return Equipment for sensor part."""
        # For single sensor instconfig: sensor_MFR_Model_...
        # For cascade sensor:datalogger: take sensor part
        part = instconfig.split(':')[0] if ':' in instconfig else instconfig
        return _parse_instconfig_equipment(part)

    def get_datalogger_equipment(self, instconfig):
        """Parse instconfig and return Equipment for datalogger part."""
        if ':' in instconfig:
            part = instconfig.split(':')[1]
        else:
            part = instconfig
        return _parse_instconfig_equipment(part)

    def get_sensor_response_str(self, instconfig, source=None):
        """Get response text for sensor-only instconfig."""
        resp = self.get_channel_response_obj(instconfig, source=source)
        from yasmine.app.utils.response_plot import polynomial_or_polezero_response
        return polynomial_or_polezero_response(resp)

    def get_datalogger_response_str(self, instconfig, source=None):
        """Get response text for datalogger-only instconfig.
        Dataloggers often have only FIR/decimation stages (no PolesZeros), so we avoid
        get_sacpz() which would raise 'No PolesZerosResponseStage found'."""
        resp = self.get_channel_response_obj(instconfig, source=source)
        return str(resp)

    def _parse_catalog_tree(self, data, path):
        """Navigate NRLCatalog JSON. Returns the array at the end of path."""
        cur = data.get('NRLCatalog') or data
        for i, key in enumerate(path):
            if cur is None:
                return None
            val = cur.get(key) if isinstance(cur, dict) else None
            if val is None:
                return None
            # For nested arrays (element, manufacturer, model), take first item to drill down
            is_last = (i == len(path) - 1)
            if isinstance(val, list) and val:
                cur = val if is_last else val[0]
            else:
                cur = val
        return cur if isinstance(cur, list) else [cur] if cur else []

    def get_sensors_keys(self, path=None):
        """Build tree for sensors. path='' for manufacturers, 'Mfr' for models.
        For path mfr/model returns [] so frontend uses modifier panel instead."""
        el = 'sensor'
        if not path:
            data = self.catalog(element=el, level='manufacturer')
            mfrs = self._parse_catalog_tree(data, ['element', 'manufacturer'])
            if not mfrs:
                return []
            return [{'text': 'Select the manufacturer', 'key': m.get('name', ''), 'id': m.get('name', ''), 'leaf': False}
                    for m in (mfrs if isinstance(mfrs, list) else [mfrs])]
        parts = path.split('/', 1)
        mfr = parts[0]
        if len(parts) == 1:
            data = self.catalog(element=el, manufacturer=mfr, level='model')
            models = self._parse_catalog_tree(data, ['element', 'manufacturer', 'model'])
            if not models:
                return []
            return [{'text': 'Select the model', 'key': m.get('name', ''), 'id': f'{mfr}/{m.get("name", "")}', 'leaf': False}
                    for m in (models if isinstance(models, list) else [models])]
        model = parts[1]
        return []

    def get_sensor_configurations(self, manufacturer, model):
        """Get configurations with parameters for modifier UI.
        Returns {configurations, parameterNames, parameterOptions}."""
        data = self.catalog(
            element='sensor',
            manufacturer=manufacturer,
            model=model,
            level='configuration'
        )
        configs = self._parse_catalog_tree(
            data, ['element', 'manufacturer', 'model', 'configuration']
        )
        if not configs:
            return {'configurations': [], 'parameterNames': [], 'parameterOptions': {}}
        cfgs = configs if isinstance(configs, list) else [configs]
        configurations = []
        param_names = []
        param_options = {}
        for c in cfgs:
            configurations.append({
                'instconfig': c.get('instconfig', ''),
                'description': c.get('description', c.get('instconfig', '')),
                'parameters': c.get('parameters') or {},
                'source': c.get('source'),
            })
        first_with_params = next((c for c in configurations if c['parameters']), None)
        if not first_with_params or len(configurations) <= 1:
            return {
                'configurations': configurations,
                'parameterNames': [],
                'parameterOptions': {},
            }
        param_names = list(first_with_params['parameters'].keys())
        for pname in param_names:
            vals = []
            for c in configurations:
                v = (c.get('parameters') or {}).get(pname)
                if v is not None and str(v).strip():
                    vals.append(str(v).strip())
            sorted_vals = self._sort_param_options(vals)
            param_options[pname] = ['*'] + sorted_vals
        return {
            'configurations': configurations,
            'parameterNames': param_names,
            'parameterOptions': param_options,
        }

    def _sort_param_options(self, values):
        """Sort parameter values by heuristic: numeric, Hz/Vpp, then string."""
        def sort_key(v):
            s = str(v).strip()
            try:
                return (0, float(s))
            except ValueError:
                pass
            m = re.search(r'([\d.]+)\s*Hz', s, re.I)
            if m:
                return (1, float(m.group(1)))
            m = re.search(r'([\d.]+)\s*Vpp', s, re.I)
            if m:
                return (2, float(m.group(1)))
            return (3, s)
        return sorted(set(values), key=sort_key)

    def get_datalogger_configurations(self, manufacturer, model):
        """Get configurations with parameters for modifier UI.
        Returns {configurations, parameterNames, parameterOptions}."""
        data = self.catalog(
            element='datalogger',
            manufacturer=manufacturer,
            model=model,
            level='configuration'
        )
        configs = self._parse_catalog_tree(
            data, ['element', 'manufacturer', 'model', 'configuration']
        )
        if not configs:
            return {'configurations': [], 'parameterNames': [], 'parameterOptions': {}}
        cfgs = configs if isinstance(configs, list) else [configs]
        configurations = []
        param_names = []
        param_options = {}
        for c in cfgs:
            configurations.append({
                'instconfig': c.get('instconfig', ''),
                'description': c.get('description', c.get('instconfig', '')),
                'parameters': c.get('parameters') or {},
                'source': c.get('source'),
            })
        first_with_params = next((c for c in configurations if c['parameters']), None)
        if not first_with_params or len(configurations) <= 1:
            return {
                'configurations': configurations,
                'parameterNames': [],
                'parameterOptions': {},
            }
        param_names = list(first_with_params['parameters'].keys())
        for pname in param_names:
            vals = []
            for c in configurations:
                v = (c.get('parameters') or {}).get(pname)
                if v is not None and str(v).strip():
                    vals.append(str(v).strip())
            sorted_vals = self._sort_param_options(vals)
            param_options[pname] = ['*'] + sorted_vals
        return {
            'configurations': configurations,
            'parameterNames': param_names,
            'parameterOptions': param_options,
        }

    def get_dataloggers_keys(self, path=None):
        """Build tree for dataloggers. Same structure as sensors.
        For path mfr/model returns [] so frontend uses modifier panel instead."""
        el = 'datalogger'
        if not path:
            data = self.catalog(element=el, level='manufacturer')
            mfrs = self._parse_catalog_tree(data, ['element', 'manufacturer'])
            if not mfrs:
                return []
            return [{'text': 'Select the manufacturer', 'key': m.get('name', ''), 'id': m.get('name', ''), 'leaf': False}
                    for m in (mfrs if isinstance(mfrs, list) else [mfrs])]
        parts = path.split('/', 1)
        mfr = parts[0]
        if len(parts) == 1:
            data = self.catalog(element=el, manufacturer=mfr, level='model')
            models = self._parse_catalog_tree(data, ['element', 'manufacturer', 'model'])
            if not models:
                return []
            return [{'text': 'Select the model', 'key': m.get('name', ''), 'id': f'{mfr}/{m.get("name", "")}', 'leaf': False}
                    for m in (models if isinstance(models, list) else [models])]
        model = parts[1]
        return []
