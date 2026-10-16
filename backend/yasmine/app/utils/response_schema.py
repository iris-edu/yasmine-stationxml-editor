# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# Compact StationXML 1.2 Response descriptor and validator.
#
# The descriptor below is a manual transcription of the response-related
# particles and simple types in the FDSN StationXML 1.2 XSD.
#
# ****************************************************************************/

import hashlib
import json
import re
from functools import lru_cache

from lxml import etree

from yasmine.app.utils.response_tree import (
    ResponseNode,
    STATIONXML_NAMESPACE,
    legacy_tree_to_node,
    node_to_element,
    qname_localname,
    qname_namespace,
)
from yasmine.app.utils.stationxml_validation import stationxml_schema


UNBOUNDED = 'unbounded'


def _element(name, type_name, minimum=1, maximum=1):
    return {'element': name, 'type': type_name, 'min': minimum, 'max': maximum}


def _sequence(*particles, minimum=1, maximum=1):
    return {'sequence': list(particles), 'min': minimum, 'max': maximum}


def _choice(*particles, minimum=1, maximum=1):
    return {'choice': list(particles), 'min': minimum, 'max': maximum}


def _any_foreign(minimum=0, maximum=UNBOUNDED):
    return {'any': '##other', 'min': minimum, 'max': maximum, 'readOnly': True}


def _attribute(type_name='String', required=False, fixed=None):
    result = {'type': type_name, 'required': required}
    if fixed is not None:
        result['fixed'] = fixed
    return result


UNCERTAINTY_ATTRIBUTES = {
    'plusError': _attribute('Double'),
    'minusError': _attribute('Double'),
    'measurementMethod': _attribute('String'),
}

FILTER_ATTRIBUTES = {
    'resourceId': _attribute(),
    'name': _attribute(),
}


def _child(name, type_name, order, minimum=0, maximum=1, choice=None, conflicts=None, required_unless=None):
    result = {
        'name': name,
        'type': type_name,
        'order': order,
        'min': minimum,
        'max': maximum,
    }
    if choice:
        result['choice'] = choice
    if conflicts:
        result['conflicts'] = conflicts
    if required_unless:
        result['requiredUnless'] = required_unless
    return result


def _base_filter_particles():
    return (
        _element('Description', 'String', 0),
        _element('InputUnits', 'Units'),
        _element('OutputUnits', 'Units'),
        _any_foreign(),
    )


def _base_filter_children():
    return [
        _child('Description', 'String', 0),
        _child('InputUnits', 'Units', 1, minimum=1),
        _child('OutputUnits', 'Units', 2, minimum=1),
    ]


_STAGE_LINEAR_NAMES = ['PolesZeros', 'Coefficients', 'ResponseList', 'FIR', 'Decimation', 'StageGain']
_STAGE_FILTER_NAMES = ['PolesZeros', 'Coefficients', 'ResponseList', 'FIR']


