# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree

try:
    from yasmine.app.utils.stationxml_catalog_generator import (
        EXPECTED_SCHEMA_SHA256,
        StationXmlCatalogGenerator,
        deterministic_json,
        response_catalog,
        validate_catalog,
    )
    _HAS_XMLSCHEMA = True
except ImportError:
    _HAS_XMLSCHEMA = False
    EXPECTED_SCHEMA_SHA256 = None
    StationXmlCatalogGenerator = None
    deterministic_json = None
    response_catalog = None
    validate_catalog = None


RESOURCE_DIR = (
    Path(__file__).resolve().parents[3]
    / 'resources'
    / 'schemas'
    / 'stationxml'
    / '1.2'
)
XSD_PATH = RESOURCE_DIR / 'fdsn-station-1.2.xsd'
MANIFEST_PATH = RESOURCE_DIR / 'manifest.json'


@unittest.skipUnless(_HAS_XMLSCHEMA, 'xmlschema is not installed')
class StationXmlHelpGeneratorTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.catalog = StationXmlCatalogGenerator(
            XSD_PATH, MANIFEST_PATH
        ).generate()

    def test_catalog_has_complete_expanded_path_coverage(self):
        metadata = self.catalog['metadata']
        self.assertEqual(metadata['schemaSha256'], EXPECTED_SCHEMA_SHA256)
        self.assertEqual(metadata['elementPathCount'], 276)
        self.assertEqual(metadata['attributeBindingCount'], 206)
        self.assertEqual(metadata['entryCount'], 482)
        self.assertTrue(validate_catalog(self.catalog))

    def test_level_choice_is_resolved_per_inventory_level(self):
        nodes = self.catalog['nodes']
        cases = {
            '/FDSNStationXML/Network/@code': 'Name of Network',
            '/FDSNStationXML/Network/Station/@code': 'Name of Station',
            '/FDSNStationXML/Network/Station/Channel/@code':
                'Name of Channel',
        }
        for path, expected in cases.items():
            self.assertIn(
                expected,
                nodes[path]['documentation']['description'],
            )

    def test_type_facets_and_conditional_occurrence_are_preserved(self):
        nodes = self.catalog['nodes']
        channel_type = nodes[
            '/FDSNStationXML/Network/Station/Channel/Type'
        ]
        self.assertEqual(len(channel_type['facets']['enumeration']), 11)

        stage_gain = nodes[
            '/FDSNStationXML/Network/Station/Channel/Response/Stage/'
            'StageGain'
        ]
        self.assertEqual(stage_gain['localOccurs']['min'], 1)
        self.assertEqual(stage_gain['effectiveOccurs']['min'], 0)
        self.assertEqual(stage_gain['conditions'][0]['kind'], 'choice')

        counter = self.catalog['types']['CounterType']
        self.assertEqual(counter['baseType'], 'integer')
        self.assertEqual(counter['facets']['minInclusive'], '0')

    def test_element_choice_examples_are_contextual(self):
        unit = self.catalog['nodes'][
            '/FDSNStationXML/Network/Station/Channel/WaterLevel/@unit'
        ]
        self.assertIn('m', unit['documentation']['examples'])

    def test_documentation_inventory_matches_pinned_xsd(self):
        namespace = '{http://www.w3.org/2001/XMLSchema}'
        root = ElementTree.parse(XSD_PATH).getroot()
        documentation = root.findall('.//%sdocumentation' % namespace)
        examples = root.findall('.//%sdocumentation/example' % namespace)
        warnings = root.findall('.//%sdocumentation/warning' % namespace)
        level_descriptions = root.findall(
            './/%sdocumentation/levelDesc' % namespace
        )
        self.assertEqual(len(documentation), 290)
        self.assertEqual(len(examples), 71)
        self.assertEqual(len(warnings), 20)
        self.assertEqual(len(level_descriptions), 12)

    def test_generated_files_are_deterministic(self):
        generated = deterministic_json(self.catalog)
        committed = (RESOURCE_DIR / 'catalog.json').read_text(
            encoding='utf-8'
        )
        self.assertEqual(generated, committed)
        self.assertEqual(
            deterministic_json(response_catalog(self.catalog)),
            (RESOURCE_DIR / 'response-1.2.json').read_text(
                encoding='utf-8'
            ),
        )

    def test_all_editor_base_contexts_resolve(self):
        nodes = self.catalog['nodes']
        contexts = self.catalog['editorContexts']
        for level, mappings in contexts.items():
            if level == 'nested':
                continue
            for name, path in mappings.items():
                if path is not None:
                    self.assertIn(path, nodes, '%s.%s' % (level, name))

    def test_usage_ids_are_unique(self):
        usage_ids = [
            entry['usageId']
            for entry in self.catalog['nodes'].values()
        ]
        self.assertEqual(len(usage_ids), len(set(usage_ids)))

    def test_catalog_is_valid_json_without_ascii_escaping(self):
        parsed = json.loads(deterministic_json(self.catalog))
        self.assertEqual(parsed['metadata']['schemaVersion'], '1.2')


if __name__ == '__main__':
    unittest.main()
