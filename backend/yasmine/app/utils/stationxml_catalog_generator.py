# 2026-09-23, version 4.2.0-beta: ASGSR, Alexey Emanov
"""Generate a deterministic StationXML 1.2 schema/help catalog.

This module is a build-time tool. Runtime code reads the generated JSON and
does not require the ``xmlschema`` package.
"""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import xmlschema
from xmlschema.validators import (
    XsdAnyAttribute,
    XsdAnyElement,
    XsdAttribute,
    XsdComplexType,
    XsdElement,
    XsdGroup,
)


STATIONXML_VERSION = '1.2'
STATIONXML_NAMESPACE = 'http://www.fdsn.org/xml/station/1'
CATALOG_FORMAT_VERSION = 1
EXPECTED_SCHEMA_SHA256 = (
    '5d5ce5e6fd26510f87a15bce194894bfaacd3e38a8d04ee26123e8a07da56096'
)

SPECIAL_DOCUMENTATION_TAGS = {'example', 'warning', 'levelDesc'}


def _local_name(name):
    if not name:
        return None
    return name.rsplit('}', 1)[-1]


def _normalise_text(value):
    if value is None:
        return ''
    return ' '.join(str(value).split())


def _append_unique(target, value):
    value = _normalise_text(value)
    if value and value not in target:
        target.append(value)


def _inner_xml(element):
    from xml.etree import ElementTree

    if len(element):
        value = ''.join(
            ElementTree.tostring(child, encoding='unicode')
            for child in element
        )
        if element.text and element.text.strip():
            value = element.text + value
        return _normalise_text(value)
    return _normalise_text(element.text)


def _plain_documentation_text(element):
    parts = []
    if element.text:
        parts.append(element.text)
    for child in element:
        if _local_name(child.tag) not in SPECIAL_DOCUMENTATION_TAGS:
            parts.extend(child.itertext())
        if child.tail:
            parts.append(child.tail)
    return _normalise_text(' '.join(parts))


def _level_for_path(path):
    segments = path.split('/')
    if 'Channel' in segments:
        return 'C'
    if 'Station' in segments:
        return 'S'
    if 'Network' in segments:
        return 'N'
    return None


def _selector_matches(element, level, element_name, parent_name=None):
    level_choice = element.attrib.get('LevelChoice')
    if level_choice and level_choice != level:
        return False

    element_choice = element.attrib.get('ElementChoice')
    if not element_choice:
        return True
    if element_choice.startswith('^'):
        try:
            distance = int(element_choice[1:])
        except ValueError:
            return False
        return distance == 1 and parent_name == element_name
    return element_choice == element_name


def _iter_type_chain(type_obj):
    seen = set()
    current = type_obj
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        content = getattr(current, 'content', None)
        if content is not None and content is not current:
            yield content
        current = getattr(current, 'base_type', None)


def _documentation(component, path, element_name, parent_name=None):
    result = {
        'description': [],
        'examples': [],
        'warnings': [],
        'sources': [],
    }
    level = _level_for_path(path)

    sources = [component]
    component_type = getattr(component, 'type', None)
    if component_type is not None:
        sources.extend(_iter_type_chain(component_type))

    seen_sources = set()
    for source in sources:
        if id(source) in seen_sources:
            continue
        seen_sources.add(id(source))
        annotation = getattr(source, 'annotation', None)
        if annotation is None:
            continue

        source_name = (
            _local_name(getattr(source, 'name', None))
            or type(source).__name__
        )
        source_used = False
        for documentation in annotation.documentation:
            plain_text = _plain_documentation_text(documentation)
            if plain_text:
                _append_unique(result['description'], plain_text)
                source_used = True

            for child in documentation:
                tag = _local_name(child.tag)
                if tag not in SPECIAL_DOCUMENTATION_TAGS:
                    continue
                if not _selector_matches(
                    child, level, element_name, parent_name=parent_name
                ):
                    continue
                if tag == 'levelDesc':
                    _append_unique(result['description'], ''.join(child.itertext()))
                elif tag == 'warning':
                    _append_unique(result['warnings'], ''.join(child.itertext()))
                elif tag == 'example':
                    _append_unique(result['examples'], _inner_xml(child))
                source_used = True

        if source_used and source_name not in result['sources']:
            result['sources'].append(source_name)

    return result