RESPONSE_DESCRIPTOR = {
    'id': 'fdsn-stationxml-1.2-response',
    'schemaVersion': '1.2',
    'schemaSha256': '5d5ce5e6fd26510f87a15bce194894bfaacd3e38a8d04ee26123e8a07da56096',
    'namespace': STATIONXML_NAMESPACE,
    'root': {'name': 'Response', 'type': 'Response'},
    'types': {
        'String': {'kind': 'simple', 'xsdType': 'xs:string', 'valueType': 'string', 'attributes': {}},
        'Double': {'kind': 'simple', 'xsdType': 'xs:double', 'valueType': 'number', 'attributes': {}},
        'Integer': {'kind': 'simple', 'xsdType': 'xs:integer', 'valueType': 'integer', 'attributes': {}},
        'Counter': {
            'kind': 'simple',
            'xsdType': 'fsx:CounterType',
            'valueType': 'integer',
            'minimum': 0,
            'attributes': {},
        },
        'PzTransferFunction': {
            'kind': 'simple',
            'xsdType': 'xs:string',
            'valueType': 'enum',
            'enum': ['LAPLACE (RADIANS/SECOND)', 'LAPLACE (HERTZ)', 'DIGITAL (Z-TRANSFORM)'],
            'attributes': {},
        },
        'CfTransferFunction': {
            'kind': 'simple',
            'xsdType': 'xs:string',
            'valueType': 'enum',
            'enum': ['ANALOG (RADIANS/SECOND)', 'ANALOG (HERTZ)', 'DIGITAL'],
            'attributes': {},
        },
        'Symmetry': {
            'kind': 'simple',
            'xsdType': 'xs:NMTOKEN',
            'valueType': 'enum',
            'enum': ['NONE', 'EVEN', 'ODD'],
            'attributes': {},
        },
        'Approximation': {
            'kind': 'simple',
            'xsdType': 'xs:string',
            'valueType': 'enum',
            'enum': ['MACLAURIN'],
            'attributes': {},
        },
        'FloatNoUnit': {
            'kind': 'simple',
            'xsdType': 'fsx:FloatNoUnitType',
            'valueType': 'number',
            'attributes': UNCERTAINTY_ATTRIBUTES,
        },
        'Float': {
            'kind': 'simple',
            'xsdType': 'fsx:FloatType',
            'valueType': 'number',
            'attributes': dict({'unit': _attribute()}, **UNCERTAINTY_ATTRIBUTES),
        },
        'Frequency': {
            'kind': 'simple',
            'xsdType': 'fsx:FrequencyType',
            'valueType': 'number',
            'attributes': dict({'unit': _attribute(fixed='HERTZ')}, **UNCERTAINTY_ATTRIBUTES),
        },
        'Angle': {
            'kind': 'simple',
            'xsdType': 'fsx:AngleType',
            'valueType': 'number',
            'minimum': -360,
            'maximum': 360,
            'attributes': dict({'unit': _attribute(fixed='DEGREES')}, **UNCERTAINTY_ATTRIBUTES),
        },
        'IndexedFloat': {
            'kind': 'simple',
            'xsdType': 'fsx:FloatNoUnitType',
            'valueType': 'number',
            'attributes': dict({'number': _attribute('Counter')}, **UNCERTAINTY_ATTRIBUTES),
        },
        'FIRCoefficient': {
            'kind': 'simple',
            'xsdType': 'xs:double',
            'valueType': 'number',
            'attributes': {'i': _attribute('Integer')},
        },
        'Response': {
            'kind': 'complex',
            'xsdType': 'fsx:ResponseType',
            'attributes': {'resourceId': _attribute()},
            'allowForeignAttributes': True,
            'content': _sequence(
                _choice(
                    _element('InstrumentSensitivity', 'Sensitivity'),
                    _element('InstrumentPolynomial', 'Polynomial'),
                    minimum=0,
                ),
                _element('Stage', 'Stage', 0, UNBOUNDED),
                _any_foreign(),
            ),
            'children': [
                _child('InstrumentSensitivity', 'Sensitivity', 0, choice='instrument'),
                _child('InstrumentPolynomial', 'Polynomial', 0, choice='instrument'),
                _child('Stage', 'Stage', 1, maximum=UNBOUNDED),
            ],
            'foreignChildOrder': 2,
            'choices': {'instrument': {'min': 0, 'max': 1}},
        },
        'Sensitivity': {
            'kind': 'complex',
            'xsdType': 'fsx:SensitivityType',
            'attributes': {},
            'content': _sequence(
                _element('Value', 'Double'),
                _element('Frequency', 'Double'),
                _element('InputUnits', 'Units'),
                _element('OutputUnits', 'Units'),
                _sequence(
                    _element('FrequencyStart', 'Double'),
                    _element('FrequencyEnd', 'Double'),
                    _element('FrequencyDBVariation', 'Double'),
                    minimum=0,
                ),
            ),
            'children': [
                _child('Value', 'Double', 0, minimum=1),
                _child('Frequency', 'Double', 1, minimum=1),
                _child('InputUnits', 'Units', 2, minimum=1),
                _child('OutputUnits', 'Units', 3, minimum=1),
                _child('FrequencyStart', 'Double', 4, choice='frequencyRange'),
                _child('FrequencyEnd', 'Double', 5, choice='frequencyRange'),
                _child('FrequencyDBVariation', 'Double', 6, choice='frequencyRange'),
            ],
            'choices': {'frequencyRange': {'allOrNone': True}},
        },
        'Stage': {
            'kind': 'complex',
            'xsdType': 'fsx:ResponseStageType',
            'attributes': {
                'number': _attribute('Counter', required=True),
                'resourceId': _attribute(),
            },
            'allowForeignAttributes': True,
            'content': _sequence(
                _choice(
                    _sequence(
                        _choice(
                            _element('PolesZeros', 'PolesZeros'),
                            _element('Coefficients', 'Coefficients'),
                            _element('ResponseList', 'ResponseList'),
                            _element('FIR', 'FIR'),
                            minimum=0,
                        ),
                        _element('Decimation', 'Decimation', 0),
                        _element('StageGain', 'Gain'),
                    ),
                    _element('Polynomial', 'Polynomial'),
                ),
                _any_foreign(),
            ),
            'children': [
                _child(
                    'PolesZeros', 'PolesZeros', 0, choice='filter', conflicts=['Polynomial']
                ),
                _child(
                    'Coefficients', 'Coefficients', 0, choice='filter', conflicts=['Polynomial']
                ),
                _child(
                    'ResponseList', 'ResponseList', 0, choice='filter', conflicts=['Polynomial']
                ),
                _child('FIR', 'FIR', 0, choice='filter', conflicts=['Polynomial']),
                _child('Decimation', 'Decimation', 1, conflicts=['Polynomial']),
                _child(
                    'StageGain',
                    'Gain',
                    2,
                    conflicts=['Polynomial'],
                    required_unless=['Polynomial'],
                ),
                _child('Polynomial', 'Polynomial', 0, conflicts=_STAGE_LINEAR_NAMES),
            ],
            'foreignChildOrder': 3,
            'choices': {'filter': {'min': 0, 'max': 1}},
        },
        'Units': {
            'kind': 'complex',
            'xsdType': 'fsx:UnitsType',
            'attributes': {},
            'content': _sequence(
                _element('Name', 'String'),
                _element('Description', 'String', 0),
            ),
            'children': [
                _child('Name', 'String', 0, minimum=1),
                _child('Description', 'String', 1),
            ],
        },
        'Gain': {
            'kind': 'complex',
            'xsdType': 'fsx:GainType',
            'attributes': {},
            'content': _sequence(
                _element('Value', 'Double'),
                _element('Frequency', 'Double'),
            ),
            'children': [
                _child('Value', 'Double', 0, minimum=1),
                _child('Frequency', 'Double', 1, minimum=1),
            ],
        },
        'PolesZeros': {
            'kind': 'complex',
            'xsdType': 'fsx:PolesZerosType',
            'attributes': FILTER_ATTRIBUTES,
            'allowForeignAttributes': True,
            'content': _sequence(
                *_base_filter_particles(),
                _element('PzTransferFunctionType', 'PzTransferFunction'),
                _element('NormalizationFactor', 'Double'),
                _element('NormalizationFrequency', 'Frequency'),
                _element('Zero', 'PoleZero', 0, UNBOUNDED),
                _element('Pole', 'PoleZero', 0, UNBOUNDED),
            ),
            'children': _base_filter_children() + [
                _child('PzTransferFunctionType', 'PzTransferFunction', 4, minimum=1),
                _child('NormalizationFactor', 'Double', 5, minimum=1),
                _child('NormalizationFrequency', 'Frequency', 6, minimum=1),
                _child('Zero', 'PoleZero', 7, maximum=UNBOUNDED),
                _child('Pole', 'PoleZero', 8, maximum=UNBOUNDED),
            ],
            'foreignChildOrder': 3,
        },
        'PoleZero': {
            'kind': 'complex',
            'xsdType': 'fsx:PoleZeroType',
            'attributes': {'number': _attribute('Integer')},
            'content': _sequence(
                _element('Real', 'FloatNoUnit'),
                _element('Imaginary', 'FloatNoUnit'),
            ),
            'children': [
                _child('Real', 'FloatNoUnit', 0, minimum=1),
                _child('Imaginary', 'FloatNoUnit', 1, minimum=1),
            ],
        },
        'Coefficients': {
            'kind': 'complex',
            'xsdType': 'fsx:CoefficientsType',
            'attributes': FILTER_ATTRIBUTES,
            'allowForeignAttributes': True,
            'content': _sequence(
                *_base_filter_particles(),
                _element('CfTransferFunctionType', 'CfTransferFunction'),
                _element('Numerator', 'IndexedFloat', 0, UNBOUNDED),
                _element('Denominator', 'IndexedFloat', 0, UNBOUNDED),
            ),
            'children': _base_filter_children() + [
                _child('CfTransferFunctionType', 'CfTransferFunction', 4, minimum=1),
                _child('Numerator', 'IndexedFloat', 5, maximum=UNBOUNDED),
                _child('Denominator', 'IndexedFloat', 6, maximum=UNBOUNDED),
            ],
            'foreignChildOrder': 3,
        },
        'FIR': {
            'kind': 'complex',
            'xsdType': 'fsx:FIRType',
            'attributes': FILTER_ATTRIBUTES,
            'allowForeignAttributes': True,
            'content': _sequence(
                *_base_filter_particles(),
                _element('Symmetry', 'Symmetry'),
                _element('NumeratorCoefficient', 'FIRCoefficient', 0, UNBOUNDED),
            ),
            'children': _base_filter_children() + [
                _child('Symmetry', 'Symmetry', 4, minimum=1),
                _child('NumeratorCoefficient', 'FIRCoefficient', 5, maximum=UNBOUNDED),
            ],
            'foreignChildOrder': 3,
        },
        'ResponseList': {
            'kind': 'complex',
            'xsdType': 'fsx:ResponseListType',
            'attributes': FILTER_ATTRIBUTES,
            'allowForeignAttributes': True,
            'content': _sequence(
                *_base_filter_particles(),
                _element('ResponseListElement', 'ResponseListElement', 0, UNBOUNDED),
            ),
            'children': _base_filter_children() + [
                _child('ResponseListElement', 'ResponseListElement', 4, maximum=UNBOUNDED),
            ],
            'foreignChildOrder': 3,
        },
        'ResponseListElement': {
            'kind': 'complex',
            'xsdType': 'fsx:ResponseListElementType',
            'attributes': {},
            'content': _sequence(
                _element('Frequency', 'Frequency'),
                _element('Amplitude', 'Float'),
                _element('Phase', 'Angle'),
            ),
            'children': [
                _child('Frequency', 'Frequency', 0, minimum=1),
                _child('Amplitude', 'Float', 1, minimum=1),
                _child('Phase', 'Angle', 2, minimum=1),
            ],
        },
        'Polynomial': {
            'kind': 'complex',
            'xsdType': 'fsx:PolynomialType',
            'attributes': FILTER_ATTRIBUTES,
            'allowForeignAttributes': True,
            'content': _sequence(
                *_base_filter_particles(),
                _element('ApproximationType', 'Approximation'),
                _element('FrequencyLowerBound', 'Frequency'),
                _element('FrequencyUpperBound', 'Frequency'),
                _element('ApproximationLowerBound', 'Double'),
                _element('ApproximationUpperBound', 'Double'),
                _element('MaximumError', 'Double'),
                _element('Coefficient', 'IndexedFloat', 1, UNBOUNDED),
            ),
            'children': _base_filter_children() + [
                _child('ApproximationType', 'Approximation', 4, minimum=1),
                _child('FrequencyLowerBound', 'Frequency', 5, minimum=1),
                _child('FrequencyUpperBound', 'Frequency', 6, minimum=1),
                _child('ApproximationLowerBound', 'Double', 7, minimum=1),
                _child('ApproximationUpperBound', 'Double', 8, minimum=1),
                _child('MaximumError', 'Double', 9, minimum=1),
                _child('Coefficient', 'IndexedFloat', 10, minimum=1, maximum=UNBOUNDED),
            ],
            'foreignChildOrder': 3,
        },
        'Decimation': {
            'kind': 'complex',
            'xsdType': 'fsx:DecimationType',
            'attributes': {},
            'content': _sequence(
                _element('InputSampleRate', 'Frequency'),
                _element('Factor', 'Integer'),
                _element('Offset', 'Integer'),
                _element('Delay', 'Float'),
                _element('Correction', 'Float'),
            ),
            'children': [
                _child('InputSampleRate', 'Frequency', 0, minimum=1),
                _child('Factor', 'Integer', 1, minimum=1),
                _child('Offset', 'Integer', 2, minimum=1),
                _child('Delay', 'Float', 3, minimum=1),
                _child('Correction', 'Float', 4, minimum=1),
            ],
        },
    },
}


