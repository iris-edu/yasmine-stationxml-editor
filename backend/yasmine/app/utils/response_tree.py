# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# QName-aware StationXML Response tree codec.
#
# ****************************************************************************/

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from lxml import etree


STATIONXML_NAMESPACE = 'http://www.fdsn.org/xml/station/1'
XML_NAMESPACE = 'http://www.w3.org/XML/1998/namespace'
XMLNS_NAMESPACE = 'http://www.w3.org/2000/xmlns/'

_LEGACY_METADATA_KEYS = {
    'attributes',
    'children',
    'namespaces',
    '$namespaces',
    'text',
    'tail',
    'id',
    'key',
    'leaf',
    'expanded',
    'iconCls',
    'schemaType',
    'foreign',
    'readOnly',
    '_opaqueValue',
}


@dataclass
class ResponseNode:
    """Canonical response node using expanded (Clark notation) QNames."""

    qname: str
    attributes: Dict[str, str] = field(default_factory=OrderedDict)
    children: List['ResponseNode'] = field(default_factory=list)
    text: Optional[str] = None
    tail: Optional[str] = None
    namespaces: Dict[Optional[str], str] = field(default_factory=dict)


def qname_namespace(name):
    """Return the namespace URI from an expanded QName, if present."""
    if isinstance(name, str) and name.startswith('{'):
        return etree.QName(name).namespace
    return None


def qname_localname(name):
    """Return the local part of an expanded or lexical QName."""
    if isinstance(name, str) and name.startswith('{'):
        return etree.QName(name).localname
    if isinstance(name, str) and name.startswith('Q{'):
        return name.split('}', 1)[1]
    if isinstance(name, str) and ':' in name:
        return name.split(':', 1)[1]
    return name


def is_foreign_qname(name):
    """Whether a QName belongs outside the StationXML namespace."""
    namespace = qname_namespace(name)
    return namespace not in (None, STATIONXML_NAMESPACE)


def _xml_parser():
    return etree.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=False)