def _type_name(type_obj):
    return _local_name(getattr(type_obj, 'name', None))


def _type_metadata(type_obj):
    if type_obj is None:
        return {
            'declaredType': None,
            'baseType': None,
            'primitiveType': None,
            'derivationChain': [],
        }

    declared = _type_name(type_obj)
    base = _type_name(getattr(type_obj, 'base_type', None))
    primitive = _type_name(getattr(type_obj, 'primitive_type', None))
    if primitive is None:
        content = getattr(type_obj, 'content', None)
        primitive = _type_name(getattr(content, 'primitive_type', None))
        if primitive is None:
            primitive = _type_name(content)

    chain = []
    for item in _iter_type_chain(type_obj):
        name = _type_name(item)
        if name and name not in chain:
            chain.append(name)

    return {
        'declaredType': declared,
        'baseType': base,
        'primitiveType': primitive,
        'derivationChain': chain,
    }


def _facet_value(facet):
    if hasattr(facet, 'enumeration') and facet.enumeration is not None:
        return list(facet.enumeration)
    elem = getattr(facet, 'elem', None)
    if elem is not None and 'value' in elem.attrib:
        return elem.attrib['value']
    value = getattr(facet, 'value', None)
    if value is None:
        return None
    return value


def _facets(type_obj):
    result = OrderedDict()
    for item in _iter_type_chain(type_obj):
        for name, facet in getattr(item, 'facets', {}).items():
            local_name = _local_name(name)
            if local_name in result:
                continue
            value = _facet_value(facet)
            if value is not None:
                result[local_name] = value
    return result


def _definition_id(component):
    owner = getattr(component, 'parent', None)
    while owner is not None and not isinstance(owner, (XsdComplexType, XsdGroup)):
        owner = getattr(owner, 'parent', None)
    owner_name = _local_name(getattr(owner, 'name', None)) or type(owner).__name__
    kind = 'attribute' if isinstance(component, XsdAttribute) else 'element'
    return 'stationxml@%s:%s:%s/%s' % (
        STATIONXML_VERSION,
        type(owner).__name__,
        owner_name,
        '%s:%s' % (kind, _local_name(component.name)),
    )


def _usage_id(path, kind):
    parts = [part for part in path.split('/') if part]
    identifiers = []
    for part in parts:
        if part.startswith('@'):
            identifiers.append('A{}%s' % part[1:])
        else:
            identifiers.append('E{%s}%s' % (STATIONXML_NAMESPACE, part))
    return 'stationxml@%s:%s:%s' % (
        STATIONXML_VERSION,
        kind,
        '/'.join(identifiers),
    )


def _multiply_occurs(values):
    result = 1
    for value in values:
        if value is None:
            return None
        result *= value
    return result


def _particle_conditions(groups, path):
    conditions = []
    effective_min_values = []
    effective_max_values = []
    choice_optional = False
    for index, group in enumerate(groups):
        min_occurs = group.min_occurs
        max_occurs = group.max_occurs
        effective_min_values.append(min_occurs)
        effective_max_values.append(max_occurs)
        if group.model == 'choice' and len(group) > 1:
            choice_optional = True
            conditions.append({
                'kind': 'choice',
                'id': '%s#choice-%s' % (path, index),
                'minOccurs': min_occurs,
                'maxOccurs': max_occurs,
            })
        elif getattr(group, 'ref', None) is not None:
            conditions.append({
                'kind': 'group',
                'name': _local_name(group.name),
                'minOccurs': min_occurs,
                'maxOccurs': max_occurs,
            })
    return conditions, effective_min_values, effective_max_values, choice_optional


def _iter_particles(particle, groups=()):
    if isinstance(particle, XsdElement):
        yield particle, groups
        return
    if isinstance(particle, XsdAnyElement):
        return
    if isinstance(particle, XsdGroup):
        next_groups = groups + (particle,)
        for child in particle:
            yield from _iter_particles(child, next_groups)


