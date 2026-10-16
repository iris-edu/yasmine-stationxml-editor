# 2026-09-28, version 4.4.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Response sensitivity recalculation helpers.
#
# ****************************************************************************/

import copy
import io
import re

from obspy import UTCDateTime, read_inventory
from obspy.core.inventory import Channel, Inventory, Network, Site, Station
from obspy.core.inventory.response import paz_to_sacpz_string

from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.utils.imp_exp import ConvertToInventory
from yasmine.app.utils.response_plot import INVALID_STORED_RESPONSE, _is_response_object
from yasmine.app.utils.response_schema import validate_response_tree
from yasmine.app.utils.response_tree import (
    replace_response_in_station_xml,
    response_tree_to_xml,
    station_xml_response_to_tree,
)


class PolynomialResponseError(ValueError):
    """Raised when recalculate is requested for a polynomial response."""


def _validate_response_tree_or_raise(response_tree):
    errors = [
        issue for issue in validate_response_tree(response_tree)
        if issue['severity'] == 'error'
    ]
    if errors:
        raise ValueError('; '.join(
            '%s: %s' % (issue['path'], issue['message'])
            for issue in errors
        ))


def _sensitivity_value_is_zero(value):
    try:
        return value is not None and float(value) == 0.0
    except (TypeError, ValueError):
        return False


def _positive_float_or_none(value):
    try:
        if value is None:
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number <= 0 or number == float('inf'):
        return None
    return number


def _sample_rate_from_response_stages(response):
    """Final output sample rate, matching ObsPy recalculate_overall_sensitivity."""
    stages = getattr(response, 'response_stages', None) or []
    for stage in reversed(list(stages)):
        input_rate = _positive_float_or_none(
            getattr(stage, 'decimation_input_sample_rate', None)
        )
        factor = _positive_float_or_none(getattr(stage, 'decimation_factor', None))
        if input_rate is not None and factor is not None:
            return input_rate / factor
    return None


def _first_stage_normalization_frequency(response):
    stages = getattr(response, 'response_stages', None) or []
    if not stages:
        return None
    return _positive_float_or_none(
        getattr(stages[0], 'normalization_frequency', None)
    )


def get_sensitivity_recalculate_options(response):
    """Values shown in the Recalculate Sensitivity frequency dialog."""
    if not _is_response_object(response):
        raise ValueError(INVALID_STORED_RESPONSE)
    if response.instrument_polynomial:
        raise PolynomialResponseError('Polynomial responses have no InstrumentSensitivity')
    normalization_frequency = _first_stage_normalization_frequency(response)
    sample_rate = _sample_rate_from_response_stages(response)
    auto_frequency = None
    if normalization_frequency is not None and sample_rate is not None:
        auto_frequency = min(normalization_frequency, (sample_rate / 2.0) / 2.0)
    elif normalization_frequency is not None:
        auto_frequency = normalization_frequency
    sens = response.instrument_sensitivity
    reported_value = None
    reported_frequency = None
    if sens is not None:
        if getattr(sens, 'value', None) is not None:
            try:
                reported_value = float(sens.value)
            except (TypeError, ValueError):
                reported_value = None
        reported_frequency = _positive_float_or_none(getattr(sens, 'frequency', None))
    return {
        'normalization_frequency': normalization_frequency,
        'sample_rate': sample_rate,
        'auto_frequency': auto_frequency,
        'reported_sensitivity_value': reported_value,
        'reported_sensitivity_frequency': reported_frequency,
        'zero_sensitivity_value': _sensitivity_value_is_zero(reported_value),
        'stored_frequency_ignored_by_auto': True,
    }


def _patch_zero_stage0_gain(sens):
    if sens is not None and _sensitivity_value_is_zero(getattr(sens, 'value', None)):
        sens.value = 1.0


