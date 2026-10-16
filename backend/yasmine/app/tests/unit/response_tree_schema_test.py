# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
# ****************************************************************************
#
# StationXML 1.2 Response tree codec and descriptor validation tests.
#
# ****************************************************************************/

import unittest

from lxml import etree

from yasmine.app.exceptions.exceptions import ResponseEditException
from yasmine.app.services.attribute_service import AttributeService
from yasmine.app.utils.response_schema import (
    get_response_descriptor,
    response_descriptor_etag,
    validate_response_tree,
)
from yasmine.app.utils.response_tree import (
    STATIONXML_NAMESPACE,
    replace_response_in_station_xml,
    response_tree_to_xml,
    response_xml_to_tree,
    station_xml_response_to_tree,
)


def _leaf(name, value, attributes=None):
    if not attributes:
        return {name: str(value)}
    return {name: {'attributes': attributes, 'children': [str(value)]}}


def _container(name, children=None, attributes=None, namespaces=None):
    value = {}
    if attributes:
        value['attributes'] = attributes
    if namespaces:
        value['namespaces'] = namespaces
    if children:
        value['children'] = children
    return {name: value}


def _units(name):
    return _container(name, [_leaf('Name', 'm/s' if name == 'InputUnits' else 'V')])


def _base_filter(extra):
    return [_units('InputUnits'), _units('OutputUnits')] + extra


def _gain():
    return _container('StageGain', [_leaf('Value', '2'), _leaf('Frequency', '1')])


def _decimation():
    return _container('Decimation', [
        _leaf('InputSampleRate', '100'),
        _leaf('Factor', '2'),
        _leaf('Offset', '0'),
        _leaf('Delay', '0'),
        _leaf('Correction', '0'),
    ])


def _polynomial(name='Polynomial'):
    return _container(name, _base_filter([
        _leaf('ApproximationType', 'MACLAURIN'),
        _leaf('FrequencyLowerBound', '0'),
        _leaf('FrequencyUpperBound', '10'),
        _leaf('ApproximationLowerBound', '-1'),
        _leaf('ApproximationUpperBound', '1'),
        _leaf('MaximumError', '0.01'),
        _leaf('Coefficient', '1', {'number': '0', 'plusError': '0.1', 'minusError': '0.1'}),
    ]), attributes={'resourceId': 'poly:1', 'name': 'Polynomial'})


def _filter_branches():
    return {
        'PolesZeros': _container('PolesZeros', _base_filter([
            _leaf('PzTransferFunctionType', 'LAPLACE (RADIANS/SECOND)'),
            _leaf('NormalizationFactor', '1'),
            _leaf('NormalizationFrequency', '1', {'unit': 'HERTZ'}),
            _container('Zero', [
                _leaf('Real', '0', {'plusError': '0.1', 'minusError': '0.1'}),
                _leaf('Imaginary', '0'),
            ], attributes={'number': '0'}),
            _container('Pole', [_leaf('Real', '-1'), _leaf('Imaginary', '0')], attributes={'number': '0'}),
        ])),
        'Coefficients': _container('Coefficients', _base_filter([
            _leaf('CfTransferFunctionType', 'DIGITAL'),
            _leaf('Numerator', '1', {'number': '0'}),
            _leaf('Denominator', '1', {'number': '0'}),
        ])),
        'FIR': _container('FIR', _base_filter([
            _leaf('Symmetry', 'NONE'),
            _leaf('NumeratorCoefficient', '1', {'i': '0'}),
        ])),
        'ResponseList': _container('ResponseList', _base_filter([
            _container('ResponseListElement', [
                _leaf('Frequency', '1', {'unit': 'HERTZ'}),
                _leaf('Amplitude', '2', {'unit': 'V'}),
                _leaf('Phase', '0', {'unit': 'DEGREES'}),
            ]),
        ])),
    }


def _response(children=None, attributes=None):
    return _container('Response', children or [], attributes=attributes)


def _sensitivity():
    return _container('InstrumentSensitivity', [
        _leaf('Value', '2'),
        _leaf('Frequency', '1'),
        _units('InputUnits'),
        _units('OutputUnits'),
    ])


def _stage(filter_node, number='1', include_decimation=True):
    children = [filter_node]
    if include_decimation:
        children.append(_decimation())
    children.append(_gain())
    return _container('Stage', children, attributes={'number': number, 'resourceId': 'stage:' + number})


def _errors(payload):
    return [issue for issue in validate_response_tree(payload) if issue['severity'] == 'error']


