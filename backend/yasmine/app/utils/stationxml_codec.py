# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
"""QName-aware StationXML 1.2 extension sidecars and serialization."""

from __future__ import annotations

from copy import copy
import io
import json

from lxml import etree

from yasmine.app.utils.stationxml_validation import (
    IMPORTABLE_SCHEMA_VERSIONS,
    STATIONXML_IMPORT_ERROR,
    STATIONXML_NAMESPACE,
    STATIONXML_VERSION,
)


PARSER = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    remove_blank_text=False,
)


def _parse(xml_data):
    if hasattr(xml_data, 'read'):
        value = xml_data.read()
    else:
        value = xml_data
    if isinstance(value, str):
        value = value.encode('utf-8')
    return etree.parse(io.BytesIO(bytes(value)), PARSER)


def _qname(element):
    return etree.QName(element)


def _is_stationxml_element(element, local_name=None):
    qname = _qname(element)
    return (
        qname.namespace == STATIONXML_NAMESPACE
        and (local_name is None or qname.localname == local_name)
    )


def _path_step(element):
    qname = _qname(element)
    index = 0
    sibling = element.getprevious()
    while sibling is not None:
        if isinstance(sibling.tag, str) and sibling.tag == element.tag:
            index += 1
        sibling = sibling.getprevious()
    return {'name': qname.localname, 'index': index}


def _extension_signature(element):
    qname = etree.QName(element)
    attrib = tuple(sorted(element.attrib.items()))
    text = (element.text or '').strip()
    return (qname.namespace, qname.localname, attrib, text)


def _stationxml_anchor(parent, position, direction):
    """Nearest StationXML sibling before (-1) or after (+1) *position*.

    ObsPy rewrite inserts optional elements, so a raw child index from the
    original document lands in the wrong place. Anchors follow the sibling
    that actually bordered the extension.
    """
    index = position + direction
    limit = -1 if direction < 0 else len(parent)
    target = None
    while index != limit:
        child = parent[index]
        if isinstance(child.tag, str) and _is_stationxml_element(child):
            target = _qname(child).localname
            target_at = index
            break
        index += direction
    if target is None:
        return None
    seen = 0
    stop = target_at + 1
    for sibling in parent[:stop]:
        if isinstance(sibling.tag, str) and _is_stationxml_element(sibling, target):
            seen += 1
    return {'name': target, 'index': seen - 1}


def extract_extension_sidecar(element, child_boundary=None):
    """Extract foreign attributes/elements below *element*.

    ``child_boundary`` names direct StationXML children that belong to a
    separate persisted inventory node and therefore receive their own sidecar.
    """
    child_boundary = set(child_boundary or ())
    attributes = []
    elements = []

    def walk(current, path):
        for name, value in current.attrib.items():
            qname = etree.QName(name)
            if qname.namespace and qname.namespace != STATIONXML_NAMESPACE:
                attributes.append({
                    'path': path,
                    'name': name,
                    'value': value,
                })

        for position, child in enumerate(current):
            if not isinstance(child.tag, str):
                continue
            qname = _qname(child)
            if (
                not path
                and qname.namespace == STATIONXML_NAMESPACE
                and qname.localname in child_boundary
            ):
                continue
            if qname.namespace != STATIONXML_NAMESPACE:
                elements.append({
                    'parentPath': path,
                    'position': position,
                    'after': _stationxml_anchor(current, position, -1),
                    'before': _stationxml_anchor(current, position, 1),
                    'xml': etree.tostring(
                        child,
                        encoding='unicode',
                        with_tail=False,
                    ),
                })
                continue
            walk(child, path + [_path_step(child)])

    walk(element, [])
    if not attributes and not elements:
        return None
    return json.dumps(
        {'attributes': attributes, 'elements': elements},
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    )


def _matching_child_indexes(parent, local_name):
    return [
        index
        for index, child in enumerate(parent)
        if isinstance(child.tag, str) and _is_stationxml_element(child, local_name)
    ]


def _anchor_index(parent, anchor, after):
    if not anchor:
        return None
    matches = _matching_child_indexes(parent, anchor.get('name'))
    if not matches:
        return None
    index = anchor.get('index', 0)
    if index < len(matches):
        match = matches[index]
    else:
        match = matches[-1] if after else matches[0]
    return match + 1 if after else match