@lru_cache(maxsize=1)
def get_response_descriptor():
    """Return the process-wide StationXML 1.2 response descriptor."""
    return RESPONSE_DESCRIPTOR


@lru_cache(maxsize=1)
def response_descriptor_json():
    """Return deterministic compact JSON used for HTTP caching and ETags."""
    return json.dumps(get_response_descriptor(), sort_keys=True, separators=(',', ':'))


@lru_cache(maxsize=1)
def response_descriptor_etag():
    return hashlib.sha256(response_descriptor_json().encode('utf-8')).hexdigest()


_DOUBLE_RE = re.compile(
    r'^(?:[+-]?(?:(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)|-?INF|NaN)$'
)
_INTEGER_RE = re.compile(r'^[+-]?\d+$')


def _issue(severity, code, path, message):
    return {
        'severity': severity,
        'code': code,
        'path': path,
        'message': message,
    }


def _xsd_response_issues(root):
    """Validate the response in a minimal valid StationXML 1.2 document."""
    document = etree.fromstring(
        (
            '<FDSNStationXML xmlns="%s" schemaVersion="1.2">'
            '<Source>Yasmine</Source>'
            '<Created>2020-01-01T00:00:00Z</Created>'
            '<Network code="XX"><Station code="YY">'
            '<Latitude>0</Latitude><Longitude>0</Longitude><Elevation>0</Elevation>'
            '<Site><Name>Validation fixture</Name></Site>'
            '<Channel code="BHZ" locationCode="">'
            '<Latitude>0</Latitude><Longitude>0</Longitude><Elevation>0</Elevation>'
            '<Depth>0</Depth>'
            '</Channel></Station></Network></FDSNStationXML>'
        ) % STATIONXML_NAMESPACE
    )
    channel = document.xpath(
        '//*[local-name()="Channel" and namespace-uri()=$namespace]',
        namespace=STATIONXML_NAMESPACE,
    )[0]
    channel.append(node_to_element(root))
    schema = stationxml_schema()
    if schema.validate(document):
        return []
    return [
        _issue(
            'error',
            'xsd.%s' % (entry.type_name or 'validation').lower(),
            entry.path or '/Response',
            entry.message,
        )
        for entry in schema.error_log
    ]