def _has_wildcard_element(type_obj):
    content = getattr(type_obj, 'content', None)
    if not isinstance(content, XsdGroup):
        return False

    def contains(group):
        for child in group:
            if isinstance(child, XsdAnyElement):
                return True
            if isinstance(child, XsdGroup) and contains(child):
                return True
        return False

    return contains(content)


def _attribute_entry(attribute, element_path, parent_element_name):
    path = '%s/@%s' % (element_path, attribute.local_name)
    docs = _documentation(
        attribute,
        path,
        parent_element_name,
        parent_name=parent_element_name,
    )
    result = {
        'kind': 'attribute',
        'xmlName': attribute.local_name,
        'path': path,
        'parentPath': element_path,
        'usageId': _usage_id(path, 'attribute'),
        'definitionId': _definition_id(attribute),
        'use': attribute.use or 'optional',
        'required': attribute.use == 'required',
        'default': attribute.default,
        'fixed': attribute.fixed,
        'facets': _facets(attribute.type),
        'documentation': docs,
    }
    result.update(_type_metadata(attribute.type))
    return result


def _element_entry(element, path, parent_path, groups):
    docs = _documentation(
        element,
        path,
        element.local_name,
        parent_name=Path(parent_path).name if parent_path else None,
    )
    conditions, group_mins, group_maxes, choice_optional = (
        _particle_conditions(groups, path)
    )
    local_min = element.min_occurs
    local_max = element.max_occurs
    effective_min = _multiply_occurs([local_min] + group_mins)
    if choice_optional:
        effective_min = 0
    effective_max = _multiply_occurs([local_max] + group_maxes)

    result = {
        'kind': 'element',
        'xmlName': element.local_name,
        'path': path,
        'parentPath': parent_path,
        'usageId': _usage_id(path, 'element'),
        'definitionId': _definition_id(element),
        'localOccurs': {'min': local_min, 'max': local_max},
        'effectiveOccurs': {'min': effective_min, 'max': effective_max},
        'required': effective_min > 0,
        'default': element.default,
        'fixed': element.fixed,
        'facets': _facets(element.type),
        'conditions': conditions,
        'documentation': docs,
        'children': [],
        'attributes': [],
        'wildcards': {
            'elements': _has_wildcard_element(element.type),
            'attributes': any(
                isinstance(attribute, XsdAnyAttribute)
                for attribute in element.attributes.values()
            ),
        },
    }
    result.update(_type_metadata(element.type))
    return result


def _type_entry(type_obj):
    name = _type_name(type_obj)
    synthetic_path = '/types/%s' % name
    docs = _documentation(type_obj, synthetic_path, name)
    result = {
        'kind': 'type',
        'xmlName': name,
        'path': synthetic_path,
        'usageId': 'stationxml@%s:type:%s' % (STATIONXML_VERSION, name),
        'facets': _facets(type_obj),
        'documentation': docs,
    }
    result.update(_type_metadata(type_obj))
    return result


def _tree_from_nodes(nodes, root_path):
    def build(path):
        entry = nodes[path]
        return {
            'text': entry['xmlName'],
            'xmlName': entry['xmlName'],
            'path': path,
            'kind': entry['kind'],
            'children': [build(child) for child in entry['children']],
            'attributes': [
                {
                    'text': '@%s' % nodes[attr]['xmlName'],
                    'xmlName': nodes[attr]['xmlName'],
                    'path': attr,
                    'kind': 'attribute',
                    'leaf': True,
                }
                for attr in entry['attributes']
            ],
            'leaf': not entry['children'] and not entry['attributes'],
        }

    return build(root_path)