def _extension_insert_index(parent, extension):
    """Place an extension beside the same StationXML siblings it had before."""
    if 'after' not in extension and 'before' not in extension:
        return min(extension.get('position', len(parent)), len(parent))
    start = _anchor_index(parent, extension.get('after'), True)
    end = _anchor_index(parent, extension.get('before'), False)
    if start is None:
        start = 0
    if end is None:
        end = len(parent)
    if start > end:
        start = end
    # Append inside the gap so several extensions keep document order.
    return end


def _find_relative(root, path):
    current = root
    for step in path:
        candidates = [
            child
            for child in current
            if isinstance(child.tag, str)
            and _is_stationxml_element(child, step['name'])
        ]
        index = step.get('index', 0)
        if index >= len(candidates):
            return None
        current = candidates[index]
    return current


def apply_extension_sidecar(element, sidecar):
    if not sidecar:
        return
    if isinstance(sidecar, str):
        sidecar = json.loads(sidecar)

    for attribute in sidecar.get('attributes', []):
        parent = _find_relative(element, attribute.get('path', []))
        if parent is not None:
            parent.set(attribute['name'], attribute['value'])

    for extension in sidecar.get('elements', []):
        parent = _find_relative(element, extension.get('parentPath', []))
        if parent is None:
            continue
        extension_element = etree.fromstring(
            extension['xml'].encode('utf-8'),
            PARSER,
        )
        signature = _extension_signature(extension_element)
        if any(
            isinstance(child.tag, str)
            and _extension_signature(child) == signature
            for child in parent
        ):
            continue
        parent.insert(_extension_insert_index(parent, extension), extension_element)


def extract_inventory_sidecars(xml_data):
    document = _parse(xml_data)
    root = document.getroot()
    result = {
        'sidecar': extract_extension_sidecar(root, {'Network'}),
        'compatibility': _compatibility_metadata(root),
        'children': [],
    }
    for network in root:
        if not _is_stationxml_element(network, 'Network'):
            continue
        network_record = {
            'sidecar': extract_extension_sidecar(network, {'Station'}),
            'compatibility': _compatibility_metadata(network),
            'children': [],
        }
        result['children'].append(network_record)
        for station in network:
            if not _is_stationxml_element(station, 'Station'):
                continue
            station_record = {
                'sidecar': extract_extension_sidecar(station, {'Channel'}),
                'compatibility': _compatibility_metadata(station),
                'children': [],
            }
            network_record['children'].append(station_record)
            for channel in station:
                if not _is_stationxml_element(channel, 'Channel'):
                    continue
                station_record['children'].append({
                    'sidecar': extract_extension_sidecar(channel),
                    'compatibility': _compatibility_metadata(channel),
                    'children': [],
                })
    return result


def _station_children(element, name):
    return [
        child
        for child in element
        if isinstance(child.tag, str)
        and _is_stationxml_element(child, name)
    ]


def _compatibility_metadata(element):
    for child in element:
        if not _is_stationxml_element(child, 'DataAvailability'):
            continue
        has_extent = any(
            _is_stationxml_element(item, 'Extent')
            for item in child
            if isinstance(item.tag, str)
        )
        has_span = any(
            _is_stationxml_element(item, 'Span')
            for item in child
            if isinstance(item.tag, str)
        )
        if has_span and not has_extent:
            return {'dataAvailabilityExtentAbsent': True}
    return {}


def insert_temporary_data_availability_extents(element):
    """Give span-only DataAvailability an Extent ObsPy can read."""
    changed = False
    for availability in element.iter('{%s}DataAvailability' % STATIONXML_NAMESPACE):
        extent = availability.find('{%s}Extent' % STATIONXML_NAMESPACE)
        spans = availability.findall('{%s}Span' % STATIONXML_NAMESPACE)
        if extent is not None or not spans:
            continue
        starts = [span.get('start') for span in spans if span.get('start')]
        ends = [span.get('end') for span in spans if span.get('end')]
        if not starts or not ends:
            continue
        extent = etree.Element('{%s}Extent' % STATIONXML_NAMESPACE)
        extent.set('start', min(starts))
        extent.set('end', max(ends))
        availability.insert(0, extent)
        changed = True
    return changed


def _copy_element(element):
    return etree.fromstring(etree.tostring(element))


def _station_sidecar_record(station):
    record = {
        'sidecar': extract_extension_sidecar(station, {'Channel'}),
        'compatibility': _compatibility_metadata(station),
        'children': [],
    }
    for child in station:
        if _is_stationxml_element(child, 'Channel'):
            record['children'].append({
                'sidecar': extract_extension_sidecar(child),
                'compatibility': _compatibility_metadata(child),
                'children': [],
            })
    return record