def _coerce_node(payload):
    if isinstance(payload, ResponseNode):
        return payload
    if isinstance(payload, dict) and 'response' in payload and 'Response' not in payload:
        payload = payload['response']
    return legacy_tree_to_node(payload)


def _is_foreign_node(node):
    return qname_namespace(node.qname) not in (None, STATIONXML_NAMESPACE)


def _match_once(particle, nodes, position):
    if 'element' in particle:
        if position >= len(nodes):
            return set()
        node = nodes[position]
        if _is_foreign_node(node):
            return set()
        return {position + 1} if qname_localname(node.qname) == particle['element'] else set()
    if 'any' in particle:
        if position < len(nodes) and _is_foreign_node(nodes[position]):
            return {position + 1}
        return set()
    if 'sequence' in particle:
        positions = {position}
        for child_particle in particle['sequence']:
            next_positions = set()
            for current in positions:
                next_positions.update(_match_particle(child_particle, nodes, current))
            positions = next_positions
            if not positions:
                break
        return positions
    if 'choice' in particle:
        positions = set()
        for child_particle in particle['choice']:
            positions.update(_match_particle(child_particle, nodes, position))
        return positions
    return set()


def _match_particle(particle, nodes, position):
    minimum = particle.get('min', 1)
    maximum = particle.get('max', 1)
    maximum = len(nodes) + 1 if maximum == UNBOUNDED else maximum
    accepted = {position} if minimum == 0 else set()
    frontier = {position}
    for count in range(1, maximum + 1):
        next_frontier = set()
        for current in frontier:
            next_frontier.update(_match_once(particle, nodes, current))
        if not next_frontier:
            break
        if count >= minimum:
            accepted.update(next_frontier)
        if next_frontier == frontier:
            break
        frontier = next_frontier
    return accepted