def recalculate_response_sensitivity(
        response, frequency=None, *, auto=False, allow_zero_gain_reset=False):
    """Recalculate InstrumentSensitivity from all response stages via ObsPy.

    * ``auto=True`` — ObsPy chooses frequency (first-stage normalization,
      capped by Nyquist/2); ignores stored InstrumentSensitivity.frequency.
    * ``frequency`` set — evaluate at that explicit Hz.
    * neither — legacy: use InstrumentSensitivity.frequency when > 0, else
      ObsPy auto; non-positive stored frequency becomes 1.0.

    A stored InstrumentSensitivity value of 0 cannot be evaluated by ObsPy.
    Callers must pass ``allow_zero_gain_reset=True`` (user confirm or
    automated NRL/equipment paths) before the temporary 0→1 rewrite.
    """
    if not _is_response_object(response):
        raise ValueError(INVALID_STORED_RESPONSE)
    if response.instrument_polynomial:
        raise PolynomialResponseError('Polynomial responses have no InstrumentSensitivity')
    sens = response.instrument_sensitivity
    if sens is not None and _sensitivity_value_is_zero(getattr(sens, 'value', None)):
        if not allow_zero_gain_reset:
            raise ValueError(
                'InstrumentSensitivity value is 0. Confirm resetting it to 1.0 '
                'before recalculate (ObsPy cannot evaluate a zero overall sensitivity).'
            )
        _patch_zero_stage0_gain(sens)

    if auto:
        response.recalculate_overall_sensitivity()
        stored = getattr(response.instrument_sensitivity, 'frequency', None)
        freq = float(stored) if stored is not None else 1.0
        return response, freq

    if frequency is not None:
        freq = float(frequency)
        if freq <= 0:
            raise ValueError('frequency must be greater than zero')
        response.recalculate_overall_sensitivity(frequency=freq)
        return response, freq

    # Legacy path for internal callers (NRL combine, equipment save).
    freq = None
    if sens and sens.frequency is not None:
        freq = float(sens.frequency)
    # A non-positive sensitivity frequency is not a place evalresp can normalize.
    # A missing frequency is left unset so ObsPy uses the stage normalization frequency.
    if freq is not None and freq <= 0:
        freq = 1.0
    if freq is None:
        response.recalculate_overall_sensitivity()
        stored = getattr(response.instrument_sensitivity, 'frequency', None)
        freq = float(stored) if stored is not None else 1.0
    else:
        response.recalculate_overall_sensitivity(frequency=freq)
    return response, freq


def validate_response_sacpz(response):
    """Validate SAC PZ conversion while accepting omitted uncertainties."""
    paz = copy.deepcopy(response.get_paz())
    for item in paz.poles + paz.zeros:
        if item.upper_uncertainty is None:
            item.upper_uncertainty = 0.0
        if item.lower_uncertainty is None:
            item.lower_uncertainty = 0.0
    return paz_to_sacpz_string(paz, response.instrument_sensitivity)


def prepare_response_json_as_xml(json_obj, parent_node=None, xml_str=''):
    """Serialize legacy response tree JSON using the QName-aware lxml codec.

    ``parent_node`` and ``xml_str`` remain only for source compatibility with
    older callers. New callers should use ``response_tree_to_xml`` directly.
    """
    if parent_node is not None:
        raise ValueError('Partial response serialization is no longer supported')
    return xml_str + response_tree_to_xml(json_obj)


def _minimal_station_xml(response_xml):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" schemaVersion="1.2">
  <Source>Yasmine</Source>
  <Module>Yasmine</Module>
  <ModuleURI></ModuleURI>
  <Created>2020-01-01T00:00:00</Created>
  <Network code="XX">
    <Station code="YY" StartDate="2020-01-01T00:00:00">
      <Latitude>0.0</Latitude>
      <Longitude>0.0</Longitude>
      <Elevation>0.0</Elevation>
      <Site><Name>Mock</Name></Site>
      <Channel code="HHZ" locationCode="00" StartDate="2020-01-01T00:00:00">
        <Latitude>0.0</Latitude>
        <Longitude>0.0</Longitude>
        <Elevation>0.0</Elevation>
        <Depth>0.0</Depth>
        <Azimuth>0.0</Azimuth>
        <Dip>0.0</Dip>
        <SampleRate>100.0</SampleRate>
        {response_xml}
      </Channel>
    </Station>
  </Network>