def _as_text(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


def _normalise_namespace_map(raw):
    result = {}
    if not isinstance(raw, dict):
        return result
    for prefix, uri in raw.items():
        if uri is None:
            continue
        result[None if prefix in (None, '', 'xmlns') else str(prefix)] = str(uri)
    return result


def _split_namespace_attributes(attributes):
    namespaces = {}
    clean_attributes = OrderedDict()
    for name, value in (attributes or {}).items():
        if name == 'xmlns':
            namespaces[None] = str(value)
        elif isinstance(name, str) and name.startswith('xmlns:'):
            namespaces[name.split(':', 1)[1]] = str(value)
        else:
            clean_attributes[name] = value
    return namespaces, clean_attributes


def _expand_qname(name, namespaces, default_namespace=None, is_attribute=False):
    if not isinstance(name, str) or not name:
        raise ValueError('XML node and attribute names must be non-empty strings')
    if name.startswith('{'):
        etree.QName(name)
        return name
    if name.startswith('Q{'):
        expanded = '{%s}%s' % tuple(name[2:].split('}', 1))
        etree.QName(expanded)
        return expanded
    if ':' in name:
        prefix, local = name.split(':', 1)
        if prefix == 'xml':
            return '{%s}%s' % (XML_NAMESPACE, local)
        namespace = namespaces.get(prefix)
        if not namespace:
            raise ValueError("Unknown namespace prefix '%s' in '%s'" % (prefix, name))
        return '{%s}%s' % (namespace, local)
    if is_attribute:
        return name
    namespace = namespaces.get(None, default_namespace)
    return '{%s}%s' % (namespace, name) if namespace else name


def _legacy_element_entry(payload):
    if not isinstance(payload, dict):
        raise ValueError('Response tree nodes must be JSON objects')
    if 'qname' in payload:
        return payload['qname'], payload
    names = [name for name in payload if name not in _LEGACY_METADATA_KEYS]
    if len(names) != 1:
        raise ValueError('Each response tree node must contain exactly one element name')
    name = names[0]
    return name, payload[name]


def legacy_tree_to_node(payload, inherited_namespaces=None, default_namespace=STATIONXML_NAMESPACE):
    """Convert legacy xmljson/ExtJS tree JSON to the canonical node DTO."""
    name, value = _legacy_element_entry(payload)
    value_dict = value if isinstance(value, dict) else {}

    namespace_map = dict(inherited_namespaces or {})
    local_namespaces = _normalise_namespace_map(
        value_dict.get('namespaces', value_dict.get('$namespaces', {}))
    )
    raw_attributes = value_dict.get('attributes', {})
    declared_attributes, raw_attributes = _split_namespace_attributes(raw_attributes)
    local_namespaces.update(declared_attributes)
    namespace_map.update(local_namespaces)

    qname = _expand_qname(name, namespace_map, default_namespace=default_namespace)
    attributes = OrderedDict()
    if raw_attributes:
        if not isinstance(raw_attributes, dict):
            raise ValueError("The 'attributes' member must be an object")
        for attr_name, attr_value in raw_attributes.items():
            expanded = _expand_qname(attr_name, namespace_map, is_attribute=True)
            attributes[expanded] = '' if attr_value is None else _as_text(attr_value)

    node = ResponseNode(qname=qname, attributes=attributes, namespaces=local_namespaces)
    if isinstance(value, dict):
        if 'text' in value:
            node.text = _as_text(value.get('text'))
        if 'tail' in value:
            node.tail = _as_text(value.get('tail'))
        child_items = value.get('children', [])
        if child_items is None:
            child_items = []
        if not isinstance(child_items, list):
            child_items = [child_items]
        previous_child = None
        for item in child_items:
            if isinstance(item, dict):
                child = legacy_tree_to_node(
                    item,
                    inherited_namespaces=namespace_map,
                    default_namespace=qname_namespace(qname) or default_namespace,
                )
                node.children.append(child)
                previous_child = child
            elif item is not None:
                text = _as_text(item)
                if previous_child is None:
                    node.text = (node.text or '') + text
                else:
                    previous_child.tail = (previous_child.tail or '') + text
    elif value is not None:
        node.text = _as_text(value)
    return node


def _node_namespace_map(node, inherited=None, is_root=False):
    namespace_map = dict(node.namespaces)
    in_scope = dict(inherited or {})
    in_scope.update(namespace_map)
    namespace = qname_namespace(node.qname)
    if is_root and namespace == STATIONXML_NAMESPACE and STATIONXML_NAMESPACE not in in_scope.values():
        namespace_map[None] = STATIONXML_NAMESPACE
    return namespace_map or None


def node_to_element(node, inherited_namespaces=None, is_root=True):
    """Build an lxml element from a canonical response node."""
    if not isinstance(node, ResponseNode):
        raise TypeError('node must be a ResponseNode')
    nsmap = _node_namespace_map(node, inherited_namespaces, is_root=is_root)
    element = etree.Element(node.qname, nsmap=nsmap)
    for name, value in node.attributes.items():
        element.set(name, value)
    element.text = node.text
    in_scope = dict(inherited_namespaces or {})
    if nsmap:
        in_scope.update(nsmap)
    for child_node in node.children:
        child = node_to_element(child_node, inherited_namespaces=in_scope, is_root=False)
        child.tail = child_node.tail
        element.append(child)
    return element


def element_to_node(element, parent_namespaces=None):
    """Build a canonical response node from an lxml element."""
    parent_namespaces = parent_namespaces or {}
    element_children = [child for child in element if isinstance(child.tag, str)]
    local_namespaces = {}
    for prefix, uri in (element.nsmap or {}).items():
        if parent_namespaces.get(prefix) != uri:
            local_namespaces[prefix] = uri

    node = ResponseNode(
        qname=str(element.tag),
        attributes=OrderedDict((str(name), value) for name, value in element.attrib.items()),
        text=element.text,
        tail=element.tail,
        namespaces=local_namespaces,
    )
    if element_children and node.text is not None and not node.text.strip():
        node.text = None
    current_namespaces = dict(parent_namespaces)
    current_namespaces.update(element.nsmap or {})
    for child in element_children:
        child_node = element_to_node(child, current_namespaces)
        if qname_namespace(element.tag) == STATIONXML_NAMESPACE and child_node.tail is not None and not child_node.tail.strip():
            child_node.tail = None
        node.children.append(child_node)
    return node


def _legacy_name(qname):
    namespace = qname_namespace(qname)
    if namespace in (None, STATIONXML_NAMESPACE):
        return qname_localname(qname)
    return qname


def node_to_legacy_tree(node):
    """Convert a canonical node to legacy tree JSON without losing QNames."""
    name = _legacy_name(node.qname)
    attributes = OrderedDict((_legacy_name(key), value) for key, value in node.attributes.items())
    namespaces = OrderedDict()
    for prefix, uri in node.namespaces.items():
        if prefix is None and uri == STATIONXML_NAMESPACE:
            continue
        namespaces['' if prefix is None else prefix] = uri

    has_element_children = bool(node.children)
    if not attributes and not namespaces and not has_element_children:
        if node.text is not None:
            return {name: node.text}
        return {name: {}}

    value = OrderedDict()
    if attributes:
        value['attributes'] = attributes
    if namespaces:
        value['namespaces'] = namespaces

    children = []
    if node.text is not None:
        children.append(node.text)
    for child in node.children:
        children.append(node_to_legacy_tree(child))
        if child.tail is not None:
            children.append(child.tail)
    if children:
        value['children'] = children
    return {name: value}


def _apply_station_namespace(node):
    if qname_namespace(node.qname) is None:
        node.qname = '{%s}%s' % (STATIONXML_NAMESPACE, qname_localname(node.qname))
    for child in node.children:
        if qname_namespace(child.qname) in (None, STATIONXML_NAMESPACE):
            _apply_station_namespace(child)


def response_tree_to_element(response_tree):
    """Convert a legacy or canonical response payload into an lxml Response."""
    node = response_tree if isinstance(response_tree, ResponseNode) else legacy_tree_to_node(response_tree)
    if qname_localname(node.qname) != 'Response':
        raise ValueError('Response tree root must be Response')
    namespace = qname_namespace(node.qname)
    if namespace not in (None, STATIONXML_NAMESPACE):
        raise ValueError('Response root must use the StationXML namespace')
    _apply_station_namespace(node)
    return node_to_element(node)


def response_tree_to_xml(response_tree, encoding='unicode'):
    """Serialize response tree JSON with correct XML escaping and namespaces."""
    element = response_tree_to_element(response_tree)
    return etree.tostring(element, encoding=encoding, with_tail=False)


def response_xml_to_tree(response_xml):
    """Parse a Response XML fragment into legacy-compatible tree JSON."""
    if isinstance(response_xml, str):
        response_xml = response_xml.encode('utf-8')
    element = etree.fromstring(response_xml, parser=_xml_parser())
    if qname_localname(element.tag) != 'Response':
        raise ValueError('XML fragment root must be Response')
    return node_to_legacy_tree(element_to_node(element))


def find_response_element(station_root):
    """Find the first Response element by QName/local name."""
    for element in station_root.iter():
        if isinstance(element.tag, str) and qname_localname(element.tag) == 'Response':
            namespace = qname_namespace(element.tag)
            if namespace in (None, STATIONXML_NAMESPACE):
                return element
    return None


def station_xml_response_to_tree(station_xml):
    """Extract Response from StationXML and return legacy-compatible tree JSON."""
    if isinstance(station_xml, str):
        station_xml = station_xml.encode('utf-8')
    root = etree.fromstring(station_xml, parser=_xml_parser())
    response = find_response_element(root)
    if response is None:
        raise ValueError('No Response element in station XML')
    return node_to_legacy_tree(element_to_node(response, response.getparent().nsmap if response.getparent() is not None else {}))


def _first_channel_element(root):
    for element in root.iter():
        if isinstance(element.tag, str) and qname_localname(element.tag) == 'Channel':
            namespace = qname_namespace(element.tag)
            if namespace in (None, STATIONXML_NAMESPACE):
                return element
    return None


def replace_response_in_station_xml(response_xml, station_xml):
    """Replace or append Response using QName-aware lxml operations."""
    had_declaration = isinstance(station_xml, (str, bytes)) and (
        station_xml.lstrip().startswith('<?xml') if isinstance(station_xml, str)
        else station_xml.lstrip().startswith(b'<?xml')
    )
    station_bytes = station_xml.encode('utf-8') if isinstance(station_xml, str) else station_xml
    response_bytes = response_xml.encode('utf-8') if isinstance(response_xml, str) else response_xml
    root = etree.fromstring(station_bytes, parser=_xml_parser())
    response = etree.fromstring(response_bytes, parser=_xml_parser())
    if qname_localname(response.tag) != 'Response':
        raise ValueError('Response XML root must be Response')

    existing = find_response_element(root)
    if existing is not None:
        existing.getparent().replace(existing, response)
    else:
        channel = _first_channel_element(root)
        if channel is None:
            raise ValueError('No Channel element in station XML')
        channel.append(response)

    if had_declaration:
        return etree.tostring(root, encoding='UTF-8', xml_declaration=True).decode('utf-8')
    return etree.tostring(root, encoding='unicode')


def iter_response_nodes(node):
    """Depth-first iteration helper for validators and callers."""
    yield node
    for child in node.children:
        yield from iter_response_nodes(child)
