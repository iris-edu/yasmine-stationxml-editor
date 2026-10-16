# 2026-09-24, version 4.3.1-beta: ASGSR, Alexey Emanov
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
from yasmine.app.utils.url_guard import NRL_SCHEMES, UrlGuardError, validate_url

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30
MAX_RETRIES = 2
BACKOFF_FACTOR = 1.0


class Nrlv2OnlineError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def _validate_url(base_url):
    """SSRF protection: http/https only. Raw private IPs blocked; hostnames allowed."""
    try:
        validate_url(
            base_url,
            schemes=NRL_SCHEMES,
            require_allowlist=False,
            allow_private_hostnames=True,
        )
    except UrlGuardError:
        raise Nrlv2OnlineError('NRLV2_BAD_REQUEST', 'Private/local URLs not allowed')


NRL_CATALOG_ELEMENTS = ('sensor', 'datalogger', 'integrated', 'soh')
NRL_SINGLE_ELEMENTS = ('integrated', 'soh')


def _catalog_element(data):
    """First element object from an NRL catalog payload."""
    cur = data.get('NRLCatalog') if isinstance(data, dict) else None
    cur = cur if isinstance(cur, dict) else data
    element = cur.get('element') if isinstance(cur, dict) else None
    if isinstance(element, list):
        element = element[0] if element else None
    return element if isinstance(element, dict) else {}


def _catalog_help(entry):
    """Plain-text help from an NRL catalog node. The service stores it as detail."""
    if not isinstance(entry, dict):
        return ''
    detail = entry.get('detail')
    if detail is None:
        return ''
    return str(detail).strip()


def nrlv2_equipment_flags(instconfig):
    """Return (fill_sensor, fill_datalogger) for an NRLv2 instconfig.

    Integrated instruments are one device, so both StationXML equipment
    fields are filled. SOH responses describe a recorder channel.
    """
    if not instconfig:
        return False, False
    head = instconfig.split(':', 1)[0]
    if head.startswith('integrated_'):
        return True, True
    if head.startswith('soh_'):
        return False, True
    return head.startswith('sensor_'), ('datalogger_' in instconfig)


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

    def _require_element(self, element):
        if element not in NRL_CATALOG_ELEMENTS:
            raise Nrlv2OnlineError('NRLV2_BAD_REQUEST', 'unsupported element')

    def get_element_nodes(self, element, path=None):
        """Return (tree nodes, element help).

        Element help is the catalog detail for the element itself and is
        only present when listing manufacturers.
        """
        self._require_element(element)
        if path:
            return self.get_element_keys(element, path), ''
        if not path:
            data = self.catalog(element=element, level='manufacturer')
            mfrs = self._parse_catalog_tree(data, ['element', 'manufacturer'])
            element_help = _catalog_help(_catalog_element(data))
            if not mfrs:
                return [], element_help
            return [{
                'text': 'Select the manufacturer',
                'key': m.get('name', ''),
                'id': m.get('name', ''),
                'leaf': False,
                'help': _catalog_help(m),
            } for m in (mfrs if isinstance(mfrs, list) else [mfrs])], element_help

    def get_element_keys(self, element, path=None):
        """Build a manufacturer/model tree for one catalog element.

        path is empty for manufacturers and 'Mfr' for models. A path of
        mfr/model returns [] so the frontend opens the modifier panel.
        """
        self._require_element(element)
        if not path:
            return self.get_element_nodes(element, path)[0]
        parts = path.split('/', 1)
        mfr = parts[0]
        if len(parts) == 1:
            data = self.catalog(element=element, manufacturer=mfr, level='model')
            models = self._parse_catalog_tree(data, ['element', 'manufacturer', 'model'])
            if not models:
                return []
            return [{
                'text': 'Select the model',
                'key': m.get('name', ''),
                'id': f'{mfr}/{m.get("name", "")}',
                'leaf': False,
                'help': _catalog_help(m),
            } for m in (models if isinstance(models, list) else [models])]
        return []

    def get_element_configurations(self, element, manufacturer, model):
        """Configurations and parameter choices for the modifier UI."""
        self._require_element(element)
        data = self.catalog(
            element=element,
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
        param_options = {}
        for pname in param_names:
            vals = []
            for c in configurations:
                v = (c.get('parameters') or {}).get(pname)
                if v is not None and str(v).strip():
                    vals.append(str(v).strip())
            param_options[pname] = ['*'] + self._sort_param_options(vals)
        return {
            'configurations': configurations,
            'parameterNames': param_names,
            'parameterOptions': param_options,
        }

    def get_element_response_str(self, instconfig, source=None):
        """Preview text for one integrated or SOH instconfig."""
        resp = self.get_channel_response_obj(instconfig, source=source)
        from yasmine.app.utils.response_plot import polynomial_or_polezero_response
        try:
            return polynomial_or_polezero_response(resp)
        except Exception:
            return str(resp)

    def get_sensors_keys(self, path=None):
        """Build tree for sensors. path='' for manufacturers, 'Mfr' for models.
        For path mfr/model returns [] so frontend uses modifier panel instead."""
        return self.get_element_keys('sensor', path)

    def get_sensor_configurations(self, manufacturer, model):
        """Get configurations with parameters for modifier UI.
        Returns {configurations, parameterNames, parameterOptions}."""
        return self.get_element_configurations('sensor', manufacturer, model)

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
        return self.get_element_configurations('datalogger', manufacturer, model)

    def get_dataloggers_keys(self, path=None):
        """Build tree for dataloggers. Same structure as sensors.
        For path mfr/model returns [] so frontend uses modifier panel instead."""
        return self.get_element_keys('datalogger', path)
