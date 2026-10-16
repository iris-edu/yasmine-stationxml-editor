#!/usr/bin/env python3
# 2026-09-20, version 4.2.0-beta: ASGSR, Alexey Emanov
"""Generate or verify StationXML 1.2 schema artifacts."""

from argparse import ArgumentParser
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from yasmine.app.utils.stationxml_catalog_generator import (  # noqa: E402
    StationXmlCatalogGenerator,
    deterministic_json,
    editor_contexts,
    response_catalog,
    validate_catalog,
)


RESOURCE_DIR = (
    BACKEND_ROOT
    / 'yasmine'
    / 'resources'
    / 'schemas'
    / 'stationxml'
    / '1.2'
)


def _artifacts():
    generator = StationXmlCatalogGenerator(
        RESOURCE_DIR / 'fdsn-station-1.2.xsd',
        RESOURCE_DIR / 'manifest.json',
    )
    catalog = generator.generate()
    validate_catalog(catalog)
    return {
        RESOURCE_DIR / 'catalog.json': deterministic_json(catalog),
        RESOURCE_DIR / 'response-1.2.json': deterministic_json(
            response_catalog(catalog)
        ),
        RESOURCE_DIR / 'editor-contexts.json': deterministic_json(
            editor_contexts()
        ),
    }


def main(argv=None):
    parser = ArgumentParser()
    parser.add_argument(
        '--check',
        action='store_true',
        help='verify committed artifacts without changing them',
    )
    args = parser.parse_args(argv)

    artifacts = _artifacts()
    stale = []
    for path, content in artifacts.items():
        if args.check:
            if not path.is_file() or path.read_text(encoding='utf-8') != content:
                stale.append(str(path.relative_to(REPOSITORY_ROOT)))
        else:
            path.write_text(content, encoding='utf-8')

    if stale:
        parser.error(
            'generated StationXML artifacts are stale: %s'
            % ', '.join(stale)
        )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
