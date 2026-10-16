# 2026-09-29, version 4.4.0-beta: ASGSR, Alexey Emanov
# Post-import 1.x → 1.2 migration notes for operators.

import io
import json

from lxml import etree

from yasmine.app.utils.stationxml_validation import (
    IMPORTABLE_SCHEMA_VERSIONS,
    STATIONXML_NAMESPACE,
    STATIONXML_VERSION,
)


def _qname(elem):
    return etree.QName(elem)


def _is_stationxml(elem, localname):
    if not isinstance(elem.tag, str):
        return False
    qname = _qname(elem)
    return qname.namespace == STATIONXML_NAMESPACE and qname.localname == localname


def build_import_migration_report(xml_data):
    """Scan source StationXML for operator-facing 1.1→1.2 notes.

    Lightweight streaming scan — does not load ObsPy inventories.
    """
    if isinstance(xml_data, str):
        raw = xml_data.encode('utf-8')
    else:
        raw = bytes(xml_data)

    notes = []
    schema_version = None
    channel_type_count = 0
    storage_format_count = 0
    span_only_da_count = 0
    extension_element_count = 0
    extension_attribute_count = 0

    context = etree.iterparse(
        io.BytesIO(raw),
        events=('start', 'end'),
        resolve_entities=False,
        no_network=True,
        huge_tree=True,
    )
    try:
        for event, elem in context:
            if not isinstance(elem.tag, str):
                continue
            qname = _qname(elem)
            if event == 'start' and qname.localname == 'FDSNStationXML':
                schema_version = elem.get('schemaVersion')
            if event != 'end':
                continue
            if qname.namespace and qname.namespace != STATIONXML_NAMESPACE:
                extension_element_count += 1
                elem.clear()
                continue
            for name in elem.attrib:
                aq = etree.QName(name)
                if aq.namespace and aq.namespace != STATIONXML_NAMESPACE:
                    extension_attribute_count += 1
                if aq.localname == 'storageFormat' or name == 'storageFormat':
                    storage_format_count += 1
            if _is_stationxml(elem, 'Type') and elem.getparent() is not None:
                parent = _qname(elem.getparent())
                if parent.localname == 'Channel':
                    channel_type_count += 1
            if _is_stationxml(elem, 'DataAvailability'):
                has_extent = any(_is_stationxml(c, 'Extent') for c in elem)
                has_span = any(_is_stationxml(c, 'Span') for c in elem)
                if has_span and not has_extent:
                    span_only_da_count += 1
            elem.clear()
    except etree.XMLSyntaxError:
        return {
            'schemaVersion': schema_version,
            'exportSchemaVersion': STATIONXML_VERSION,
            'notes': ['Source XML could not be fully scanned for migration notes.'],
            'counts': {},
        }

    if schema_version and schema_version != STATIONXML_VERSION:
        if schema_version in IMPORTABLE_SCHEMA_VERSIONS:
            notes.append(
                'Source schemaVersion was %s; export will write %s.'
                % (schema_version, STATIONXML_VERSION)
            )
        else:
            notes.append('Unexpected schemaVersion %s.' % schema_version)

    if channel_type_count:
        notes.append(
            'Found %s Channel/Type element(s). Type is retained but marked for '
            'removal in StationXML 1.2 help; review before archive deposit.'
            % channel_type_count
        )
    if storage_format_count:
        notes.append(
            'Found %s storageFormat value(s). StorageFormat is not in '
            'StationXML 1.2 and has no editor in Yasmine.'
            % storage_format_count
        )
    if span_only_da_count:
        notes.append(
            'Found %s span-only DataAvailability block(s). Import may add a '
            'temporary Extent for ObsPy; export omits that Extent when spans remain.'
            % span_only_da_count
        )
    if extension_element_count or extension_attribute_count:
        notes.append(
            'Foreign-namespace extensions: %s element(s), %s attribute(s) '
            'stored as opaque sidecars (read-only; deleted with the parent node).'
            % (extension_element_count, extension_attribute_count)
        )

    if not notes:
        notes.append('No 1.1→1.2 migration notes; source already looks like StationXML 1.2.')

    return {
        'schemaVersion': schema_version,
        'exportSchemaVersion': STATIONXML_VERSION,
        'notes': notes,
        'counts': {
            'channelType': channel_type_count,
            'storageFormat': storage_format_count,
            'spanOnlyDataAvailability': span_only_da_count,
            'extensionElements': extension_element_count,
            'extensionAttributes': extension_attribute_count,
        },
    }


def summarize_extension_sidecar(sidecar_text):
    """Return a compact read-only summary of one node's extension_sidecar JSON."""
    if not sidecar_text:
        return {'attributeCount': 0, 'elementCount': 0, 'attributes': [], 'elements': []}
    try:
        payload = json.loads(sidecar_text) if isinstance(sidecar_text, str) else sidecar_text
    except (TypeError, ValueError):
        return {
            'attributeCount': 0,
            'elementCount': 0,
            'attributes': [],
            'elements': [],
            'parseError': True,
        }
    attributes = payload.get('attributes') or []
    elements = payload.get('elements') or []
    attr_names = []
    for item in attributes[:50]:
        attr_names.append(str(item.get('name') or ''))
    element_labels = []
    for item in elements[:50]:
        xml = item.get('xml') or ''
        label = xml.split('>', 1)[0].lstrip('<').split()[0] if xml.startswith('<') else 'element'
        element_labels.append(label)
    return {
        'attributeCount': len(attributes),
        'elementCount': len(elements),
        'attributes': attr_names,
        'elements': element_labels,
    }