def _collect_element_refs(particle, result=None):
    if result is None:
        result = {}
    if 'element' in particle:
        result[particle['element']] = particle['type']
    for key in ('sequence', 'choice'):
        for child in particle.get(key, []):
            _collect_element_refs(child, result)
    return result


def _validate_scalar(value, type_name, path, issues):
    type_definition = RESPONSE_DESCRIPTOR['types'][type_name]
    lexical = '' if value is None else str(value).strip()
    value_type = type_definition.get('valueType')
    numeric_value = None

    if value_type == 'number':
        if not _DOUBLE_RE.match(lexical):
            issues.append(_issue('error', 'xsd.type', path, "'%s' is not a valid xs:double value." % lexical))
            return
        if lexical not in ('INF', '-INF', 'NaN'):
            numeric_value = float(lexical)
    elif value_type == 'integer':
        if not _INTEGER_RE.match(lexical):
            issues.append(_issue('error', 'xsd.type', path, "'%s' is not a valid integer value." % lexical))
            return
        numeric_value = int(lexical)
    elif value_type == 'enum' and lexical not in type_definition.get('enum', []):
        issues.append(
            _issue(
                'error',
                'xsd.enumeration',
                path,
                "'%s' is not one of: %s." % (lexical, ', '.join(type_definition.get('enum', []))),
            )
        )
        return

    if numeric_value is not None:
        minimum = type_definition.get('minimum')
        maximum = type_definition.get('maximum')
        if minimum is not None and numeric_value < minimum:
            issues.append(_issue('error', 'xsd.minimum', path, 'Value must be greater than or equal to %s.' % minimum))
        if maximum is not None and numeric_value > maximum:
            issues.append(_issue('error', 'xsd.maximum', path, 'Value must be less than or equal to %s.' % maximum))