def editor_contexts():
    root = '/FDSNStationXML'
    network = root + '/Network'
    station = network + '/Station'
    channel = station + '/Channel'
    common = {
        'code': '@code',
        'alternate_code': '@alternateCode',
        'historical_code': '@historicalCode',
        'source_id': '@sourceID',
        'start_date': '@startDate',
        'end_date': '@endDate',
        'restricted_status': '@restrictedStatus',
        'description': 'Description',
        'identifiers': 'Identifier',
        'comments': 'Comment',
        'data_availability': 'DataAvailability',
    }

    def expand(base, mapping):
        return {
            key: (
                None
                if suffix is None
                else base + ('/' if not suffix.startswith('@') else '/@') +
                (suffix[1:] if suffix.startswith('@') else suffix)
            )
            for key, suffix in mapping.items()
        }

    contexts = {
        'root': {
            'name': None,
            'source': root + '/Source',
            'sender': root + '/Sender',
            'module': root + '/Module',
            'uri': root + '/ModuleURI',
            'created': root + '/Created',
            'schema_version': root + '/@schemaVersion',
        },
        'network': expand(network, dict(common, **{
            'operators': 'Operator',
            'total_number_of_stations': 'TotalNumberStations',
            'selected_number_of_stations': 'SelectedNumberStations',
        })),
        'station': expand(station, dict(common, **{
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'elevation': 'Elevation',
            'site': 'Site',
            'water_level': 'WaterLevel',
            'vault': 'Vault',
            'geology': 'Geology',
            'equipment': 'Equipment',
            'equipments': 'Equipment',
            'operators': 'Operator',
            'external_references': 'ExternalReference',
            'creation_date': 'CreationDate',
            'termination_date': 'TerminationDate',
            'total_number_of_channels': 'TotalNumberChannels',
            'selected_number_of_channels': 'SelectedNumberChannels',
        })),
        'channel': expand(channel, dict(common, **{
            'location_code': '@locationCode',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'elevation': 'Elevation',
            'depth': 'Depth',
            'azimuth': 'Azimuth',
            'dip': 'Dip',
            'water_level': 'WaterLevel',
            'types': 'Type',
            'external_references': 'ExternalReference',
            'sample_rate': 'SampleRate',
            'sample_rate_ratio_number_samples': 'SampleRateRatio/NumberSamples',
            'sample_rate_ratio_number_seconds': 'SampleRateRatio/NumberSeconds',
            'clock_drift_in_seconds_per_sample': 'ClockDrift',
            'calibration_units': 'CalibrationUnits/Name',
            'calibration_units_description': 'CalibrationUnits/Description',
            'sensor': 'Sensor',
            'pre_amplifier': 'PreAmplifier',
            'data_logger': 'DataLogger',
            'equipment': 'Equipment',
            'equipments': 'Equipment',
            'response': 'Response',
        })),
        'nested': {
            'site.name': 'Name',
            'site.description': 'Description',
            'site.town': 'Town',
            'site.county': 'County',
            'site.region': 'Region',
            'site.country': 'Country',
            'comment.value': 'Value',
            'comment.begin_effective_time': 'BeginEffectiveTime',
            'comment.end_effective_time': 'EndEffectiveTime',
            'comment.author': 'Author',
            'comment.id': '@id',
            'comment.subject': '@subject',
            'operator.agency': 'Agency',
            'operator.contact': 'Contact',
            'operator.website': 'WebSite',
            'person.name': 'Name',
            'person.agency': 'Agency',
            'person.email': 'Email',
            'person.phone': 'Phone',
            'equipment.type': 'Type',
            'equipment.description': 'Description',
            'equipment.manufacturer': 'Manufacturer',
            'equipment.vendor': 'Vendor',
            'equipment.model': 'Model',
            'equipment.serial_number': 'SerialNumber',
            'equipment.installation_date': 'InstallationDate',
            'equipment.removal_date': 'RemovalDate',
            'equipment.calibration_date': 'CalibrationDate',
            'equipment.resource_id': '@resourceId',
            'external_reference.uri': 'URI',
            'external_reference.description': 'Description',
            'identifier.value': '',
            'identifier.type': '@type',
        },
    }
    return contexts