def _piece_document(root, header, network, preamble, station=None):
    """One network, optionally one station, for ObsPy to read."""
    new_root = etree.Element(root.tag, nsmap=root.nsmap)
    for key, value in root.attrib.items():
        new_root.set(key, value)
    for child in header:
        new_root.append(_copy_element(child))
    new_network = etree.Element(network.tag)
    for key, value in network.attrib.items():
        new_network.set(key, value)
    for child in preamble:
        new_network.append(_copy_element(child))
    if station is not None:
        station_copy = _copy_element(station)
        insert_temporary_data_availability_extents(station_copy)
        new_network.append(station_copy)
    new_root.append(new_network)
    return etree.tostring(new_root, xml_declaration=True, encoding='UTF-8')


def iter_stationxml_pieces(xml_data):
    """Yield a network preamble, then one station at a time.

    A response-level network file is hundreds of megabytes. Reading it as one
    ObsPy inventory exhausts memory, so each piece is a document ObsPy can
    read on its own. The source bytes are released as each station ends.
    """
    if isinstance(xml_data, str):
        xml_data = xml_data.encode('utf-8')
    context = etree.iterparse(
        io.BytesIO(bytes(xml_data)),
        events=('start', 'end'),
        resolve_entities=False,
        no_network=True,
        huge_tree=True,
        remove_blank_text=False,
    )
    root = None
    network = None
    header = []
    preamble = []
    network_opened = False
    try:
        for event, elem in context:
            if not isinstance(elem.tag, str):
                continue
            if event == 'start' and root is None:
                root = elem
                qname = _qname(elem)
                if (
                    qname.namespace != STATIONXML_NAMESPACE
                    or qname.localname != 'FDSNStationXML'
                    or elem.get('schemaVersion') not in IMPORTABLE_SCHEMA_VERSIONS
                ):
                    raise ValueError(STATIONXML_IMPORT_ERROR)
                continue
            if event != 'end' or elem is root:
                if event == 'end' and elem is root:
                    break
                continue
            parent = elem.getparent()
            if parent is root and network is None and not _is_stationxml_element(elem, 'Network'):
                if _is_stationxml_element(elem):
                    header.append(_copy_element(elem))
                continue
            if parent is root and _is_stationxml_element(elem, 'Network'):
                if not network_opened:
                    yield {
                        'kind': 'network',
                        'xml': _piece_document(root, header, elem, preamble),
                        'sidecar': extract_extension_sidecar(elem, {'Station'}),
                        'compatibility': _compatibility_metadata(elem),
                    }
                network = None
                preamble = []
                network_opened = False
                elem.clear()
                continue
            if not _is_stationxml_element(elem.getparent(), 'Network'):
                continue
            network = elem.getparent()
            if not _is_stationxml_element(elem, 'Station'):
                preamble.append(_copy_element(elem))
                continue
            if not network_opened:
                yield {
                    'kind': 'network',
                    'xml': _piece_document(root, header, network, preamble),
                    'sidecar': extract_extension_sidecar(network, {'Station'}),
                    'compatibility': _compatibility_metadata(network),
                }
                network_opened = True
            yield {
                'kind': 'station',
                'xml': _piece_document(root, header, network, preamble, elem),
                'record': _station_sidecar_record(elem),
            }
            network.remove(elem)
        if root is not None:
            yield {
                'kind': 'root',
                'sidecar': extract_extension_sidecar(root, {'Network'}),
            }
    except etree.XMLSyntaxError:
        raise ValueError(STATIONXML_IMPORT_ERROR)


def prepare_stationxml_for_obspy(xml_data):
    """Add temporary extents for ObsPy versions that reject span-only data."""
    document = _parse(xml_data)
    changed = insert_temporary_data_availability_extents(document.getroot())
    if not changed:
        if hasattr(xml_data, 'read'):
            return etree.tostring(
                document,
                xml_declaration=True,
                encoding='UTF-8',
            )
        return xml_data.encode('utf-8') if isinstance(xml_data, str) else bytes(xml_data)
    return etree.tostring(
        document,
        xml_declaration=True,
        encoding='UTF-8',
    )