def _validate_attributes(node, type_definition, path, issues):
    definitions = type_definition.get('attributes', {})
    seen = set()
    for qname, value in node.attributes.items():
        namespace = qname_namespace(qname)
        localname = qname_localname(qname)
        attr_path = '%s/@%s' % (path, qname if namespace else localname)
        if namespace not in (None, STATIONXML_NAMESPACE):
            if not type_definition.get('allowForeignAttributes'):
                issues.append(_issue('error', 'xsd.attribute', attr_path, 'Foreign attributes are not allowed here.'))
            continue
        definition = definitions.get(localname)
        if definition is None or namespace == STATIONXML_NAMESPACE:
            issues.append(_issue('error', 'xsd.attribute', attr_path, "Attribute '%s' is not allowed." % localname))
            continue
        seen.add(localname)
        _validate_scalar(value, definition['type'], attr_path, issues)
        if 'fixed' in definition and str(value) != definition['fixed']:
            issues.append(
                _issue(
                    'error',
                    'xsd.fixed',
                    attr_path,
                    "Attribute '%s' must have the fixed value '%s'." % (localname, definition['fixed']),
                )
            )
    for name, definition in definitions.items():
        if definition.get('required') and name not in seen:
            issues.append(_issue('error', 'xsd.required_attribute', '%s/@%s' % (path, name), "Required attribute '%s' is missing." % name))