</FDSNStationXML>'''


def merge_response_into_station_xml(response_xml, station_xml):
    """Replace or insert a Response element in a StationXML document string."""
    return replace_response_in_station_xml(response_xml, station_xml)


def get_updated_response_obj(response_xml, station_xml):
    """Parse merged StationXML and return the channel Response object."""
    station_xml = merge_response_into_station_xml(response_xml, station_xml)
    station_xml_binary = io.BytesIO(station_xml.encode('utf-8'))
    inv = read_inventory(station_xml_binary)
    for network in inv.networks:
        for station in network.stations:
            for channel in station.channels:
                if hasattr(channel, 'response'):
                    return getattr(channel, 'response')


def response_tree_to_obj(response_tree):
    """Parse tree-editor JSON into an ObsPy Response object."""
    _validate_response_tree_or_raise(response_tree)
    response_xml = prepare_response_json_as_xml(response_tree)
    station_xml = _minimal_station_xml(response_xml)
    return get_updated_response_obj(response_xml, station_xml)


def response_json_to_obj(response_json, node_inst_id, handler):
    """Parse tree-editor JSON into an ObsPy Response object using a channel context."""
    _validate_response_tree_or_raise(response_json)
    response_xml = prepare_response_json_as_xml(response_json)
    station_xml = ConvertToInventory(None, handler).get_station_xml_for_channel(node_inst_id)
    return get_updated_response_obj(response_xml, station_xml)


def load_response_for_node(node_inst_id, handler, response_json=None):
    """Load Response from tree JSON or from the channel stored in the database."""
    if response_json:
        return response_json_to_obj(response_json, node_inst_id, handler)
    channel = ConvertToInventory(None, handler).convert_channel(node_inst_id)
    return channel.response


def load_response_from_preview_params(params, handler=None):
    """Load Response from saved channel, instconfig, or library keys."""
    node_inst_id = params.get('nodeInstanceId')
    if node_inst_id:
        return load_response_for_node(node_inst_id, handler, params.get('response'))

    instconfig = params.get('instconfig')
    if instconfig:
        app = getattr(handler, 'application', None) if handler else None
        helper = LibraryHelperFactory().get_helper(LibraryTypeEnum.NRLV2_ONLINE, application=app)
        return helper.get_channel_response_obj(instconfig, source=params.get('source'))

    library_type = params.get('libraryType')
    sensor_keys = params.get('sensorKeys')
    datalogger_keys = params.get('dataloggerKeys')
    nrl_response_type = params.get('nrlResponseType')
    if library_type == LibraryTypeEnum.NRL and nrl_response_type in ('integrated', 'soh') and sensor_keys:
        helper = LibraryHelperFactory().get_helper(library_type)
        return helper.get_element_response_obj(nrl_response_type, sensor_keys)
    if library_type and sensor_keys and datalogger_keys:
        helper = LibraryHelperFactory().get_helper(library_type)
        return helper.get_channel_response_obj(sensor_keys, datalogger_keys)

    raise ValueError('nodeInstanceId, instconfig, or libraryType with sensorKeys and dataloggerKeys required')


def preview_plot_basename(params):
    """Basename for preview plot files (wizard or saved channel)."""
    node_inst_id = params.get('nodeInstanceId')
    if node_inst_id:
        return f'channel_node_{node_inst_id}'
    instconfig = params.get('instconfig')
    if instconfig:
        slug = re.sub(r'[^\w\-]+', '_', instconfig)[:120]
        return f'wizard_preview_{slug}'
    library_type = params.get('libraryType') or 'preview'
    sensor_keys = params.get('sensorKeys') or []
    datalogger_keys = params.get('dataloggerKeys') or []
    slug = re.sub(
        r'[^\w\-]+', '_',
        f'{library_type}_{"_".join(sensor_keys)}_{"_".join(datalogger_keys)}',
    )[:120]
    return f'wizard_preview_{slug}'


def response_obj_to_tree_json(response, node_inst_id, handler):
    """Serialize an ObsPy Response to the tree-editor JSON format."""
    converter = ConvertToInventory(None, handler)
    inv = converter.get_inventory_for_channel(node_inst_id)
    inv.networks[0].stations[0].channels[0].response = response
    output = io.BytesIO()
    inv.write(output, format='STATIONXML')
    station_xml = output.getvalue().decode('utf-8')
    output.close()
    return station_xml_response_to_tree(station_xml)


def response_obj_to_tree_json_standalone(response):
    """Serialize Response to tree JSON without a database channel."""
    start_date = UTCDateTime(2020, 1, 1)
    channel = Channel(
        code='HHZ',
        location_code='00',
        latitude=0.0,
        longitude=0.0,
        elevation=0.0,
        depth=0.0,
        azimuth=0.0,
        dip=0.0,
        sample_rate=100.0,
        start_date=start_date,
        response=response,
    )
    station = Station(
        code='YY',
        latitude=0.0,
        longitude=0.0,
        elevation=0.0,
        start_date=start_date,
        site=Site('Mock'),
        channels=[channel],
    )
    network = Network(code='XX', stations=[station], start_date=start_date)
    inv = Inventory(
        networks=[network],
        source='Yasmine',
        module='Yasmine',
        module_uri='',
        created=start_date,
    )
    output = io.BytesIO()
    inv.write(output, format='STATIONXML')
    station_xml = output.getvalue().decode('utf-8')
    output.close()
    return station_xml_response_to_tree(station_xml)