def _strip_foreign_content(element):
    """Drop foreign nodes ObsPy hoists to the wrong parent before reapplying."""
    for child in list(element):
        if not isinstance(child.tag, str):
            continue
        if not _is_stationxml_element(child):
            element.remove(child)
            continue
        _strip_foreign_content(child)
    for name in list(element.attrib):
        qname = etree.QName(name)
        if qname.namespace and qname.namespace != STATIONXML_NAMESPACE:
            del element.attrib[name]


def apply_inventory_sidecars(xml_data, sidecar_tree):
    document = _parse(xml_data)
    root = document.getroot()
    root.set('schemaVersion', STATIONXML_VERSION)
    _strip_foreign_content(root)
    sidecar_tree = sidecar_tree or {}
    apply_extension_sidecar(root, sidecar_tree.get('sidecar'))

    levels = [
        ('Network', 'Station'),
        ('Station', 'Channel'),
        ('Channel', None),
    ]

    def apply_children(parent, record, level):
        if level >= len(levels):
            return
        child_name, _ = levels[level]
        xml_children = _station_children(parent, child_name)
        records = record.get('children', [])
        for child, child_record in zip(xml_children, records):
            apply_extension_sidecar(child, child_record.get('sidecar'))
            apply_children(child, child_record, level + 1)

    apply_children(root, sidecar_tree, 0)
    return etree.tostring(
        document,
        xml_declaration=True,
        encoding='UTF-8',
        pretty_print=True,
    )


def serialize_inventory_12(inventory, sidecar_tree=None, validate=False):
    output = io.BytesIO()
    inventory.write(output, format='STATIONXML', validate=validate)
    return apply_inventory_sidecars(output.getvalue(), sidecar_tree)


MEASUREMENT_FIELDS = {
    'plusError': 'upper_uncertainty',
    'plus_error': 'upper_uncertainty',
    'upper_uncertainty': 'upper_uncertainty',
    'minusError': 'lower_uncertainty',
    'minus_error': 'lower_uncertainty',
    'lower_uncertainty': 'lower_uncertainty',
    'measurementMethod': 'measurement_method',
    'measurement_method': 'measurement_method',
    'unit': '_unit',
    'datum': 'datum',
}

MEASURED_ATTRIBUTE_NAMES = {
    'latitude',
    'longitude',
    'elevation',
    'depth',
    'azimuth',
    'dip',
    'water_level',
    'sample_rate',
    'clock_drift_in_seconds_per_sample',
}


def merge_measured_value(existing, value, value_class=None):
    """Replace a measured scalar without silently dropping its metadata."""
    metadata = {}
    scalar = value
    if isinstance(value, dict):
        scalar = value.get('value', value.get('_value'))
        for source, target in MEASUREMENT_FIELDS.items():
            if source in value:
                metadata[target] = value[source]

    if existing is None or not hasattr(existing, '__dict__'):
        if value_class is None:
            return value
        try:
            existing = value_class(
                scalar if scalar is not None else existing
            )
        except (TypeError, ValueError):
            return value

    if not isinstance(value, dict):
        for target in set(MEASUREMENT_FIELDS.values()):
            if hasattr(existing, target):
                metadata[target] = getattr(existing, target)

    try:
        merged = existing.__class__(scalar)
    except (TypeError, ValueError):
        try:
            merged = copy(existing)
        except TypeError:
            return value

    for name, item in metadata.items():
        try:
            setattr(merged, name, item)
        except (AttributeError, TypeError, ValueError):
            if name == '_unit':
                try:
                    setattr(merged, 'unit', item)
                except (AttributeError, TypeError, ValueError):
                    pass
    return merged


def measured_value_payload(value):
    if value is None or not hasattr(value, '__dict__'):
        return value
    result = {'value': float(value)}
    mappings = {
        'upper_uncertainty': 'plusError',
        'lower_uncertainty': 'minusError',
        'measurement_method': 'measurementMethod',
        '_unit': 'unit',
        'datum': 'datum',
    }
    for source, target in mappings.items():
        item = getattr(value, source, None)
        if item is not None:
            result[target] = item
    return result


def measured_metadata_payload(value):
    if value is None or not hasattr(value, '__dict__'):
        return None
    mappings = {
        'upper_uncertainty': 'plus_error',
        'lower_uncertainty': 'minus_error',
        'measurement_method': 'measurement_method',
        '_unit': 'unit',
        'datum': 'datum',
    }
    result = {}
    for source, target in mappings.items():
        item = getattr(value, source, None)
        if item is not None:
            result[target] = item
    return result or None