def _child_paths(nodes, parent_path):
    totals = {}
    for node in nodes:
        localname = qname_localname(node.qname)
        totals[localname] = totals.get(localname, 0) + 1
    counters = {}
    result = []
    for node in nodes:
        localname = qname_localname(node.qname)
        counters[localname] = counters.get(localname, 0) + 1
        suffix = '[%d]' % counters[localname] if totals[localname] > 1 or localname == 'Stage' else ''
        result.append('%s/%s%s' % (parent_path, localname, suffix))
    return result


def _validate_node(node, type_name, path, issues):
    type_definition = RESPONSE_DESCRIPTOR['types'][type_name]
    _validate_attributes(node, type_definition, path, issues)

    if type_definition['kind'] == 'simple':
        if node.children:
            issues.append(_issue('error', 'xsd.simple_content', path, 'Simple-content elements cannot contain child elements.'))
        _validate_scalar(node.text, type_name, path, issues)
        return

    if node.text and node.text.strip():
        issues.append(_issue('error', 'xsd.element_content', path, 'Element-only content cannot contain text.'))

    content = type_definition['content']
    final_positions = _match_particle(content, node.children, 0)
    if len(node.children) not in final_positions:
        issues.append(
            _issue(
                'error',
                'xsd.content',
                path,
                'Children do not match the StationXML 1.2 order, choice, or cardinality for %s.' % qname_localname(node.qname),
            )
        )

    element_refs = _collect_element_refs(content)
    for child, child_path in zip(node.children, _child_paths(node.children, path)):
        if _is_foreign_node(child):
            continue
        child_name = qname_localname(child.qname)
        child_type = element_refs.get(child_name)
        if child_type is None:
            issues.append(_issue('error', 'xsd.element', child_path, "Element '%s' is not allowed." % child_name))
        else:
            _validate_node(child, child_type, child_path, issues)


def _children(node, name=None):
    result = [
        child for child in node.children
        if not _is_foreign_node(child) and (name is None or qname_localname(child.qname) == name)
    ]
    return result


def _first_child(node, name):
    matches = _children(node, name)
    return matches[0] if matches else None


def _node_value(node):
    return node.text.strip() if node is not None and node.text is not None else None


def _unit_name(container, child_name):
    units = _first_child(container, child_name)
    return _node_value(_first_child(units, 'Name')) if units is not None else None


def _stage_filter(stage):
    for name in _STAGE_FILTER_NAMES + ['Polynomial']:
        child = _first_child(stage, name)
        if child is not None:
            return child
    return None