class StationXmlCatalogGenerator:
    def __init__(self, schema_path, manifest_path=None):
        self.schema_path = Path(schema_path)
        self.manifest_path = Path(manifest_path) if manifest_path else None
        self.schema_bytes = self.schema_path.read_bytes()
        self.schema_sha256 = sha256(self.schema_bytes).hexdigest()
        if self.schema_sha256 != EXPECTED_SCHEMA_SHA256:
            raise ValueError(
                'Unexpected StationXML XSD checksum: %s' % self.schema_sha256
            )
        self.schema = xmlschema.XMLSchema(str(self.schema_path))
        self.nodes = OrderedDict()

    def _walk(self, element, parent_path='', groups=()):
        path = '%s/%s' % (parent_path, element.local_name)
        entry = _element_entry(element, path, parent_path or None, groups)
        self.nodes[path] = entry

        for attribute in element.attributes.values():
            if isinstance(attribute, XsdAnyAttribute):
                continue
            attribute_entry = _attribute_entry(
                attribute, path, element.local_name
            )
            self.nodes[attribute_entry['path']] = attribute_entry
            entry['attributes'].append(attribute_entry['path'])

        content = getattr(element.type, 'content', None)
        if isinstance(content, XsdGroup):
            for child, child_groups in _iter_particles(content):
                child_path = '%s/%s' % (path, child.local_name)
                entry['children'].append(child_path)
                self._walk(child, path, child_groups)

    def generate(self):
        root = self.schema.elements['FDSNStationXML']
        self._walk(root)
        nodes = OrderedDict(sorted(self.nodes.items()))
        types = OrderedDict(
            (name, _type_entry(type_obj))
            for name, type_obj in sorted(self.schema.types.items())
            if name
        )
        root_path = '/FDSNStationXML'
        element_count = sum(
            entry['kind'] == 'element' for entry in nodes.values()
        )
        attribute_count = sum(
            entry['kind'] == 'attribute' for entry in nodes.values()
        )
        metadata = {
            'catalogFormatVersion': CATALOG_FORMAT_VERSION,
            'schemaVersion': STATIONXML_VERSION,
            'namespace': STATIONXML_NAMESPACE,
            'schemaSha256': self.schema_sha256,
            'elementPathCount': element_count,
            'attributeBindingCount': attribute_count,
            'entryCount': element_count + attribute_count,
        }
        if self.manifest_path and self.manifest_path.is_file():
            metadata['source'] = json.loads(
                self.manifest_path.read_text(encoding='utf-8')
            )
        return {
            'metadata': metadata,
            'rootPath': root_path,
            'tree': _tree_from_nodes(nodes, root_path),
            'nodes': nodes,
            'types': types,
            'editorContexts': editor_contexts(),
        }


def deterministic_json(data):
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + '\n'


def response_catalog(catalog):
    response_path = (
        '/FDSNStationXML/Network/Station/Channel/Response'
    )
    nodes = catalog['nodes']
    subset = OrderedDict(
        (path, deepcopy(entry))
        for path, entry in nodes.items()
        if path == response_path
        or path.startswith(response_path + '/')
        or path.startswith(response_path + '/@')
    )
    return {
        'metadata': dict(catalog['metadata'], subtree='Response'),
        'rootPath': response_path,
        'tree': _tree_from_nodes(subset, response_path),
        'nodes': subset,
    }


def validate_catalog(catalog):
    metadata = catalog['metadata']
    expected = {
        'elementPathCount': 276,
        'attributeBindingCount': 206,
        'entryCount': 482,
    }
    errors = []
    for key, value in expected.items():
        if metadata.get(key) != value:
            errors.append('%s=%r, expected %r' % (
                key, metadata.get(key), value
            ))

    usage_ids = [
        entry['usageId'] for entry in catalog['nodes'].values()
    ]
    if len(usage_ids) != len(set(usage_ids)):
        errors.append('usageId values are not unique')

    for level, mappings in catalog['editorContexts'].items():
        if level == 'nested':
            continue
        for key, path in mappings.items():
            if path is not None and path not in catalog['nodes']:
                errors.append('Unknown editor context %s.%s -> %s' % (
                    level, key, path
                ))
    if errors:
        raise ValueError('; '.join(errors))
    return True
