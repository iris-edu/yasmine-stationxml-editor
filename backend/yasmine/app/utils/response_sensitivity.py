# ****************************************************************************
#
# Response sensitivity recalculation helpers.
#
# ****************************************************************************/

import io
import re

from lxml.etree import fromstring
from obspy import UTCDateTime, read_inventory
from obspy.core.inventory import Channel, Inventory, Network, Site, Station
from xmljson import abdera

from yasmine.app.enums.library import LibraryTypeEnum
from yasmine.app.helpers.library_helper_factory import LibraryHelperFactory
from yasmine.app.utils.imp_exp import ConvertToInventory


class PolynomialResponseError(ValueError):
    """Raised when recalculate is requested for a polynomial response."""


def recalculate_response_sensitivity(response):
    """Recalculate InstrumentSensitivity from all response stages via ObsPy."""
    if response.instrument_polynomial:
        raise PolynomialResponseError('Polynomial responses have no InstrumentSensitivity')
    freq = 1.0
    sens = response.instrument_sensitivity
    if sens and sens.frequency:
        freq = float(sens.frequency)
    response.recalculate_overall_sensitivity(frequency=freq)
    return response, freq


def prepare_response_json_as_xml(json_obj, parent_node=None, xml_str=''):
    """Build Response XML fragment from the tree-editor JSON structure."""
    for key, value in json_obj.items():
        if key == 'children':
            for item in value:
                if isinstance(item, dict):
                    xml_str = prepare_response_json_as_xml(item, parent_node, xml_str)
                else:
                    xml_str += str(item)
        elif key == 'attributes':
            attrs = ''
            for attr_key, attr_value in value.items():
                if len(str(attr_value)) > 0:
                    if len(attrs) > 0:
                        attrs += ' '
                    attrs += '%s="%s"' % (attr_key, attr_value)
            start = xml_str.rfind('<%s>' % parent_node)
            end = start + len(parent_node) + 2
            xml_str = xml_str[:start] + '<%s %s>' % (parent_node, attrs) + xml_str[end:]
        else:
            xml_str += '<%s>' % key
            if isinstance(value, dict):
                xml_str = prepare_response_json_as_xml(value, key, xml_str)
            else:
                xml_str += str(value)
            xml_str += '</%s>' % key
    return xml_str


def _minimal_station_xml(response_xml):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<FDSNStationXML xmlns="http://www.fdsn.org/xml/station/1" schemaVersion="1.1">
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
    resp_start = station_xml.find('<Response>')
    if resp_start >= 0:
        resp_end = station_xml.find('</Response>') + len('</Response>')
        return station_xml[:resp_start] + response_xml + station_xml[resp_end:]
    channel_end = station_xml.rfind('</Channel>')
    if channel_end < 0:
        raise ValueError('No Channel element in station XML')
    return station_xml[:channel_end] + response_xml + station_xml[channel_end:]


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
    response_xml = prepare_response_json_as_xml(response_tree)
    station_xml = _minimal_station_xml(response_xml)
    return get_updated_response_obj(response_xml, station_xml)


def response_json_to_obj(response_json, node_inst_id, handler):
    """Parse tree-editor JSON into an ObsPy Response object using a channel context."""
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
    resp_start = station_xml.find('<Response>')
    resp_end = station_xml.find('</Response>') + 11
    response_xml = station_xml[resp_start:resp_end]
    return abdera.data(fromstring(response_xml))


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
    resp_start = station_xml.find('<Response>')
    resp_end = station_xml.find('</Response>') + 11
    response_xml = station_xml[resp_start:resp_end]
    return abdera.data(fromstring(response_xml))