class ResponseDescriptorTest(unittest.TestCase):

    def test_descriptor_covers_response_branches_and_enums(self):
        descriptor = get_response_descriptor()
        self.assertEqual(descriptor['schemaVersion'], '1.2')
        self.assertEqual(
            descriptor['schemaSha256'],
            '5d5ce5e6fd26510f87a15bce194894bfaacd3e38a8d04ee26123e8a07da56096',
        )
        self.assertEqual(descriptor['namespace'], STATIONXML_NAMESPACE)
        for type_name in (
                'Response', 'Sensitivity', 'Stage', 'PolesZeros', 'Coefficients',
                'FIR', 'ResponseList', 'Polynomial', 'Decimation', 'Gain', 'Units'):
            self.assertIn(type_name, descriptor['types'])
        self.assertEqual(
            descriptor['types']['Symmetry']['enum'],
            ['NONE', 'EVEN', 'ODD'],
        )
        self.assertEqual(len(response_descriptor_etag()), 64)

    def test_descriptor_is_cached(self):
        self.assertIs(get_response_descriptor(), get_response_descriptor())


class ResponseSchemaValidationTest(unittest.TestCase):

    def test_empty_response_and_root_resource_id_are_valid(self):
        self.assertEqual(_errors(_response(attributes={'resourceId': 'YASMINE:unknown'})), [])

    def test_instrument_sensitivity_branch_is_valid(self):
        self.assertEqual(_errors(_response([_sensitivity()])), [])

    def test_instrument_polynomial_branch_is_valid(self):
        self.assertEqual(_errors(_response([_polynomial('InstrumentPolynomial')])), [])

    def test_every_linear_stage_filter_branch_is_valid(self):
        for name, filter_node in _filter_branches().items():
            with self.subTest(branch=name):
                payload = _response([_sensitivity(), _stage(filter_node)])
                self.assertEqual(_errors(payload), [])

    def test_polynomial_stage_branch_is_valid(self):
        payload = _response([
            _polynomial('InstrumentPolynomial'),
            _container('Stage', [_polynomial()], attributes={'number': '1'}),
        ])
        self.assertEqual(_errors(payload), [])

    def test_response_choice_is_enforced(self):
        payload = _response([_sensitivity(), _polynomial('InstrumentPolynomial')])
        issues = _errors(payload)
        self.assertTrue(any(issue['code'] == 'xsd.content' for issue in issues))

    def test_stage_filter_choice_and_cardinality_are_enforced(self):
        branches = _filter_branches()
        stage = _container(
            'Stage',
            [branches['PolesZeros'], branches['FIR'], _gain(), _gain()],
            attributes={'number': '1'},
        )
        issues = _errors(_response([stage]))
        self.assertTrue(any(issue['path'] == '/Response/Stage[1]' for issue in issues))

    def test_child_order_is_enforced(self):
        branches = _filter_branches()
        stage = _container('Stage', [_gain(), branches['FIR']], attributes={'number': '1'})
        self.assertTrue(any(issue['code'] == 'xsd.content' for issue in _errors(_response([stage]))))

    def test_required_children_attributes_enums_and_types_are_errors(self):
        stage = _container('Stage', [
            _container('FIR', _base_filter([_leaf('Symmetry', 'SIDEWAYS')])),
            _container('StageGain', [_leaf('Value', 'not-a-number')]),
        ])
        issues = _errors(_response([stage]))
        codes = {issue['code'] for issue in issues}
        self.assertIn('xsd.required_attribute', codes)
        self.assertIn('xsd.enumeration', codes)
        self.assertIn('xsd.type', codes)
        self.assertIn('xsd.content', codes)
        self.assertTrue(all(set(issue) == {'severity', 'code', 'path', 'message'} for issue in issues))

    def test_foreign_elements_and_attributes_are_accepted_at_extension_points(self):
        payload = _container(
            'Response',
            [_container('{urn:vendor}Calibration', [_leaf('{urn:vendor}Value', 'opaque')])],
            attributes={'{urn:vendor}flag': 'yes'},
            namespaces={'v': 'urn:vendor'},
        )
        self.assertEqual(_errors(payload), [])

    def test_operational_rules_are_warnings(self):
        branches = _filter_branches()
        first = _stage(branches['FIR'], number='2')
        first['Stage']['children'][0]['FIR']['children'][1]['OutputUnits']['children'][0] = _leaf('Name', 'count')
        second = _stage(branches['Coefficients'], number='4')
        issues = validate_response_tree(_response([first, second]))
        self.assertFalse(any(issue['severity'] == 'error' for issue in issues))
        warning_codes = {issue['code'] for issue in issues}
        self.assertIn('operational.stage_sequence', warning_codes)
        self.assertIn('operational.units', warning_codes)
        self.assertIn('operational.instrument_sensitivity', warning_codes)

    def test_gain_and_decimation_operational_failures_remain_warnings(self):
        stage = _stage(_filter_branches()['FIR'])
        decimation = stage['Stage']['children'][1]['Decimation']['children']
        decimation[1] = _leaf('Factor', '0')
        decimation[2] = _leaf('Offset', '1')
        stage['Stage']['children'][2]['StageGain']['children'][0] = _leaf('Value', '0')
        issues = validate_response_tree(_response([stage]))
        self.assertFalse(any(issue['severity'] == 'error' for issue in issues))
        warning_codes = {issue['code'] for issue in issues}
        self.assertIn('operational.stage_gain', warning_codes)
        self.assertIn('operational.decimation_factor', warning_codes)
        self.assertIn('operational.decimation_offset', warning_codes)