def _operational_warnings(root):
    warnings = []
    stages = _children(root, 'Stage')
    instrument_sensitivity = _first_child(root, 'InstrumentSensitivity')
    instrument_polynomial = _first_child(root, 'InstrumentPolynomial')
    polynomial_stages = [stage for stage in stages if _first_child(stage, 'Polynomial') is not None]

    if stages and polynomial_stages and instrument_polynomial is None:
        warnings.append(
            _issue(
                'warning',
                'operational.instrument_polynomial',
                '/Response',
                'A polynomial stage should be paired with InstrumentPolynomial.',
            )
        )
    if stages and not polynomial_stages and instrument_sensitivity is None:
        warnings.append(
            _issue(
                'warning',
                'operational.instrument_sensitivity',
                '/Response',
                'A non-polynomial response should include InstrumentSensitivity.',
            )
        )

    stage_numbers = []
    stage_units = []
    for index, stage in enumerate(stages, 1):
        stage_path = '/Response/Stage[%d]' % index
        number = stage.attributes.get('number')
        try:
            stage_numbers.append(int(number))
        except (TypeError, ValueError):
            pass

        filter_node = _stage_filter(stage)
        if filter_node is None:
            warnings.append(
                _issue(
                    'warning',
                    'operational.stage_filter',
                    stage_path,
                    'A gain-only stage should still document a filter so its units are explicit.',
                )
            )
            stage_units.append((None, None))
        else:
            stage_units.append((_unit_name(filter_node, 'InputUnits'), _unit_name(filter_node, 'OutputUnits')))

        gain = _first_child(stage, 'StageGain')
        gain_value = _node_value(_first_child(gain, 'Value')) if gain is not None else None
        try:
            if gain_value is not None and float(gain_value) == 0:
                warnings.append(
                    _issue(
                        'warning',
                        'operational.stage_gain',
                        stage_path + '/StageGain/Value',
                        'A zero stage gain makes the response unusable.',
                    )
                )
        except ValueError:
            pass

        decimation = _first_child(stage, 'Decimation')
        if decimation is not None:
            factor_node = _first_child(decimation, 'Factor')
            offset_node = _first_child(decimation, 'Offset')
            try:
                factor = int(_node_value(factor_node))
                offset = int(_node_value(offset_node))
                if factor <= 0:
                    warnings.append(
                        _issue(
                            'warning',
                            'operational.decimation_factor',
                            stage_path + '/Decimation/Factor',
                            'Decimation factor should be greater than zero.',
                        )
                    )
                if offset < 0 or factor <= 0 or offset >= factor:
                    warnings.append(
                        _issue(
                            'warning',
                            'operational.decimation_offset',
                            stage_path + '/Decimation/Offset',
                            'Decimation offset should be non-negative and less than the factor.',
                        )
                    )
            except (TypeError, ValueError):
                pass

    expected_numbers = list(range(1, len(stage_numbers) + 1))
    if stage_numbers and stage_numbers != expected_numbers:
        warnings.append(
            _issue(
                'warning',
                'operational.stage_sequence',
                '/Response/Stage',
                'Stage numbers should start at 1 and increase contiguously.',
            )
        )

    for index in range(len(stage_units) - 1):
        output_units = stage_units[index][1]
        input_units = stage_units[index + 1][0]
        if output_units and input_units and output_units.strip().lower() != input_units.strip().lower():
            warnings.append(
                _issue(
                    'warning',
                    'operational.units',
                    '/Response/Stage[%d]' % (index + 2),
                    "Stage input units '%s' do not match the previous output units '%s'." % (input_units, output_units),
                )
            )

    if instrument_sensitivity is not None and stage_units:
        sensitivity_input = _unit_name(instrument_sensitivity, 'InputUnits')
        sensitivity_output = _unit_name(instrument_sensitivity, 'OutputUnits')
        first_input = stage_units[0][0]
        last_output = stage_units[-1][1]
        if sensitivity_input and first_input and sensitivity_input.strip().lower() != first_input.strip().lower():
            warnings.append(
                _issue(
                    'warning',
                    'operational.units',
                    '/Response/InstrumentSensitivity/InputUnits',
                    'InstrumentSensitivity input units do not match the first stage.',
                )
            )
        if sensitivity_output and last_output and sensitivity_output.strip().lower() != last_output.strip().lower():
            warnings.append(
                _issue(
                    'warning',
                    'operational.units',
                    '/Response/InstrumentSensitivity/OutputUnits',
                    'InstrumentSensitivity output units do not match the last stage.',
                )
            )
    return warnings


def validate_response_tree(payload):
    """Return structured StationXML 1.2 errors and operational warnings."""
    issues = []
    try:
        root = _coerce_node(payload)
    except (TypeError, ValueError) as error:
        return [_issue('error', 'xsd.payload', '/Response', str(error))]

    if qname_localname(root.qname) != 'Response' or qname_namespace(root.qname) not in (None, STATIONXML_NAMESPACE):
        return [_issue('error', 'xsd.root', '/', 'Payload root must be StationXML Response.')]

    _validate_node(root, 'Response', '/Response', issues)
    if not any(issue['severity'] == 'error' for issue in issues):
        try:
            issues.extend(_xsd_response_issues(root))
        except (OSError, ValueError, etree.LxmlError) as error:
            issues.append(_issue(
                'error',
                'xsd.schema_unavailable',
                '/Response',
                str(error),
            ))
    issues.extend(_operational_warnings(root))
    return issues