class ResponseTreeCodecTest(unittest.TestCase):

    def test_root_attributes_empty_response_and_escaping_round_trip(self):
        payload = _response(attributes={'resourceId': 'a&"b<c>'})
        xml = response_tree_to_xml(payload)
        self.assertIn('resourceId="a&amp;&quot;b&lt;c&gt;"', xml)
        self.assertTrue(xml.endswith('/>'))
        self.assertEqual(response_xml_to_tree(xml)['Response']['attributes']['resourceId'], 'a&"b<c>')

    def test_legacy_scalar_and_uncertainty_payload_round_trip(self):
        payload = _response([_sensitivity()])
        xml = response_tree_to_xml(payload)
        restored = response_xml_to_tree(xml)
        self.assertEqual(
            restored['Response']['children'][0]['InstrumentSensitivity']['children'][0]['Value'],
            '2',
        )

    def test_foreign_qnames_and_attributes_are_opaque_and_preserved(self):
        payload = _container(
            'Response',
            [_container(
                '{urn:vendor}Extension',
                [_leaf('{urn:vendor}Raw', 'x<&')],
                attributes={'{urn:vendor}mode': 'raw'},
            )],
            attributes={'resourceId': 'root', '{urn:vendor}flag': 'on'},
            namespaces={'vendor': 'urn:vendor'},
        )
        xml = response_tree_to_xml(payload)
        root = etree.fromstring(xml.encode('utf-8'))
        extension = root[0]
        self.assertEqual(extension.tag, '{urn:vendor}Extension')
        self.assertEqual(extension.get('{urn:vendor}mode'), 'raw')
        restored = response_xml_to_tree(xml)
        self.assertEqual(restored['Response']['attributes']['{urn:vendor}flag'], 'on')
        self.assertEqual(
            restored['Response']['children'][0]['{urn:vendor}Extension']['children'][0]['{urn:vendor}Raw'],
            'x<&',
        )

    def test_prefixed_legacy_namespace_declarations_are_supported(self):
        payload = {
            'Response': {
                'attributes': {'xmlns:v': 'urn:vendor', 'v:flag': 'on'},
                'children': [{'v:Marker': {'attributes': {'v:id': '1'}}}],
            },
        }
        xml = response_tree_to_xml(payload)
        root = etree.fromstring(xml.encode('utf-8'))
        self.assertEqual(root.get('{urn:vendor}flag'), 'on')
        self.assertEqual(root[0].tag, '{urn:vendor}Marker')
        self.assertEqual(_errors(payload), [])

    def test_attributes_only_elements_are_self_closing(self):
        payload = _container(
            'Response',
            [_container('{urn:vendor}Marker', attributes={'id': '1'})],
            namespaces={'v': 'urn:vendor'},
        )
        xml = response_tree_to_xml(payload)
        self.assertRegex(xml, r'<v:Marker id="1"\s*/>')

    def test_response_replacement_is_qname_aware(self):
        station_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<fsx:FDSNStationXML xmlns:fsx="%s" schemaVersion="1.2">'
            '<fsx:Channel code="BHZ" locationCode="">'
            '<fsx:Response resourceId="old"/></fsx:Channel>'
            '</fsx:FDSNStationXML>'
        ) % STATIONXML_NAMESPACE
        replacement = response_tree_to_xml(_response(attributes={'resourceId': 'new'}))
        merged = replace_response_in_station_xml(replacement, station_xml)
        restored = station_xml_response_to_tree(merged)
        self.assertEqual(restored['Response']['attributes']['resourceId'], 'new')
        self.assertNotIn('resourceId="old"', merged)


class ResponseAttributeSaveTest(unittest.TestCase):

    def test_schema_errors_are_blocked_before_inventory_conversion(self):
        service = AttributeService.__new__(AttributeService)
        invalid_response = _response([
            _container('Stage', [], attributes={'number': '1'}),
        ])

        with self.assertRaises(ResponseEditException) as context:
            service._update_modified_response(
                object(),
                {'nodeId': 1, 'response': invalid_response},
            )

        self.assertIn('/Response', str(context.exception))

    def test_display_text_is_not_stored(self):
        from types import SimpleNamespace

        from yasmine.app.enums.xml_node import XmlNodeAttrEnum

        service = AttributeService.__new__(AttributeService)
        original = object()
        obj = SimpleNamespace(
            attr=SimpleNamespace(name=XmlNodeAttrEnum.RESPONSE),
            value_obj=original,
        )
        text = 'Channel Response\n\tOverall Sensitivity: 904530 defined at 10.000 Hz'

        with self.assertRaises(ResponseEditException) as context:
            service._update_attribute_value(obj, text)

        self.assertIs(obj.value_obj, original)
        self.assertIn('was not saved', str(context.exception))


if __name__ == '__main__':
    unittest.main()
